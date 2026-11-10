"""Compartments, vaults and keys through Oracle's CD3 Automation Toolkit modules (terraform).

The `foundation` environment (iac/oci/environments/foundation) holds three maps in its
terraform.tfvars.json: compartments, vaults and keys. Each create adds one entry and applies;
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
        for name in ("compartments", "vaults", "keys"):
            values.setdefault(name, {})
        return {**values, **self.provider}

    def _write(self, values: dict[str, Any]) -> None:
        self.tfvars.write_text(json.dumps(values, indent=2) + "\n")
        self.tfvars.chmod(0o600)

    def _apply(self, section: str, name: str, entry: Any) -> dict[str, Any]:
        def change(values: dict[str, Any]) -> None:
            values[section][name] = entry
        return self._change(change, name)

    def _change(self, change: Callable[[dict[str, Any]], None], name: str) -> dict[str, Any]:
        before = self._values()
        after = json.loads(json.dumps(before))
        change(after)
        self._write(after)
        adapter = Adapter({"iac_dir": str(self.workdir)})
        try:
            try:
                return adapter.apply(ENVIRONMENT, approved=True)
            except VashError as exc:
                if "NotAuthorizedOrNotFound" not in str(exc):
                    raise
                # IAM is eventually consistent: a new compartment can read as 404 for a while.
                self.echo("OCI is still making the new object visible; trying again in 30 seconds ...")
                self.sleep(30)
                return adapter.apply(ENVIRONMENT, approved=True)
        except VashError as exc:
            self._write(before)  # not created: forget it, so a later run does not retry it
            if "LimitExceeded" in str(exc):
                raise VashError(f"Could not create {name}: the tenancy limit is reached", LIMIT_HINT) from exc
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
