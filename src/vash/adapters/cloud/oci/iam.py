"""IAM helpers shared by onboarding steps."""
from __future__ import annotations

import time
from typing import Any, Callable

from vash.core.exceptions import VashError

COMPARTMENT_POLLS = 24  # 2 minutes at 5 s


def create_compartment(oci: Callable[..., Any], echo: Callable[[str], None], tenancy: str, name: str,
                       description: str, sleep: Callable[[float], None] = time.sleep) -> str:
    """Create a compartment and wait until it can be read.

    IAM is eventually consistent: right after a create, reading the new compartment can answer
    404 NotAuthorizedOrNotFound for a while (seen in Cloud Shell), which made the CLI's own
    --wait-for-state fail although the compartment was created. VASH polls instead.
    """
    data = oci("iam", "compartment", "create", "--compartment-id", tenancy, "--name", name,
               "--description", description).get("data", {})
    comp_id = data.get("id") or ""
    if not comp_id:
        raise VashError(f"Compartment '{name}' was not created", "Check the OCI policy and run again")
    for _ in range(COMPARTMENT_POLLS):
        try:
            state = oci("iam", "compartment", "get", "--compartment-id", comp_id).get("data", {}).get("lifecycle-state")
        except VashError as exc:
            if "NotAuthorizedOrNotFound" not in str(exc):
                raise
            state = ""  # not visible yet
        if state == "ACTIVE":
            return comp_id
        sleep(5)
    echo(f"Compartment '{name}' was created; OCI is still making it visible, continuing")
    return comp_id
