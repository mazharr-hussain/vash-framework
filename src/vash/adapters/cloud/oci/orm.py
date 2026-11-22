"""OCI Resource Manager: VASH's whole setup as one stack, run inside OCI.

Resource Manager (free) runs terraform in OCI itself, so the setup keeps going when Cloud Shell, the browser or
the laptop is closed, and the job and its log stay visible in the Console (Developer Services, Resource Manager,
Jobs). The stack is iac/oci/environments/vash-stack: one terraform graph, so terraform builds at the same time
everything that does not wait for something else. Every call goes through the oci CLI with an argument list.
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any, Callable

STACK_DIR = "environments/vash-stack"
TERRAFORM_VERSION = "1.5.x"
DONE = ("SUCCEEDED", "FAILED", "CANCELED")


def stack_variables(values: dict[str, Any]) -> dict[str, str]:
    """Resource Manager keeps stack variables as text: lists and maps as JSON (terraform reads JSON as HCL)."""
    out = {}
    for key, value in values.items():
        if value is None:
            continue
        if isinstance(value, bool):
            out[key] = "true" if value else "false"
        elif isinstance(value, (dict, list)):
            out[key] = json.dumps(value)
        else:
            out[key] = str(value)
    return out


def package(iac_root: Path, cloud_init: str, target: Path) -> Path:
    """The stack's zip: the vash-stack environment (with its first-boot script) and VASH's own modules; CD3's
    modules are fetched by terraform from their pinned release."""
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        stack = iac_root / STACK_DIR
        for name in ("main.tf", "variables.tf", "outputs.tf"):
            zf.write(stack / name, f"{STACK_DIR}/{name}")
        zf.writestr(f"{STACK_DIR}/scripts/vash-runner.sh", cloud_init)
        for path in sorted((iac_root / "modules").rglob("*.tf")):
            zf.write(path, str(path.relative_to(iac_root)))
    return target


class ResourceManager:
    def __init__(self, oci: Callable[..., Any], workdir: Path, echo: Callable[[str], None]):
        self.oci, self.workdir, self.echo = oci, workdir, echo

    def _variables_file(self, values: dict[str, Any]) -> str:
        path = self.workdir / "stack-variables.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(stack_variables(values), indent=2) + "\n")
        path.chmod(0o600)
        return f"file://{path}"

    def save_stack(self, stack_id: str, tenancy: str, name: str, zip_path: Path, values: dict[str, Any]) -> str:
        """Create the stack (in the root compartment, which always exists) or update it; returns its id."""
        common = ["--config-source", str(zip_path), "--working-directory", STACK_DIR,
                  "--variables", self._variables_file(values)]
        if stack_id:
            self.oci("resource-manager", "stack", "update", "--stack-id", stack_id, *common,
                     "--terraform-version", TERRAFORM_VERSION, "--force")
            return stack_id
        made = self.oci("resource-manager", "stack", "create", "--compartment-id", tenancy, *common,
                        "--display-name", name, "--terraform-version", TERRAFORM_VERSION,
                        "--description", "VASH: compartments, vault, network, VM and database (vash onboard oci)")
        return made.get("data", {}).get("id", "")

    def apply(self, stack_id: str) -> str:
        job = self.oci("resource-manager", "job", "create-apply-job", "--stack-id", stack_id,
                       "--execution-plan-strategy", "AUTO_APPROVED", "--display-name", "vash-setup")
        return job.get("data", {}).get("id", "")

    def destroy(self, stack_id: str) -> str:
        job = self.oci("resource-manager", "job", "create-destroy-job", "--stack-id", stack_id,
                       "--execution-plan-strategy", "AUTO_APPROVED", "--display-name", "vash-remove")
        return job.get("data", {}).get("id", "")

    def job(self, job_id: str) -> dict[str, Any]:
        return self.oci("resource-manager", "job", "get", "--job-id", job_id).get("data", {})

    def logs(self, job_id: str) -> list[str]:
        data = self.oci("resource-manager", "job", "get-job-logs", "--job-id", job_id, "--all").get("data", [])
        return [line.get("message", "") for line in data or [] if line.get("message")]

    def outputs(self, job_id: str) -> dict[str, Any]:
        """The stack's outputs, from the state the job left (name => value)."""
        path = self.workdir / "stack-state.json"
        self.oci("resource-manager", "job", "get-job-tf-state", "--job-id", job_id, "--file", str(path))
        try:
            state = json.loads(path.read_text()) if path.exists() else {}
        finally:
            path.unlink(missing_ok=True)  # it holds the database password; only Resource Manager keeps it
        return {k: v.get("value") for k, v in state.get("outputs", {}).items()}
