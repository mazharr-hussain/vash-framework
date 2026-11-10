"""Free-tier guardrails: a quota policy that allows only Always Free amounts, and a budget e-mail.

Quota statements use OCI limit names, which differ between tenancies and change over time, so
every name is looked up in the tenancy's own limit definitions first; a statement whose name is
not found is left out and said so. The owner sees the statements and says yes before anything is
applied. Built with Oracle's CD3 modules through the foundation environment.
"""
from __future__ import annotations

from typing import Any, Callable

from vash.core.exceptions import VashError

from .foundation import Foundation

# (quota family, limit service, exact limit name, Always Free amount, what it is). Exact names only: a limit
# name is not always a valid quota name for the family (seen live: vm-standard-e2-1-micro-count is a compute
# limit but not a compute-core quota), and one invalid statement makes OCI refuse the whole policy.
ALLOWED = (
    ("compute-core", "compute", "standard-a1-core-count", 4, "Arm A1 cores"),
    ("compute-memory", "compute", "standard-a1-memory-count", 24, "Arm A1 memory (GB)"),
    ("compute-core", "compute", "standard-e2-micro-core-count", 2, "AMD Micro VMs"),
    ("block-storage", "block-storage", "total-storage-gb", 200, "block and boot volume storage (GB)"),
    ("database", "database", "adb-free-count", 2, "Always Free Autonomous Databases"),
)
# OCI also checks a regional A1 limit at launch, which "zero <family>" zeroes too and which
# `limits definition list` may not return: allowed whenever the per-domain name is found (both regional names
# appeared in OCI's own QuotaExceeded error).
REGIONAL = {"standard-a1-core-count": "standard-a1-core-regional-count",
            "standard-a1-memory-count": "standard-a1-memory-regional-count"}
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
        for family, service, name, amount, what in ALLOWED:
            if name in names[service]:
                allowed += [f"set {family} quota {n} to {amount} in tenancy" for n in [name, REGIONAL.get(name)] if n]
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
