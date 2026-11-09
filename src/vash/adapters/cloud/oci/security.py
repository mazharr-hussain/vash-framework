"""Where VASH keeps its secrets: an OCI vault and an encryption key, chosen by the owner.

VASH lists the vaults (and their keys) that already exist in the tenancy; the owner picks one
by S.No, or creates a new free virtual vault in a security compartment (default name 'security',
or a name the owner types). Vaults stay out of application compartments, so deleting an
application never waits for OCI's vault deletion period (7 to 30 days).
Reading uses the oci CLI; compartments, vaults and keys are created with Oracle's CD3 Automation
Toolkit modules (terraform, see foundation.py).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable

from vash.core.exceptions import VashError

from .foundation import Foundation

DEFAULT_SECURITY = "security"
COMPARTMENT_RE = re.compile(r"^[A-Za-z0-9._-]{1,100}$")
VAULT_TYPES = {"DEFAULT": "virtual (free)", "VIRTUAL_PRIVATE": "private (paid)"}


@dataclass(frozen=True)
class Vault:
    no: int
    name: str
    kind: str
    compartment: str
    compartment_id: str
    id: str
    endpoint: str  # management endpoint, needed for key calls
    keys: tuple[tuple[str, str], ...] = ()  # (name, id) of enabled keys


class VaultSetup:
    def __init__(self, oci: Callable[..., Any], echo: Callable[[str], None], confirm: Callable[[str], bool],
                 ask: Callable[[str, str], str], build: Foundation):
        self.oci, self.echo, self.confirm, self.ask, self.build = oci, echo, confirm, ask, build

    # ---- reading -------------------------------------------------------
    def compartments(self, tenancy: str) -> dict[str, str]:
        comps = self.oci("iam", "compartment", "list", "--compartment-id", tenancy, "--compartment-id-in-subtree",
                         "true", "--lifecycle-state", "ACTIVE", "--access-level", "ACCESSIBLE", "--all").get("data", [])
        return {tenancy: "(root)", **{c["id"]: c["name"] for c in comps}}

    def vaults(self, tenancy: str) -> list[Vault]:
        found: list[Vault] = []
        for comp_id, comp in self.compartments(tenancy).items():
            try:
                items = self.oci("kms", "management", "vault", "list", "--compartment-id", comp_id,
                                 "--all").get("data", [])
            except VashError:
                continue
            for v in items or []:
                if v.get("lifecycle-state") != "ACTIVE":
                    continue
                endpoint = v.get("management-endpoint") or ""
                found.append(Vault(len(found) + 1, v.get("display-name") or "", v.get("vault-type") or "", comp,
                                   comp_id, v.get("id") or "", endpoint, self.keys(comp_id, endpoint)))
        return found

    def keys(self, compartment_id: str, endpoint: str) -> tuple[tuple[str, str], ...]:
        if not endpoint:
            return ()
        try:
            items = self.oci("kms", "management", "key", "list", "--compartment-id", compartment_id,
                             "--endpoint", endpoint, "--all").get("data", [])
        except VashError:
            return ()
        return tuple((k.get("display-name") or "", k.get("id") or "") for k in items or []
                     if k.get("lifecycle-state") == "ENABLED")

    def show(self, vaults: list[Vault]) -> None:
        headers = ("S.No", "Vault", "Type", "Compartment", "Keys")
        table = [headers] + [(str(v.no), v.name, VAULT_TYPES.get(v.kind, v.kind), v.compartment,
                              ", ".join(n for n, _ in v.keys) or "(none)") for v in vaults]
        widths = [max(len(r[i]) for r in table) for i in range(len(headers))]
        line = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
        self.echo(line)
        for i, row in enumerate(table):
            self.echo("| " + " | ".join(c.ljust(widths[j]) for j, c in enumerate(row)) + " |")
            if i == 0:
                self.echo(line)
        self.echo(line)

    # ---- choosing ------------------------------------------------------
    def _number(self, question: str, allowed: list[int]) -> int | None:
        """An S.No from `allowed`, or None for Enter / 0; a wrong answer is explained and asked again."""
        for attempt in range(3):
            answer = self.ask(question, "").strip()
            if answer in ("", "0"):
                return None
            if answer.isdigit() and int(answer) in allowed:
                return int(answer)
            if attempt < 2:
                self.echo(f"'{answer}' is not a valid choice here. Type one of: "
                          f"{', '.join(map(str, allowed))}; or press Enter (or 0) to create a new one")
        self.echo("No valid choice after 3 tries: a new one is created")
        return None

    def choose(self, tenancy: str, key_name: str) -> dict[str, str]:
        """{vault_id, vault_endpoint, key_id, vault_compartment_id}: existing ones or new ones, as the owner chooses."""
        self.echo("Looking for vaults and keys in the tenancy ...")
        vaults = self.vaults(tenancy)
        vault: Vault | None = None
        if vaults:
            self.echo("VASH keeps its secrets (passwords, tokens) in an OCI vault. These vaults exist:")
            self.show(vaults)
            no = self._number("Which vault should VASH use? Type its S.No, or press Enter (or 0) to create a new one",
                              [v.no for v in vaults])
            vault = next((v for v in vaults if v.no == no), None)
        else:
            self.echo("No vault found: VASH keeps its secrets (passwords, tokens) in an OCI vault; one is created now")
        if vault is None:
            vault = self.create_vault(tenancy)
        key_id = ""
        if vault.keys:
            listed = list(enumerate(vault.keys, 1))
            self.echo(f"Keys in vault {vault.name}: " + ", ".join(f"{i} = {n}" for i, (n, _) in listed))
            no = self._number(f"Which key should encrypt VASH's secrets? Type its number, or press Enter (or 0) to "
                              f"create a new key '{key_name}'", [i for i, _ in listed])
            key_id = next((k for i, (_, k) in listed if i == no), "")
        if not key_id:
            key_id = self.create_key(vault, key_name)
        self.echo(f"VASH uses vault {vault.name} (compartment {vault.compartment})")
        return {"vault_id": vault.id, "vault_endpoint": vault.endpoint, "key_id": key_id,
                "vault_compartment_id": vault.compartment_id}

    # ---- creating ------------------------------------------------------
    def security_compartment(self, tenancy: str) -> tuple[str, str]:
        if self.confirm(f"Keep the new vault in a compartment named '{DEFAULT_SECURITY}' "
                        "(one place for every application's vaults and keys)?"):
            name = DEFAULT_SECURITY
        else:
            name = ""
            for _ in range(3):
                answer = self.ask("Name of the compartment for vaults and keys (an existing name, or a new one)",
                                  "").strip()
                if COMPARTMENT_RE.match(answer):
                    name = answer
                    break
                self.echo("Please type a name: letters, digits, '.', '-' and '_', at most 100")
            if not name:
                raise VashError("No compartment name for the vault", "Run again and type a name")
        found = self.oci("iam", "compartment", "list", "--compartment-id", tenancy, "--name", name,
                         "--lifecycle-state", "ACTIVE", "--compartment-id-in-subtree", "true",
                         "--access-level", "ACCESSIBLE").get("data", [])
        if found:
            self.echo(f"Compartment '{name}' exists")
            return name, found[0]["id"]
        if not self.confirm(f"Compartment '{name}' does not exist. Create it?"):
            raise VashError(f"No compartment '{name}' for the vault", "Run again and choose an existing vault")
        self.echo(f"Creating compartment {name} (CD3 iam-compartment module) ...")
        comp_id = self.build.compartment(name, "Vaults and keys of every application (created by vash onboard)")
        self.echo(f"Compartment '{name}' created")
        return name, comp_id

    def create_vault(self, tenancy: str) -> Vault:
        comp, comp_id = self.security_compartment(tenancy)
        name = f"{comp}-vault"
        if not self.confirm(f"Create the free virtual vault '{name}' in compartment {comp}? It takes a few minutes"):
            raise VashError("No vault for VASH's secrets", "Run again and choose an existing vault")
        self.echo(f"Creating vault {name} (CD3 vault module) ...")
        vault_id, endpoint = self.build.vault(name, comp_id)
        self.echo(f"Vault {name} created")
        return Vault(0, name, "DEFAULT", comp, comp_id, vault_id, endpoint)

    def create_key(self, vault: Vault, name: str) -> str:
        if not self.confirm(f"Create the key '{name}' (AES-256, kept in the vault's HSM) in vault {vault.name}?"):
            raise VashError("No key for VASH's secrets", "Run again and choose an existing key")
        self.echo(f"Creating key {name} (CD3 key module) ...")
        key_id = self.build.key(name, vault.compartment_id, vault.endpoint)
        self.echo(f"Key {name} created")
        return key_id
