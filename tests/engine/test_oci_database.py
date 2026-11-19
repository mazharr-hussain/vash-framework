"""--database / --database-only (Always Free Autonomous Database, password in the vault) and the network compartment."""
import base64
import json
from pathlib import Path

import pytest

from vash.adapters.cloud.oci import adapter as tf_module
from vash.adapters.cloud.oci.database import DatabaseSetup, generate_password
from vash.core.exceptions import VashError

from .test_onboard_oci import COMPARTMENT, FakeCloud, FakeTerraform, done, make



@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    (tmp_path / "home").mkdir()
    return tmp_path / "home"


VAULT = {"vault_id": "ocid1.vault..v", "key_id": "ocid1.key..k", "vault_compartment_id": "ocid1.compartment..sec"}


def test_generated_passwords_meet_the_database_rules():
    for _ in range(200):
        p = generate_password()
        assert 12 <= len(p) <= 30 and p[0].isalpha() and '"' not in p and "admin" not in p.lower()
        assert any(c.isupper() for c in p) and any(c.islower() for c in p) and sum(c.isdigit() for c in p) >= 2
    assert len({generate_password() for _ in range(20)}) == 20


class SecretCloud(FakeCloud):
    def __init__(self, existing: str | None = None, **kw):
        super().__init__(**kw)
        self.existing = existing
        self.stored = None

    def __call__(self, args, **kwargs):
        if args[:4] == ["oci", "vault", "secret", "create-base64"]:
            path = args[args.index("--from-json") + 1].removeprefix("file://")
            self.stored = json.loads(Path(path).read_text())
            self.calls.append((args, kwargs))
            return done("{}")
        return super().__call__(args, **kwargs)

    def oci(self, args):
        if args[:3] == ["vault", "secret", "list"]:
            return {"data": [{"id": "ocid1.secret..s", "lifecycle-state": "ACTIVE"}] if self.existing else []}
        if args[:3] == ["secrets", "secret-bundle", "get"]:
            return {"data": {"secret-bundle-content": {"content": base64.b64encode(self.existing.encode()).decode()}}}
        return super().oci(args)


class DbTerraform(FakeTerraform):
    def __init__(self):
        super().__init__()
        self.envs = []

    def __call__(self, cmd, cwd=None, **kwargs):
        if Path(cwd).name == "foundation":
            self.envs.append(kwargs.get("env") or {})
            if cmd[1] == "output":
                values = json.loads((Path(cwd) / "terraform.tfvars.json").read_text())
                return done(json.dumps({
                    "compartment_ids": {"value": {n: COMPARTMENT for n in values["compartments"]}},
                    "databases": {"value": {n: {"id": "ocid1.autonomousdatabase..d", "db_name": f"{n}db"}
                                            for n in values["databases"]}}}))
        return super().__call__(cmd, cwd=cwd, **kwargs)


def _onboard(home, cloud, **opts):
    onboarding = make(cloud, home, **opts)
    (home / ".vash/oci").mkdir(parents=True, exist_ok=True)
    (home / ".vash/oci/onboard.json").write_text(json.dumps(VAULT))  # the vault chosen at an earlier run
    return onboarding


def test_database_only_makes_the_database_and_keeps_the_password_out_of_files_and_commands(home, monkeypatch):
    cloud, tf = SecretCloud(compartments=[COMPARTMENT]), DbTerraform()
    monkeypatch.setattr(tf_module.subprocess, "run", tf)
    assert _onboard(home, cloud, database=True, database_only=True).up() == 0
    assert tf.calls == []  # no VM terraform at all
    stored = cloud.stored
    password = base64.b64decode(stored["secretContentContent"]).decode()
    assert stored["secretName"] == "north-db-admin-password" and stored["vaultId"] == VAULT["vault_id"]
    assert stored["keyId"] == VAULT["key_id"] and stored["compartmentId"] == VAULT["vault_compartment_id"]
    tfvars = (home / ".vash/oci/environments/foundation/terraform.tfvars.json").read_text()
    assert json.loads(tfvars)["databases"] == {"north": {"compartment_id": COMPARTMENT}}
    assert password not in tfvars
    assert any(e.get("TF_VAR_db_admin_passwords") == json.dumps({"north": password}) for e in tf.envs)
    assert all(password not in " ".join(c[0]) for c in cloud.calls)
    state = json.loads((home / ".vash/oci/onboard.json").read_text())
    assert state["database"] == {"id": "ocid1.autonomousdatabase..d", "db_name": "northdb",
                                 "vault_entry": "north-db-admin-password"}  # pragma: allowlist secret (a test value)


