"""Free-tier guardrails: a quota policy that allows only Always Free amounts, and a budget e-mail.

Quota statements use OCI limit names, which differ between tenancies and change over time, so
every name is looked up in the tenancy's own limit definitions first; a statement whose name is
not found is left out and said so. The owner sees the statements and says yes before anything is
applied. Built with Oracle's CD3 modules through the foundation environment.
"""
from __future__ import annotations

import re
from typing import Any, Callable

from vash.core.exceptions import VashError

from .foundation import Foundation

# (quota family, limit service, pattern of the limit name, Always Free amount, what it is)
ALLOWED = (
    ("compute-core", "compute", r"^standard-a1-core-count$", 4, "Arm A1 cores"),
    ("compute-memory", "compute", r"^standard-a1-memory-count$", 24, "Arm A1 memory (GB)"),
    ("compute-core", "compute", r"^standard-e2-micro-core-count$|^vm-standard-e2-1-micro-count$", 2, "AMD Micro VMs"),
    ("block-storage", "block-storage", r"^total-storage-gb$", 200, "block and boot volume storage (GB)"),
    ("database", "database", r"^adb-free-count$", 2, "Always Free Autonomous Databases"),
)
ZEROED = (("compute-core", "compute"), ("compute-memory", "compute"), ("database", "database"))


class Guardrails:
    def __init__(self, oci: Callable[..., Any], echo: Callable[[str], None], confirm: Callable[[str], bool],
                 build: Foundation):
        self.oci, self.echo, self.confirm, self.build = oci, echo, confirm, build

    def limit_names(self, tenancy: str, service: str) -> list[str]:
        try:
            data = self.oci("limits", "definition", "list", "--compartment-id", tenancy, "--service-name", service,
                            "--all").get("data", [])
        except VashError:
            return []
        return [d.get("name", "") for d in data or []]

    def statements(self, tenancy: str) -> list[str]:
        names = {svc: self.limit_names(tenancy, svc) for svc in {svc for _, svc, *_ in ALLOWED}}
        allowed: list[str] = []
        for family, service, pattern, amount, what in ALLOWED:
            found = next((n for n in names[service] if re.match(pattern, n)), None)
            if found:
                allowed.append(f"set {family} quota {found} to {amount} in tenancy")
            else:
                self.echo(f"  (no limit for {what} in this tenancy: left out)")
        # A family is zeroed only when its Always Free amount is allowed again, so nothing free is lost.
        families = {s.split()[1] for s in allowed}
        zeroed = [f"zero {family} quotas in tenancy" for family, _ in ZEROED if family in families]
        return zeroed + allowed

    def apply(self, tenancy: str, email: str) -> bool:
        """Asks, then applies; True when applied."""
        statements = self.statements(tenancy)
        if not statements:
            self.echo("No Always Free limit names were found in this tenancy; no quota policy is made")
        else:
            self.echo("Free-tier guardrail: this quota policy lets OCI refuse anything beyond Always Free:")
            for s in statements:
                self.echo(f"  {s}")
        budget = f" and a monthly budget that e-mails {email} at the first spend" if email else ""
        if not self.confirm(f"Apply this quota policy{budget}? Nothing you use now changes; only paid use is "
                            "blocked (a budget only warns, OCI has no hard spending cap)"):
            self.echo("Free-tier guardrails not applied")
            return False
        self.echo("Applying the guardrails (CD3 quota-policy and budget modules) ...")
        self.build.guardrails(statements, email)
        self.echo("Free-tier guardrails applied: quota policy 'vash-free-tier'"
                  + (" and budget 'vash-free-tier'" if email else ""))
        return True
