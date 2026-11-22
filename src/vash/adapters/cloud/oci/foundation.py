"""Compartments, vaults, keys and Always Free databases through Oracle's CD3 Automation Toolkit modules (terraform).

The `foundation` environment (iac/oci/environments/foundation) holds four maps in its
terraform.tfvars.json: compartments, vaults, keys and databases (VASH's own module for the database: the
CD3 adb module has no free-tier option). Each create adds one entry and applies;
terraform leaves what already exists as it is. When an apply fails, the entry is taken out again,
so a later run does not retry something the owner did not choose again.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from vash.core.exceptions import VashError

from .adapter import Adapter

ENVIRONMENT = "foundation"
LIMIT_HINT = ("OCI's limit for this tenancy is reached (vaults waiting for deletion still count). "
              "Run again and pick an existing vault by S.No, or ask Oracle for a higher limit")

DB_LIMIT_HINT = ("Always Free allows 2 Autonomous Databases per tenancy (stopped ones count too). "
                 "Delete one you no longer need, or use an existing one")


# Errors that pass by themselves: IAM shows a new compartment late (404 for a while), and the address of a new
# vault (<id>-management.kms.<region>.oraclecloud.com) is not in DNS for the first minutes (seen live in Frankfurt).
TRANSIENT = ("NotAuthorizedOrNotFound", "no such host", "i/o timeout")
TRANSIENT_WAIT = 30  # seconds between tries
TRANSIENT_TRIES = 10  # about 5 minutes

# Each map of terraform.tfvars.json, the module that builds its entries, and that module's main object in the state.
SECTIONS = {
    "compartments": ("compartment", "oci_identity_compartment.compartment"),
    "vaults": ("vault", "oci_kms_vault.vault"),
    "keys": ("key", "oci_kms_key.key"),
    "databases": ("database", "oci_database_autonomous_database.db"),
}


class Foundation:
    def __init__(self, workdir: Path, provider: dict[str, Any], echo: Callable[[str], None],
                 sleep: Callable[[float], None]):
        self.workdir = workdir  # a copy of iac/oci, prepared by onboarding
        self.provider = provider  # region, tenancy_ocid, oci_auth
        self.echo = echo
        self.sleep = sleep

    @property
    def tfvars(self) -> Path:
        return self.workdir / "environments" / ENVIRONMENT / "terraform.tfvars.json"

    def _values(self) -> dict[str, Any]:
        values = json.loads(self.tfvars.read_text()) if self.tfvars.exists() else {}
        for name in SECTIONS:
            values.setdefault(name, {})
        self._restore_from_state(values)
        return {**values, **self.provider}

    def _state(self) -> list[dict[str, Any]]:
        path = self.tfvars.with_name("terraform.tfstate")
        try:
            return json.loads(path.read_text()).get("resources", []) if path.exists() else []
        except (ValueError, OSError):
            return []

    def _in_state(self, section: str, name: str) -> dict[str, Any] | None:
        """The state's record of `name` in `section` (its first instance), when terraform has made it."""
        module, address = SECTIONS[section]
        rtype, rname = address.split(".")
        for res in self._state():
            if res.get("module") == f'module.{module}["{name}"]' and res.get("type") == rtype \
                    and res.get("name") == rname and res.get("instances"):
                return res["instances"][0]
        return None

    def _restore_from_state(self, values: dict[str, Any]) -> None:
        """An object terraform made but the tfvars lost (an older VASH forgot it after a failed apply) is put back,
        so a later apply never deletes it."""
        for section, (module, _) in SECTIONS.items():
            for res in self._state():
                prefix = f'module.{module}["'
                mod = res.get("module", "")
                if not mod.startswith(prefix) or not res.get("instances"):
                    continue
                name = mod[len(prefix):-2]
                if name in values[section] or self._in_state(section, name) is None:
                    continue
                attrs = res["instances"][0].get("attributes", {})
                if section == "compartments":
                    values[section][name] = attrs.get("description", "")
                elif section == "keys":
                    values[section][name] = {"compartment_id": attrs.get("compartment_id", ""),
                                             "management_endpoint": attrs.get("management_endpoint", "")}
                else:
                    values[section][name] = {"compartment_id": attrs.get("compartment_id", "")}
                self.echo(f"Found {name} in terraform's records; keeping it")

    def _untaint(self, adapter: Adapter) -> None:
        """A create whose read-back failed leaves the object marked 'tainted', and terraform would replace it
        (a key would be scheduled for deletion). The object was made, so it is marked healthy again."""
        for module, address in SECTIONS.values():
            rtype, rname = address.split(".")
            for res in self._state():
                mod = res.get("module", "")
                if (mod.startswith(f'module.{module}["') and res.get("type") == rtype and res.get("name") == rname
                        and any(i.get("status") == "tainted" for i in res.get("instances", []))):
                    adapter.untaint(ENVIRONMENT, f"{mod}.{address}")

    def _write(self, values: dict[str, Any]) -> None:
        self.tfvars.write_text(json.dumps(values, indent=2) + "\n")
        self.tfvars.chmod(0o600)

    def _apply(self, section: str, name: str, entry: Any) -> dict[str, Any]:
        def change(values: dict[str, Any]) -> None:
            values[section][name] = entry
        return self._change(change, name)

    def _change(self, change: Callable[[dict[str, Any]], None], name: str,
                env: dict[str, str] | None = None) -> dict[str, Any]:
        before = self._values()
        after = json.loads(json.dumps(before))
        change(after)
        self._write(after)
        adapter = Adapter({"iac_dir": str(self.workdir)})
        try:
            for attempt in range(1, TRANSIENT_TRIES + 1):
                try:
                    self._untaint(adapter)
                    return adapter.apply(ENVIRONMENT, approved=True, env=env)
                except VashError as exc:
                    if attempt == TRANSIENT_TRIES or not any(t in str(exc) for t in TRANSIENT):
                        raise
                    self.echo(f"OCI is still making the new object reachable; trying again in {TRANSIENT_WAIT} "
                              f"seconds ({attempt} of {TRANSIENT_TRIES - 1}) ...")
                    self.sleep(TRANSIENT_WAIT)
            raise AssertionError("unreachable")
        except VashError as exc:
            # Not created: forget it, so a later run does not retry it. What terraform did make stays (the next
            # apply would otherwise delete it).
            kept = json.loads(json.dumps(before))
            for section in SECTIONS:
                for name, entry in after.get(section, {}).items():
                    if name not in kept[section] and self._in_state(section, name) is not None:
                        kept[section][name] = entry
            self._write(kept)
            if "LimitExceeded" in str(exc):
                hint = DB_LIMIT_HINT if name.startswith("the database") else LIMIT_HINT
                raise VashError(f"Could not create {name}: the tenancy limit is reached", hint) from exc
            raise

    def guardrails(self, statements: list[str], budget_email: str) -> None:
        """The free-tier quota policy and the budget e-mail (CD3 quota-policy, budget, budget-alert-rule)."""
        def change(values: dict[str, Any]) -> None:
            values["quota_statements"] = statements
            values["budget_email"] = budget_email
        self._change(change, "the free-tier guardrails")

    def compartment(self, name: str, description: str) -> str:
        out = self._apply("compartments", name, description)
        return out.get("compartment_ids", {}).get("value", {}).get(name, "")

    def vault(self, name: str, compartment_id: str) -> tuple[str, str]:
        out = self._apply("vaults", name, {"compartment_id": compartment_id})
        made = out.get("vaults", {}).get("value", {}).get(name, {})
        return made.get("id", ""), made.get("management_endpoint", "")

    def key(self, name: str, compartment_id: str, management_endpoint: str) -> str:
        out = self._apply("keys", name, {"compartment_id": compartment_id,
                                         "management_endpoint": management_endpoint})
        return out.get("key_ids", {}).get("value", {}).get(name, "")

    def database(self, name: str, compartment_id: str, admin_password: str) -> dict[str, str]:
        """An Always Free Autonomous Database `<name>-db`; the password goes to terraform through the environment
        only, never into terraform.tfvars.json. Returns {id, db_name}."""
        def change(values: dict[str, Any]) -> None:
            values["databases"][name] = {"compartment_id": compartment_id}
        out = self._change(change, f"the database {name}-db",
                           env={"TF_VAR_db_admin_passwords": json.dumps({name: admin_password})})
        return out.get("databases", {}).get("value", {}).get(name, {})
