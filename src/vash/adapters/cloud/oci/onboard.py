"""One-command onboarding on OCI: find quota, create the Always Free runner VM, install VASH on it.

Meant to run in OCI Cloud Shell, where the oci CLI and terraform are already signed in.
Every OCI call goes through the oci CLI with an argument list; every terraform call goes
through the cloud Adapter of this package.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Sequence

from vash.core.exceptions import AdapterNotInstalled, VashError
from vash.core.paths import vash_root

from .adapter import Adapter

SHAPE = "VM.Standard.A1.Flex"
ENVIRONMENT = "always-free"
DEFAULT_SOURCE = "git+https://github.com/mazharr-hussain/vash-framework.git"
DEFAULT_MODEL = "qwen2.5-coder:7b"
CAPACITY_ERRORS = ("out of host capacity", "outofhostcapacity", "out of capacity")

Runner = Callable[..., subprocess.CompletedProcess]


@dataclass
class Options:
    """What the user chose on the command line."""

    compartment_name: str = "vash"
    ocpus: int = 2
    memory_in_gbs: int = 12
    os_name: str = "Canonical Ubuntu"
    os_version: str = "24.04"
    admin_cidr: str | None = None
    workdir: Path = field(default_factory=lambda: Path.home() / ".vash" / "oci")
    vash_source: str = DEFAULT_SOURCE
    model: str = DEFAULT_MODEL
    runner_repo: str | None = None
    wait_minutes: int = 30


class Onboarding:
    """The onboarding steps; each one prints what it found."""

    def __init__(
        self,
        options: Options,
        run: Runner = subprocess.run,
        echo: Callable[[str], None] = print,
        confirm: Callable[[str], bool] | None = None,
        sleep: Callable[[float], None] = time.sleep,
        env: dict[str, str] | None = None,
    ):
        self.options = options
        self._run = run
        self.echo = echo
        self.confirm = confirm or (lambda _question: True)
        self.sleep = sleep
        self.env = dict(os.environ if env is None else env)

    # ---- helpers -------------------------------------------------------
    def _cmd(self, args: Sequence[str], stdin: str | None = None) -> subprocess.CompletedProcess:
        try:
            return self._run(list(args), check=False, capture_output=True, text=True, input=stdin)
        except FileNotFoundError:
            raise AdapterNotInstalled(f"{args[0]} is not installed", f"Install {args[0]}, or run this in OCI Cloud Shell")

    def oci(self, *args: str) -> Any:
        res = self._cmd(["oci", *args, "--output", "json"])
        if res.returncode != 0:
            raise VashError(f"oci {' '.join(args[:3])} failed: {res.stderr.strip()}", "Check the OCI policy and the oci CLI setup")
        out = res.stdout.strip()
        return json.loads(out) if out else {}

    # ---- discovery -----------------------------------------------------
    def in_cloud_shell(self) -> bool:
        return self.env.get("OCI_CLI_CLOUD_SHELL", "").lower() == "true"

    def tenancy_and_region(self) -> tuple[str, str]:
        tenancy = self.env.get("OCI_TENANCY") or self.env.get("OCI_CLI_TENANCY")
        region = self.env.get("OCI_REGION") or self.env.get("OCI_CLI_REGION")
        if not (tenancy and region):
            cfg = Path(self.env.get("OCI_CONFIG_FILE", str(Path.home() / ".oci" / "config")))
            if cfg.exists():
                for line in cfg.read_text().splitlines():
                    key, _, value = line.partition("=")
                    key, value = key.strip(), value.strip()
                    if key == "tenancy" and not tenancy:
                        tenancy = value
                    if key == "region" and not region:
                        region = value
        if not (tenancy and region):
            raise VashError("Tenancy or region not found", "Run in OCI Cloud Shell, or run `oci setup config` first")
        return tenancy, region

    def ensure_compartment(self, tenancy: str) -> str:
        name = self.options.compartment_name
        found = self.oci("iam", "compartment", "list", "--compartment-id", tenancy,
                         "--name", name, "--lifecycle-state", "ACTIVE")
        items = found.get("data", []) if isinstance(found, dict) else []
        if items:
            self.echo(f"Compartment '{name}' exists")
            return items[0]["id"]
        created = self.oci("iam", "compartment", "create", "--compartment-id", tenancy, "--name", name,
                           "--description", "VASH runner (created by vash onboard)",
                           "--wait-for-state", "ACTIVE")
        self.echo(f"Compartment '{name}' created")
        return created["data"]["id"]

    def availability_domains(self, tenancy: str) -> list[str]:
        data = self.oci("iam", "availability-domain", "list", "--compartment-id", tenancy).get("data", [])
        return [ad["name"] for ad in data]

    def _available(self, tenancy: str, ad: str, limit: str) -> float:
        data = self.oci("limits", "resource-availability", "get", "--service-name", "compute",
                        "--limit-name", limit, "--compartment-id", tenancy, "--availability-domain", ad).get("data", {})
        value = data.get("available")
        return float(value) if value is not None else 0.0

    def domains_with_quota(self, tenancy: str) -> list[str]:
        fits = []
        for ad in self.availability_domains(tenancy):
            cores = self._available(tenancy, ad, "standard-a1-core-count")
            memory = self._available(tenancy, ad, "standard-a1-memory-count")
            ok = cores >= self.options.ocpus and memory >= self.options.memory_in_gbs
            self.echo(f"{ad}: {cores:g} A1 cores, {memory:g} GB free{'' if ok else ' (not enough)'}")
            if ok:
                fits.append(ad)
        if not fits:
            raise VashError(
                f"No availability domain has {self.options.ocpus} A1 cores and {self.options.memory_in_gbs} GB free",
                "Free A1 quota (stop or delete A1 instances), or pass --ocpus/--memory smaller values",
            )
        return fits

    def latest_image(self, compartment: str) -> str:
        data = self.oci("compute", "image", "list", "--compartment-id", compartment,
                        "--operating-system", self.options.os_name,
                        "--operating-system-version", self.options.os_version,
                        "--shape", SHAPE, "--sort-by", "TIMECREATED", "--sort-order", "DESC",
                        "--limit", "1").get("data", [])
        if not data:
            raise VashError(f"No {self.options.os_name} {self.options.os_version} image for {SHAPE}",
                            "Pass --os-version with a version OCI offers for Arm")
        self.echo(f"Image: {data[0].get('display-name', data[0]['id'])}")
        return data[0]["id"]

    def ssh_public_key(self) -> tuple[Path, str]:
        """Reuse an existing key, else create one: ed25519, or RSA 4096 where FIPS mode forbids ed25519 (Cloud Shell)."""
        ssh_dir = Path.home() / ".ssh"
        for name in ("id_ed25519", "id_rsa"):
            key = ssh_dir / name
            if key.exists() and key.with_suffix(".pub").exists():
                return key, key.with_suffix(".pub").read_text().strip()
        ssh_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        errors = []
        for name, args in (("id_ed25519", ["-t", "ed25519"]), ("id_rsa", ["-t", "rsa", "-b", "4096"])):
            key = ssh_dir / name
            res = self._cmd(["ssh-keygen", "-q", *args, "-N", "", "-f", str(key)])
            if res.returncode == 0 and key.with_suffix(".pub").exists():
                self.echo(f"SSH key created: {key}")
                return key, key.with_suffix(".pub").read_text().strip()
            errors.append(f"{name}: {res.stderr.strip()}")
        raise VashError(f"ssh-keygen failed: {'; '.join(errors)}",
                        "Create a key with: ssh-keygen -t rsa -b 4096 -N '' -f ~/.ssh/id_rsa")

    def admin_cidr(self) -> str:
        if self.options.admin_cidr:
            return self.options.admin_cidr
        try:
            with urllib.request.urlopen("https://checkip.amazonaws.com", timeout=10) as resp:
                ip = resp.read().decode().strip()
        except OSError as exc:
            raise VashError(f"Could not find this shell's public IP: {exc}", "Pass --admin-cidr x.x.x.x/32")
        return f"{ip}/32"

    # ---- infrastructure --------------------------------------------------
    def prepare_workdir(self) -> Path:
        """Copy the IaC to a work folder that keeps the terraform state between runs."""
        src = vash_root() / "iac" / "oci"
        if not src.is_dir():
            raise VashError(f"IaC not found at {src}", "Reinstall VASH, or set VASH_HOME to a checkout")
        dest = self.options.workdir
        for item in src.rglob("*"):
            if item.is_file() and ".terraform" not in item.parts:
                target = dest / item.relative_to(src)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target)
        return dest

    def user_data(self, workdir: Path) -> str:
        text = (workdir / "cloud-init" / "vash-runner.sh").read_text()
        return text.replace("@@VASH_SOURCE@@", self.options.vash_source).replace("@@MODEL@@", self.options.model)

    def tfvars_path(self, workdir: Path) -> Path:
        return workdir / "environments" / ENVIRONMENT / "terraform.tfvars.json"

    def existing_tfvars(self) -> dict[str, Any]:
        path = self.tfvars_path(self.options.workdir)
        return json.loads(path.read_text()) if path.exists() else {}

    def write_tfvars(self, workdir: Path, values: dict[str, Any]) -> None:
        path = self.tfvars_path(workdir)
        path.write_text(json.dumps(values, indent=2) + "\n")
        path.chmod(0o600)

    def create(self, workdir: Path, base: dict[str, Any], domains: list[str]) -> dict[str, Any]:
        adapter = Adapter({"iac_dir": str(workdir)})
        last: VashError | None = None
        for ad in domains:
            self.write_tfvars(workdir, {**base, "availability_domain": ad})
            self.echo(f"Creating the VM in {ad} ...")
            try:
                return adapter.apply(ENVIRONMENT, approved=True)
            except VashError as exc:
                if not any(word in str(exc).lower() for word in CAPACITY_ERRORS):
                    raise
                self.echo(f"{ad}: out of host capacity, trying the next domain")
                last = exc
        raise VashError(f"Every availability domain is out of A1 capacity: {last}",
                        "Run `vash onboard oci` again later; free A1 capacity comes and goes")

    # ---- the VM --------------------------------------------------------
    def ssh(self, key: Path, ip: str, command: str, stdin: str | None = None) -> subprocess.CompletedProcess:
        return self._cmd(["ssh", "-i", str(key), "-o", "StrictHostKeyChecking=accept-new",
                          "-o", "ConnectTimeout=10", "-o", "BatchMode=yes", f"ubuntu@{ip}", command], stdin=stdin)

    def wait_ready(self, key: Path, ip: str) -> str:
        deadline = self.options.wait_minutes * 60
        waited = 0
        while waited <= deadline:
            res = self.ssh(key, ip, "cat /var/lib/vash/ready")
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
            self.sleep(30)
            waited += 30
        raise VashError(f"The VM did not finish installing in {self.options.wait_minutes} minutes",
                        f"ssh ubuntu@{ip} and read /var/log/vash-onboard.log")

    def register_runner(self, key: Path, ip: str, token: str) -> None:
        repo = self.options.runner_repo
        command = (
            "cd ~/actions-runner && "
            f"./config.sh --unattended --replace --url https://github.com/{repo} "
            "--name vash-runner --labels self-hosted,vash --token \"$(cat)\" && "
            "sudo ./svc.sh install ubuntu && sudo ./svc.sh start"
        )
        res = self.ssh(key, ip, command, stdin=token)
        if res.returncode != 0:
            raise VashError(f"Runner registration failed: {res.stderr.strip()[-300:]}",
                            "Get a new token (it expires after 1 hour) and run `vash onboard oci --runner-repo` again")
        self.echo(f"GitHub runner registered for {repo}")

    # ---- entry points --------------------------------------------------
    def up(self, runner_token: Callable[[], str] | None = None) -> int:
        tenancy, region = self.tenancy_and_region()
        self.echo(f"Tenancy found, region {region}{' (Cloud Shell)' if self.in_cloud_shell() else ''}")
        compartment = self.ensure_compartment(tenancy)
        previous = self.existing_tfvars()
        if previous:
            # A VM made earlier keeps its domain and image, so terraform repairs it instead of replacing it.
            self.echo(f"Earlier onboarding found in {self.options.workdir}; checking that VM")
            domains = [previous["availability_domain"]]
            image = previous["image_id"]
        else:
            domains = self.domains_with_quota(tenancy)
            image = self.latest_image(compartment)
        key, public_key = self.ssh_public_key()
        cidr = self.admin_cidr()
        self.echo(f"SSH will be open to {cidr} only")
        if not self.confirm(f"Create a {self.options.ocpus}-core {self.options.memory_in_gbs} GB Always Free VM in {region}?"):
            self.echo("Stopped; nothing was created")
            return 1
        workdir = self.prepare_workdir()
        base = {
            "region": region,
            "compartment_id": compartment,
            "image_id": image,
            "admin_cidr": cidr,
            "ssh_public_key": public_key,
            "oci_auth": "InstancePrincipal" if self.in_cloud_shell() else "ApiKey",
            "ocpus": self.options.ocpus,
            "memory_in_gbs": self.options.memory_in_gbs,
            "user_data": self.user_data(workdir),
        }
        outputs = self.create(workdir, base, domains)
        ip = outputs.get("runner_ip", {}).get("value")
        if not ip:
            raise VashError("The VM has no public IP", f"Check the instance in compartment '{self.options.compartment_name}'")
        self.echo(f"VM is up at {ip}; installing VASH, terraform and Ollama (about 10-20 minutes) ...")
        ready = self.wait_ready(key, ip)
        self.echo(ready)
        if self.options.runner_repo and runner_token is not None:
            self.register_runner(key, ip, runner_token())
        self.echo(f"Done. Connect with: ssh -i {key} ubuntu@{ip}")
        return 0

    def down(self) -> int:
        workdir = self.options.workdir
        if not self.tfvars_path(workdir).exists():
            self.echo(f"Nothing to remove: no onboarding state in {workdir}")
            return 0
        if not self.confirm("Destroy the VASH VM and its network?"):
            self.echo("Stopped; nothing was removed")
            return 1
        Adapter({"iac_dir": str(workdir)}).destroy(ENVIRONMENT, approved=True)
        self.echo("VASH VM and network removed")
        return 0


def run_cli(args: Any) -> int:
    """Entry point for `vash onboard oci`."""
    import getpass

    options = Options(
        ocpus=args.ocpus,
        memory_in_gbs=args.memory,
        os_version=args.os_version,
        admin_cidr=args.admin_cidr,
        runner_repo=args.runner_repo,
        model=args.model,
    )
    if args.workdir:
        options.workdir = Path(args.workdir)

    def ask(question: str) -> bool:
        if args.yes:
            return True
        return input(f"{question} [y/N] ").strip().lower() in ("y", "yes")

    def token() -> str:
        return getpass.getpass(f"GitHub runner registration token for {args.runner_repo} (not stored): ").strip()

    onboarding = Onboarding(options, confirm=ask)
    if args.down:
        return onboarding.down()
    return onboarding.up(runner_token=token if args.runner_repo else None)
