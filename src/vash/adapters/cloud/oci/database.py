"""An Always Free Autonomous Database for a project, with its admin password kept in the VASH vault.

The password is generated here, stored first as a secret in the vault the owner chose (OCI Vault, free), and then
given to terraform through the environment only (foundation.py): it is never printed, never written to a
tfvars file and never put on a command line. The CD3 toolkit has no module for vault secrets, so the secret is
created with the oci CLI (catalog/search-log.md). A secret that already exists (an earlier run that stopped) is
read back and reused, so a rerun creates the same database with the same password.
The database has no private endpoint (Always Free does not offer one): clients need the wallet (mutual TLS).
"""
from __future__ import annotations

import base64
import json
import os
import secrets
import string
import tempfile
from typing import Any, Callable

from vash.core.exceptions import VashError

from .foundation import Foundation

SPECIALS = "#_-"
LENGTH = 24


def generate_password(length: int = LENGTH) -> str:
    """An admin password that meets Autonomous Database's rules: 12 to 30 characters, at least one upper-case
    letter, one lower-case letter and one digit, no double quote and not the word 'admin'."""
    alphabet = string.ascii_letters + string.digits + SPECIALS
    while True:
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        if (any(c.isupper() for c in password) and any(c.islower() for c in password)
                and sum(c.isdigit() for c in password) >= 2 and any(c in SPECIALS for c in password)
                and password[0].isalpha() and "admin" not in password.lower()):
            return password


def vault_entry(prefix: str) -> str:
    """Name of the vault secret that holds the admin password of `<prefix>-db` (a name, not the password)."""
    return f"{prefix}-db-admin-password"


class DatabaseSetup:
    def __init__(self, oci: Callable[..., Any], echo: Callable[[str], None], confirm: Callable[[str], bool],
                 build: Foundation):
        self.oci, self.echo, self.confirm, self.build = oci, echo, confirm, build

    def existing_password(self, vault: dict[str, str], name: str) -> str | None:
        found = self.oci("vault", "secret", "list", "--compartment-id", vault["vault_compartment_id"],
                         "--vault-id", vault["vault_id"], "--name", name, "--all").get("data", [])
        active = [s for s in found or [] if s.get("lifecycle-state") == "ACTIVE"]
        if not active:
            return None
        bundle = self.oci("secrets", "secret-bundle", "get", "--secret-id", active[0]["id"]).get("data", {})
        content = (bundle.get("secret-bundle-content") or {}).get("content") or ""
        return base64.b64decode(content).decode() if content else None

    def store_password(self, vault: dict[str, str], name: str, password: str) -> None:
        """Create the secret; the request is read from a private temporary file, so the password is not on the
        command line (where other processes could read it)."""
        request = {"compartmentId": vault["vault_compartment_id"], "vaultId": vault["vault_id"],
                   "keyId": vault["key_id"], "secretName": name,
                   "description": "Admin password of a VASH Autonomous Database (created by vash onboard)",
                   "secretContentContent": base64.b64encode(password.encode()).decode()}
        fd, path = tempfile.mkstemp(prefix="vash-secret-", suffix=".json")
        try:
            with os.fdopen(fd, "w") as handle:  # mkstemp creates the file readable by its owner only
                json.dump(request, handle)
            self.oci("vault", "secret", "create-base64", "--from-json", f"file://{path}")
        finally:
            os.remove(path)

    def create(self, prefix: str, compartment_id: str, compartment_name: str, vault: dict[str, str]) -> dict[str, str]:
        """{id, db_name, vault_entry}: the database `<prefix>-db` and the name of the vault secret with its password."""
        if not (vault.get("vault_id") and vault.get("key_id")):
            raise VashError("No vault for the database password",
                            "Run onboarding without --no-vault, so VASH can keep the password in a vault")
        name = vault_entry(prefix)
        if not self.confirm(f"Create the Always Free Autonomous Database '{prefix}-db' (1 OCPU, 20 GB, $0) in "
                            f"compartment {compartment_name}? Its admin password is generated and kept only in "
                            f"the vault secret '{name}'; clients connect with the wallet (mutual TLS)"):
            raise VashError("No database created", "Run again and answer yes, or leave out --database")
        password = self.existing_password(vault, name)
        if password:
            self.echo(f"Vault secret '{name}' exists (an earlier run); its password is used")
        else:
            password = generate_password()
            self.store_password(vault, name, password)
            self.echo(f"Admin password generated and stored in vault secret '{name}'")
        self.echo(f"Creating database {prefix}-db (VASH database module; takes a few minutes) ...")
        made = self.build.database(prefix, compartment_id, password)
        self.echo(f"Database {prefix}-db created")
        return {"id": made.get("id", ""), "db_name": made.get("db_name", ""), "vault_entry": name}