def test_secret_request_file_is_removed(home, monkeypatch, tmp_path):
    monkeypatch.setattr("tempfile.tempdir", str(tmp_path))
    cloud, tf = SecretCloud(compartments=[COMPARTMENT]), DbTerraform()
    monkeypatch.setattr(tf_module.subprocess, "run", tf)
    _onboard(home, cloud, database=True, database_only=True).up()
    assert cloud.stored and not list(tmp_path.glob("vash-secret-*"))


def test_existing_secret_is_reused_and_a_second_run_creates_nothing(home, monkeypatch):
    cloud, tf = SecretCloud(existing="Kept-Password-42", compartments=[COMPARTMENT]), DbTerraform()
    monkeypatch.setattr(tf_module.subprocess, "run", tf)
    onboarding = _onboard(home, cloud, database=True, database_only=True)
    onboarding.up()
    assert cloud.stored is None  # nothing new stored
    assert any(e.get("TF_VAR_db_admin_passwords") == json.dumps({"north": "Kept-Password-42"}) for e in tf.envs)
    runs = len(tf.envs)
    onboarding.up()
    assert len(tf.envs) == runs  # already made: no terraform


def test_database_needs_the_vault(home, monkeypatch):
    monkeypatch.setattr(tf_module.subprocess, "run", DbTerraform())
    with pytest.raises(VashError, match="No vault"):
        make(SecretCloud(compartments=[COMPARTMENT]), home, database=True, database_only=True).up()


def test_declined_database_creates_nothing(home, monkeypatch):
    cloud, tf = SecretCloud(compartments=[COMPARTMENT]), DbTerraform()
    monkeypatch.setattr(tf_module.subprocess, "run", tf)
    onboarding = _onboard(home, cloud, database=True, database_only=True)
    onboarding.confirm = lambda q: "Autonomous Database" not in q
    with pytest.raises(VashError, match="No database"):
        onboarding.up()
    assert cloud.stored is None and tf.envs == []


def test_new_network_goes_to_the_network_compartment(home, monkeypatch):
    monkeypatch.setattr(tf_module.subprocess, "run", DbTerraform())
    assert make(FakeCloud(), home).up() == 0
    tfvars = json.loads((home / ".vash/oci/environments/always-free/terraform.tfvars.json").read_text())
    assert tfvars["network_compartment_id"] == COMPARTMENT
    created = json.loads((home / ".vash/oci/environments/foundation/terraform.tfvars.json").read_text())
    assert "network" in created["compartments"]


def test_named_network_compartment_and_existing_subnet(home, monkeypatch):
    monkeypatch.setattr(tf_module.subprocess, "run", DbTerraform())
    make(FakeCloud(), home, network_compartment="nets").up()
    created = json.loads((home / ".vash/oci/environments/foundation/terraform.tfvars.json").read_text())
    assert "nets" in created["compartments"] and "network" not in created["compartments"]


def test_earlier_network_is_not_moved(home, monkeypatch):
    monkeypatch.setattr(tf_module.subprocess, "run", DbTerraform())
    make(FakeCloud(), home).up()
    path = home / ".vash/oci/environments/always-free/terraform.tfvars.json"
    old = json.loads(path.read_text())
    del old["network_compartment_id"]  # an onboarding from before network compartments
    path.write_text(json.dumps(old))
    make(FakeCloud(), home).up()
    assert json.loads(path.read_text())["network_compartment_id"] == ""


def test_setup_refuses_without_key():
    setup = DatabaseSetup(lambda *a: {}, lambda _m: None, lambda _q: True, build=None)
    with pytest.raises(VashError, match="No vault"):
        setup.create("north", COMPARTMENT, "vash", {"vault_id": "v"})
