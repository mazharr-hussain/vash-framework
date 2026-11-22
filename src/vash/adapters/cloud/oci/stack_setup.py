"""`vash onboard oci` through OCI Resource Manager: every question first, then one job that runs in OCI.

1. Questions: name prefix, the VASH compartment, free-tier guardrails, vault and key, database, network
   compartment, VM size (A1 asked size, basic A1, AMD Micro), SSH key, e-mail. Nothing is created while asking.
2. One summary and one yes.
3. The stack (iac/oci/environments/vash-stack) is saved in Resource Manager and an apply job starts. Terraform
   builds in parallel whatever does not depend on something else; the job runs in OCI, so this window can close.
4. `--status` shows the job, its last log lines and, when done, the VM's address and the install's progress;
   `--resume` runs it again (on no A1 capacity: the next availability domain, then the AMD Micro after a yes);
   `--down` removes what the stack made (compartments are kept).
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from vash.core.exceptions import VashError

from .orm import DONE, ResourceManager, package

if TYPE_CHECKING:
    from .onboard import Onboarding

POLL_SECONDS = 30
LOG_LINES = 15


class StackSetup:
    def __init__(self, ob: "Onboarding"):
        self.ob = ob
        self.echo = ob.echo
        self.rm = ResourceManager(ob.oci, ob.options.workdir, ob.echo)

    # ---- state ----------------------------------------------------------
    @property
    def state(self) -> dict[str, Any]:
        return self.ob._state().get("stack", {})

    def save(self, **values: Any) -> None:
        self.ob._save_state(stack={**self.state, **values})

    # ---- questions ------------------------------------------------------
    def compartment(self, tenancy: str, name: str, description: str) -> dict[str, str]:
        from .security import VaultSetup
        found = VaultSetup(self.ob.oci, self.echo, self.ob.confirm, self.ob.ask, None).find_compartment(tenancy, name)
        if found:
            self.echo(f"Compartment '{name}' exists: it is used as it is")
        elif not self.ob.confirm(f"Compartment '{name}' does not exist. Create it (under the root)?"):
            raise VashError(f"No compartment '{name}'", "Run again and answer yes, or name an existing compartment")
        return {"name": name, "id": found, "description": description}

    def network_name(self) -> str:
        from .onboard import COMPARTMENT_RE, DEFAULT_NETWORK
        if self.ob.options.network_compartment:
            return self.ob.options.network_compartment
        if self.ob.confirm(f"Put the new network (VCN, subnet, gateway, route table, security list) in a compartment "
                           f"named '{DEFAULT_NETWORK}' (one place for every application's networks)?"):
            return DEFAULT_NETWORK
        return self.ob.ask_required("Name of the compartment for the network (an existing name, or a new one)",
                                    COMPARTMENT_RE, "letters, digits, '.', '-' and '_', at most 100")

    def guardrails(self, tenancy: str, email: str) -> tuple[list[str], str]:
        if not self.ob.options.guardrails or "guardrails" in self.ob._state():
            return [], ""
        from .guardrails import Guardrails
        statements = Guardrails(self.ob.oci, self.echo, self.ob.confirm, None).statements(tenancy)
        if statements:
            self.echo("Free-tier guardrail: this quota policy lets OCI refuse anything beyond Always Free:")
            for s in statements:
                self.echo(f"  {s}")
        budget = f" and a monthly budget that e-mails {email} at the first spend" if email else ""
        if not self.ob.confirm(f"Apply this quota policy{budget}? Nothing you use now changes; only paid use is "
                               "blocked (a budget only warns, OCI has no hard spending cap)"):
            self.ob._save_state(guardrails="declined")
            return [], ""
        return statements, email

    def interview(self, tenancy: str) -> tuple[dict[str, Any], list[str]]:
        ob, o = self.ob, self.ob.options
        ob.ensure_prefix({"name_prefix": self.state.get("values", {}).get("name_prefix", "")})
        prefix = ob.prefix
        compartments = {"app": self.compartment(tenancy, ob.compartment_name(), "VASH runner and database")}
        email = ob.notify_address({})
        quota, budget_email = self.guardrails(tenancy, email)
        from .security import VaultSetup
        vault = VaultSetup(ob.oci, self.echo, ob.confirm, ob.ask, None).plan(tenancy, f"{prefix}-secrets-key")
        compartments["security"] = {"name": vault["security_name"], "id": vault["security_id"],
                                    "description": "Vaults and keys of every application (VASH)"}
        create_database = bool(o.database) and ob.confirm(
            f"Create the Always Free Autonomous Database '{prefix}-db' (1 OCPU, 20 GB, $0)? Its admin password is "
            f"made in OCI and kept only in the vault secret '{prefix}-db-admin-password'")
        values: dict[str, Any] = {
            "name_prefix": prefix, "compartments": compartments, "vault_id": vault["vault_id"],
            "vault_endpoint": vault["vault_endpoint"], "vault_name": vault["vault_name"], "key_id": vault["key_id"],
            "key_name": vault["key_name"], "quota_statements": quota, "budget_email": budget_email,
            "notify_email": email, "create_database": create_database, "create_vm": not o.database_only,
        }
        domains: list[str] = []
        if o.database_only:
            compartments["network"] = {"name": compartments["app"]["name"], "id": compartments["app"]["id"],
                                       "description": "VASH runner and database"}
        else:
            if o.subnet_id:
                ob.check_subnet(o.subnet_id)
                compartments["network"] = dict(compartments["app"])
            else:
                compartments["network"] = self.compartment(tenancy, self.network_name(),
                                                           "Networks of every application (VASH)")
            domains = ob.domains_with_quota(tenancy)
            _, public_key = ob.ssh_public_key()
            values.update(subnet_id=o.subnet_id or "", availability_domain=domains[0], shape=o.shape,
                          ocpus=o.ocpus, memory_in_gbs=o.memory_in_gbs, image_id=ob.latest_image(tenancy),
                          ssh_public_key=public_key, admin_cidr=ob.admin_cidr(), cloud_init_script="vash-runner.sh")
        return values, domains

    def summary(self, values: dict[str, Any]) -> str:
        c = values["compartments"]

        def comp(k: str) -> str:
            return f"{c[k]['name']} ({'exists' if c[k]['id'] else 'new, under the root'})"
        lines = [f"VASH compartment: {comp('app')}", f"Vault and key: {comp('security')}: "
                 + ("existing vault" if values["vault_id"] else f"new vault {values['vault_name']}")
                 + (", existing key" if values["key_id"] else f", new key {values['key_name']}")]
        if values["quota_statements"]:
            lines.append("Free-tier guardrails: quota policy vash-free-tier"
                         + (f" and budget e-mails to {values['budget_email']}" if values["budget_email"] else ""))
        if values["create_database"]:
            lines.append(f"Database: {values['name_prefix']}-db (Always Free), password in the vault")
        if values["create_vm"]:
            micro = values["shape"].endswith("Micro")
            lines.append(f"Network: {comp('network')}" if not values["subnet_id"] else "Network: the existing subnet")
            lines.append("VM: " + (f"{values['shape']} (1 GB, no model on the VM)" if micro else
                                   f"{values['ocpus']}-core {values['memory_in_gbs']} GB Arm, model "
                                   f"{self.ob.options.model}") + f" in {values['availability_domain']}")
        if values["notify_email"]:
            lines.append(f"E-mails about the VM to {values['notify_email']}")
        return "\n".join(f"  - {line}" for line in lines)

    # ---- running --------------------------------------------------------
    def submit(self, tenancy: str, values: dict[str, Any]) -> str:
        workdir = self.ob.prepare_workdir()
        zip_path = package(workdir, self.ob.user_data(workdir), self.ob.options.workdir / "vash-stack.zip")
        stack_id = self.rm.save_stack(self.state.get("id", ""), tenancy, f"vash-{values['name_prefix']}", zip_path,
                                      values)
        self.save(id=stack_id, values=values)
        job = self.rm.apply(stack_id)
        self.save(job=job)
        if values.get("quota_statements"):
            self.ob._save_state(guardrails="applied")
        self.echo(f"Started in OCI Resource Manager (stack vash-{values['name_prefix']}, job {job}).")
        self.echo("It runs in OCI: you can close this window. Watch it with `vash onboard oci --status`, or in the "
                  "Console: Developer Services, Resource Manager, Jobs.")
        return job

    def up(self) -> int:
        tenancy, region = self.ob.tenancy_and_region()
        self.echo(f"Tenancy found, region {region}{' (Cloud Shell)' if self.ob.in_cloud_shell() else ''}")
        running = self.state.get("job")
        if running and self.rm.job(running).get("lifecycle-state") not in DONE:
            self.echo("A VASH setup is already running in Resource Manager:")
            return self.status()
        values, domains = self.interview(tenancy)
        self.echo("VASH will set up:")
        self.echo(self.summary(values))
        if not self.ob.confirm("Start this setup in OCI Resource Manager? It runs in OCI by itself"):
            self.echo("Stopped; nothing was created")
            return 1
        self.save(domains=domains, domain_index=0)
        self.submit(tenancy, values)
        if self.ob.confirm("Watch the progress here? (Ctrl+C stops watching only; the setup goes on in OCI)"):
            return self.watch()
        return 0

    def watch(self) -> int:
        job_id, seen = self.state.get("job", ""), 0
        while True:
            job = self.rm.job(job_id)
            lines = self.rm.logs(job_id)
            for line in lines[seen:]:
                if any(w in line for w in ("Creation complete", "Error", "Apply complete", "Still creating")):
                    self.echo(f"  {line.strip()}")
            seen = len(lines)
            if job.get("lifecycle-state") in DONE:
                return self.report(job_id, job, lines)
            self.ob.sleep(POLL_SECONDS)

    def report(self, job_id: str, job: dict[str, Any], lines: list[str]) -> int:
        state = job.get("lifecycle-state", "")
        if state == "SUCCEEDED":
            out = self.rm.outputs(job_id)
            self.save(outputs={k: v for k, v in out.items() if k != "db_password"})
            self.echo("Setup finished in OCI.")
            if out.get("db_password_secret"):
                self.echo(f"Database password: vault secret '{out['db_password_secret']}'")
            ip = out.get("runner_ip")
            if ip:
                key = self.ob._state().get("ssh_key", "~/.ssh/<key>")
                self.echo(f"VM at {ip}: VASH installs itself there (about 10-20 minutes). Follow it with: ssh -i {key} "
                          f"{self.ob.user}@{ip} 'tail -f /var/log/vash-onboard.log'")
            return 0
        self.echo(f"The setup job ended {state}. Last lines of its log:")
        for line in lines[-LOG_LINES:]:
            self.echo(f"  {line.rstrip()}")
        from .onboard import CAPACITY_ERRORS
        if any(w in line.lower() for line in lines for w in CAPACITY_ERRORS):
            self.echo("Oracle has no free capacity for this VM there right now. Everything else is kept; run "
                      "`vash onboard oci --resume` to try the next availability domain or a smaller VM")
        else:
            self.echo("Fix what the log says, then run `vash onboard oci --resume`; what was made is kept")
        return 1

    def status(self) -> int:
        job_id = self.state.get("job")
        if not job_id:
            self.echo("No VASH setup has been started from this shell")
            return 1
        job = self.rm.job(job_id)
        state = job.get("lifecycle-state", "")
        self.echo(f"Setup job {job_id}: {state} (started {job.get('time-created', '')})")
        lines = self.rm.logs(job_id)
        if state not in DONE:
            for line in lines[-LOG_LINES:]:
                self.echo(f"  {line.rstrip()}")
            return 0
        code = self.report(job_id, job, lines)
        ip = self.state.get("outputs", {}).get("runner_ip")
        key = self.ob._state().get("ssh_key")
        if code == 0 and ip and key:
            from pathlib import Path
            res = self.ob.ssh(Path(key), ip, "cat /var/lib/vash/ready 2>/dev/null || tail -n 5 /var/log/vash-onboard.log")
            self.echo("On the VM:\n" + (res.stdout.strip() or res.stderr.strip() or "(not reachable yet)"))
        return code

    def resume(self) -> int:
        tenancy, _ = self.ob.tenancy_and_region()
        st = self.state
        if not st.get("id"):
            self.echo("No VASH setup has been started from this shell: run `vash onboard oci` first")
            return 1
        values = dict(st["values"])
        job_id = st.get("job", "")
        lines = self.rm.logs(job_id) if job_id else []
        from .onboard import CAPACITY_ERRORS, MICRO
        if values.get("create_vm") and any(w in line.lower() for line in lines for w in CAPACITY_ERRORS):
            domains, index = st.get("domains", []), st.get("domain_index", 0) + 1
            if index < len(domains):
                values["availability_domain"] = domains[index]
                self.echo(f"Trying the next availability domain: {domains[index]}")
            elif not values["shape"].endswith("Micro"):
                micro = self.ob.offer_micro(tenancy, "No availability domain had A1 capacity")
                if not micro:
                    self.echo("Kept the A1 VM; trying the first domain again (capacity comes and goes)")
                    index = 0
                    values["availability_domain"] = domains[0]
                else:
                    domains, index = micro, 0
                    values.update(shape=MICRO, ocpus=1, memory_in_gbs=1, availability_domain=micro[0],
                                  image_id=self.ob.latest_image(tenancy))
            else:
                index = 0
                values["availability_domain"] = domains[0] if domains else values["availability_domain"]
            self.save(domains=domains, domain_index=index)
        self.submit(tenancy, values)
        if self.ob.confirm("Watch the progress here? (Ctrl+C stops watching only; the setup goes on in OCI)"):
            return self.watch()
        return 0

    def down(self) -> int:
        stack_id = self.state.get("id")
        if not stack_id:
            self.echo("Nothing to remove: no VASH stack was made from this shell")
            return 0
        if not self.ob.confirm("Remove what the VASH stack made (VM, network, vault, key, database, guardrails)? "
                               "Compartments are kept; a vault is deleted by OCI only after its waiting period"):
            self.echo("Stopped; nothing was removed")
            return 1
        job = self.rm.destroy(stack_id)
        self.save(job=job)
        self.echo(f"Removal started in OCI Resource Manager (job {job}); watch it with `vash onboard oci --status`")
        return 0
