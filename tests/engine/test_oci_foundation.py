"""Compartments, vaults and keys through the CD3 modules: one tfvars entry per create, removed again on failure."""
import json
import subprocess
from pathlib import Path

import pytest

from vash.adapters.cloud.oci import adapter as tf_module
from vash.adapters.cloud.oci.foundation import Foundation
from vash.core.exceptions import VashError

PROVIDER = {"region": "me-jeddah-1", "tenancy_ocid": "ocid1.tenancy..t", "oci_auth": "InstancePrincipal"}


class FakeTerraform:
    def __init__(self, failures=()):
        self.failures = list(failures)  # stderr of the next failing applies
        self.calls = []

    def __call__(self, cmd, cwd=None, **kwargs):
        self.calls.append(cmd[1])
        values = json.loads((Path(cwd) / "terraform.tfvars.json").read_text())
        if cmd[1] == "apply" and self.failures:
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr=self.failures.pop(0))
        if cmd[1] == "output":
            out = {"compartment_ids": {"value": {n: f"ocid1.comp..{n}" for n in values["compartments"]}},
                   "vaults": {"value": {n: {"id": f"ocid1.vault..{n}", "management_endpoint": f"https://{n}"}
                                        for n in values["vaults"]}},
                   "key_ids": {"value": {n: f"ocid1.key..{n}" for n in values["keys"]}}}
            return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(out), stderr="")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")


def foundation(tmp_path, monkeypatch, tf):
    (tmp_path / "environments" / "foundation").mkdir(parents=True)
    monkeypatch.setattr(tf_module.subprocess, "run", tf)
    return Foundation(tmp_path, PROVIDER, lambda m: None, lambda s: None)


def tfvars(tmp_path):
    return json.loads((tmp_path / "environments" / "foundation" / "terraform.tfvars.json").read_text())


def test_entries_add_up_and_ids_come_from_the_outputs(tmp_path, monkeypatch):
    build = foundation(tmp_path, monkeypatch, FakeTerraform())
    assert build.compartment("security", "vaults") == "ocid1.comp..security"
    assert build.vault("security-vault", "ocid1.comp..security") == ("ocid1.vault..security-vault",
                                                                     "https://security-vault")
    assert build.key("vash-secrets-key", "ocid1.comp..security", "https://security-vault") == \
        "ocid1.key..vash-secrets-key"
    values = tfvars(tmp_path)
    assert values["compartments"] == {"security": "vaults"}
    assert values["vaults"] == {"security-vault": {"compartment_id": "ocid1.comp..security"}}
    assert values["keys"]["vash-secrets-key"]["management_endpoint"] == "https://security-vault"
    assert values["region"] == "me-jeddah-1" and values["oci_auth"] == "InstancePrincipal"


def test_a_failed_create_is_taken_out_again_and_the_limit_is_explained(tmp_path, monkeypatch):
    build = foundation(tmp_path, monkeypatch, FakeTerraform(["Error: 400-LimitExceeded, The limit for this "
                                                             "tenancy has been exceeded."]))
    with pytest.raises(VashError) as err:
        build.vault("security-vault", "ocid1.comp..security")
    assert "tenancy limit is reached" in str(err.value) and "pick an existing vault" in err.value.fix
    assert tfvars(tmp_path)["vaults"] == {}


def test_not_found_right_after_a_create_is_tried_once_more(tmp_path, monkeypatch):
    tf = FakeTerraform(["Error: 404-NotAuthorizedOrNotFound, Authorization failed or requested resource not found"])
    build = foundation(tmp_path, monkeypatch, tf)
    assert build.compartment("vash", "VASH runner") == "ocid1.comp..vash"
    assert tf.calls.count("apply") == 2


def test_cd3_modules_are_pinned():
    main = (Path(__file__).parents[2] / "iac/oci/environments/foundation/main.tf").read_text()
    for module in ("identity/iam-compartment", "security/vault", "security/key"):
        assert f"modules/{module}?ref=v2026.2.2" in main
    assert "enable_delete           = false" in main and 'vault_type     = "DEFAULT"' in main


def test_cd3_instance_module_gets_the_values_its_defaults_break_on():
    main = (Path(__file__).parents[2] / "iac/oci/environments/always-free/main.tf").read_text()
    instance = main[main.index('module "instance"'):]
    instance = instance[:instance.index("\n}\n")]
    assert "plugins_details = []" in instance  # CD3 iterates over it; its default is null
    assert "boot_tf_policy  = null" in instance  # CD3's default "" looks up a policy named ""
    assert "launch_options  = null" in instance  # CD3 reads element(launch_options, 0) of its default []
    assert "nsg_ids         = null" in instance  # CD3 turns its default [] into ["INVALID NSG Name"]
