"""`vash onboard oci` through OCI Resource Manager: every question first, then one job that runs in OCI."""
import json
import zipfile
from pathlib import Path

import pytest

from vash.adapters.cloud.oci import adapter as tf_module
from vash.adapters.cloud.oci.orm import stack_variables

from .test_onboard_oci import FakeCloud, done, make


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    (tmp_path / "home").mkdir()
    return tmp_path / "home"


class StackCloud(FakeCloud):
    """FakeCloud plus vault listing and Resource Manager."""

    def __init__(self, jobs=("SUCCEEDED",), logs=("Apply complete!",), vaults=(), secrets=(), dbs=(), **kw):
        super().__init__(**kw)
        self.secrets = list(secrets)
        self.vm = None  # the VM as OCI reports it (compute instance get)
        self.saved_secrets = []
        self.dbs = list(dbs)
        self.jobs = list(jobs)
        self.logs = list(logs)
        self.vaults = list(vaults)
        self.stacks = []  # (action, variables) of each stack create/update
        self.zip_names = []

    def __call__(self, args, **kwargs):
        if args[:3] == ["oci", "resource-manager", "job"] and args[3] == "get-job-tf-state":
            Path(args[args.index("--file") + 1]).write_text(json.dumps({"outputs": {
                "runner_ip": {"value": "203.0.113.9"}, "instance_id": {"value": "ocid1.instance..i"},
                "db_password_secret": {"value": "vash-db-admin-password"}}}))
            self.calls.append((args, kwargs))
            return done("")
        return super().__call__(args, **kwargs)

    def oci(self, args):
        if args[:3] == ["iam", "compartment", "list"]:
            return {"data": [{"id": c, "name": "found"} for c in self.compartments]}
        if args[:3] == ["kms", "management", "vault"]:
            return {"data": self.vaults}
        if args[:3] == ["kms", "management", "key"]:
            return {"data": []}
        if args[:3] == ["compute", "instance", "get"]:
            return {"data": self.vm} if self.vm else {"data": {}}
        if args[:3] == ["vault", "secret", "create-base64"] or args[:3] == ["vault", "secret", "update-base64"]:
            self.saved_secrets.append(json.loads(Path(args[args.index("--from-json") + 1][7:]).read_text()))
            return {"data": {}}
        if args[:3] == ["vault", "secret", "list"]:
            name = args[args.index("--name") + 1]
            return {"data": [x for x in self.secrets if x["secret-name"] == name]}
        if args[:3] == ["db", "autonomous-database", "list"]:
            return {"data": self.dbs}
        if args[:2] == ["resource-manager", "stack"] and args[2] in ("create", "update"):
            variables = args[args.index("--variables") + 1].removeprefix("file://")
            source = args[args.index("--config-source") + 1]
            self.zip_names = zipfile.ZipFile(source).namelist()
            self.stacks.append((args[2], json.loads(Path(variables).read_text())))
            return {"data": {"id": "ocid1.ormstack..s"}}
        if args[:3] == ["resource-manager", "job", "create-apply-job"]:
            return {"data": {"id": f"ocid1.ormjob..{len(self.stacks)}"}}
        if args[:3] == ["resource-manager", "job", "create-destroy-job"]:
            return {"data": {"id": "ocid1.ormjob..destroy"}}
        if args[:3] == ["resource-manager", "job", "get"]:
            state = self.jobs.pop(0) if len(self.jobs) > 1 else self.jobs[0]
            return {"data": {"lifecycle-state": state, "time-created": "now"}}
        if args[:3] == ["resource-manager", "job", "get-job-logs"]:
            return {"data": [{"message": m} for m in self.logs]}
        return super().oci(args)


def stack_make(cloud, home, **opts):
    opts.setdefault("engine", "stack")
    return make(cloud, home, **opts)


def no_local_terraform(cmd, **kwargs):
    raise AssertionError(f"terraform must not run in this shell: {cmd}")


def rm_calls(cloud):
    return [c[0][1:4] for c in cloud.calls if c[0][:2] == ["oci", "resource-manager"]]


def test_empty_tenancy_one_job_with_everything(home, monkeypatch):
    monkeypatch.setattr(tf_module.subprocess, "run", no_local_terraform)
    cloud = StackCloud()
    assert stack_make(cloud, home, database=True).up() == 0
    action, v = cloud.stacks[0]
    assert action == "create"
    comps = json.loads(v["compartments"])
    assert {k: (c["name"], c["id"]) for k, c in comps.items()} == {
        "app": ("vash", ""), "security": ("security", ""), "network": ("network", "")}  # all three made, at the root
    assert v["vault_id"] == "" and v["key_id"] == "" and v["create_database"] == "true" and v["create_vm"] == "true"
    assert v["shape"] == "VM.Standard.A1.Flex" and v["availability_domain"] == "AD-1"
    assert v["tenancy_ocid"] == "ocid1.tenancy.oc1..t" and v["region"] == "eu-frankfurt-1"  # not filled by OCI
    assert "environments/vash-stack/main.tf" in cloud.zip_names
    assert "environments/vash-stack/scripts/vash-runner.sh" in cloud.zip_names
    assert "modules/database/main.tf" in cloud.zip_names
    assert ["resource-manager", "job", "create-apply-job"] in rm_calls(cloud)
    state = json.loads((home / ".vash/oci/onboard.json").read_text())["stack"]
    assert state["id"] == "ocid1.ormstack..s" and state["outputs"]["runner_ip"] == "203.0.113.9"
    assert not list((home / ".vash/oci").glob("stack-state.json"))  # the state (with the password) is not kept


def test_nothing_is_started_before_the_one_yes(home, monkeypatch):
    monkeypatch.setattr(tf_module.subprocess, "run", no_local_terraform)
    cloud = StackCloud()
    ob = stack_make(cloud, home)
    ob.confirm = lambda q: not q.startswith("Start this setup")
    assert ob.up() == 1
    assert rm_calls(cloud) == []


def test_existing_vault_and_compartments_are_referenced(home, monkeypatch):
    monkeypatch.setattr(tf_module.subprocess, "run", no_local_terraform)
    cloud = StackCloud(compartments=["ocid1.compartment..found"], vaults=[{
        "lifecycle-state": "ACTIVE", "display-name": "security-vault", "vault-type": "DEFAULT", "id": "ocid1.vault..v",
        "management-endpoint": "https://v"}])
    ob = stack_make(cloud, home)
    ob.ask = lambda q, d: "1" if "S.No" in q else d
    ob.up()
    _, v = cloud.stacks[0]
    assert v["vault_id"] == "ocid1.vault..v" and v["vault_endpoint"] == "https://v"
    assert all(c["id"] for c in json.loads(v["compartments"]).values())


def test_database_only_makes_no_vm(home, monkeypatch):
    monkeypatch.setattr(tf_module.subprocess, "run", no_local_terraform)
    cloud = StackCloud()
    stack_make(cloud, home, database=True, database_only=True).up()
    _, v = cloud.stacks[0]
    assert v["create_vm"] == "false" and v["create_database"] == "true" and "image_id" not in v


def test_status_shows_a_running_job(home, monkeypatch):
    monkeypatch.setattr(tf_module.subprocess, "run", no_local_terraform)
    cloud = StackCloud(jobs=("IN_PROGRESS",), logs=("module.vcn: Creating...",))
    ob = stack_make(cloud, home)
    ob.confirm = lambda q: not q.startswith("Watch")
    ob.up()
    seen = []
    ob = stack_make(cloud, home, status=True)
    ob.echo = seen.append
    assert ob.up() == 0
    assert any("IN_PROGRESS" in s for s in seen) and any("module.vcn" in s for s in seen)


def test_resume_after_no_capacity_tries_the_next_domain_then_the_amd_micro(home, monkeypatch):
    monkeypatch.setattr(tf_module.subprocess, "run", no_local_terraform)
    cloud = StackCloud(quota={"AD-1": (4, 24), "AD-2": (4, 24)}, micro=1, jobs=("FAILED",),
                       logs=("Error: 500-InternalError, Out of host capacity.",))
    stack_make(cloud, home).up()
    stack_make(cloud, home, resume=True).up()
    assert cloud.stacks[-1][1]["availability_domain"] == "AD-2"
    stack_make(cloud, home, resume=True).up()
    assert cloud.stacks[-1][1]["shape"] == "VM.Standard.E2.1.Micro"
    assert [a for a, _ in cloud.stacks] == ["create", "update", "update"]


def test_down_starts_a_destroy_job(home, monkeypatch):
    monkeypatch.setattr(tf_module.subprocess, "run", no_local_terraform)
    cloud = StackCloud()
    stack_make(cloud, home).up()
    assert stack_make(cloud, home).down() == 0
    assert ["resource-manager", "job", "create-destroy-job"] in rm_calls(cloud)


def test_stack_variables_are_text():
    assert stack_variables({"a": True, "b": 2, "c": {"x": 1}, "d": ["s"], "e": None, "f": "t"}) == {
        "a": "true", "b": "2", "c": '{"x": 1}', "d": '["s"]', "f": "t"}


def test_resume_sets_tenancy_and_region_on_a_stack_saved_without_them(home, monkeypatch):
    """Seen live: the first stack had no tenancy_ocid or region; --resume must save them."""
    monkeypatch.setattr(tf_module.subprocess, "run", no_local_terraform)
    cloud = StackCloud(jobs=("FAILED",), logs=("Error: No value for required variable",))
    stack_make(cloud, home).up()
    path = home / ".vash/oci/onboard.json"
    state = json.loads(path.read_text())
    state["stack"]["values"].pop("tenancy_ocid", None)
    path.write_text(json.dumps(state))
    stack_make(cloud, home, resume=True).up()
    _, v = cloud.stacks[-1]
    assert v["tenancy_ocid"] == "ocid1.tenancy.oc1..t" and v["region"] == "eu-frankfurt-1"


VAULT = [{"lifecycle-state": "ACTIVE", "display-name": "security-vault", "vault-type": "DEFAULT", "id": "ocid1.vault..v",
          "management-endpoint": "https://v"}]


def _existing(cloud, home, monkeypatch):
    monkeypatch.setattr(tf_module.subprocess, "run", no_local_terraform)
    ob = stack_make(cloud, home, database=True)
    ob.ask = lambda q, d: "1" if "S.No" in q else d
    ob.up()
    return cloud.stacks[-1][1]


def test_existing_password_secret_is_reused(home, monkeypatch):
    """Seen live in Frankfurt: '400-InvalidParameter, name already exists' for vash-db-admin-password."""
    cloud = StackCloud(compartments=["ocid1.compartment..found"], vaults=VAULT, secrets=[
        {"secret-name": "north-db-admin-password", "lifecycle-state": "ACTIVE", "id": "ocid1.vaultsecret..s"}])
    v = _existing(cloud, home, monkeypatch)
    assert v["db_secret_id"] == "ocid1.vaultsecret..s" and v["create_database"] == "true"


def test_a_secret_waiting_for_deletion_gets_a_new_name(home, monkeypatch):
    cloud = StackCloud(compartments=["ocid1.compartment..found"], vaults=VAULT, secrets=[
        {"secret-name": "north-db-admin-password", "lifecycle-state": "PENDING_DELETION", "id": "x"}])
    v = _existing(cloud, home, monkeypatch)
    assert v["db_secret_id"] == "" and v["db_secret_name"] == "north-db-admin-password-2"


def test_an_existing_database_is_kept(home, monkeypatch):
    cloud = StackCloud(compartments=["ocid1.compartment..found"], vaults=VAULT,
                       dbs=[{"lifecycle-state": "AVAILABLE", "display-name": "north-db"}])
    v = _existing(cloud, home, monkeypatch)
    assert v["create_database"] == "false"


def test_a_vm_resized_in_the_console_is_not_shrunk_by_a_later_run(home, monkeypatch):
    """Seen live: the owner resized the VM from 2/12 to 4/24 in the Console; --resume must send 4/24."""
    monkeypatch.setattr(tf_module.subprocess, "run", no_local_terraform)
    cloud = StackCloud()
    stack_make(cloud, home).up()
    assert cloud.stacks[0][1]["ocpus"] == "2"
    cloud.vm = {"lifecycle-state": "RUNNING", "shape": "VM.Standard.A1.Flex",
                "shape-config": {"ocpus": 4.0, "memory-in-gbs": 24.0}}
    stack_make(cloud, home, resume=True).up()
    v = cloud.stacks[-1][1]
    assert (v["ocpus"], v["memory_in_gbs"]) == ("4", "24")


def test_update_installs_vash_on_the_vm_again_with_nothing_done_by_hand(home, monkeypatch):
    monkeypatch.setattr(tf_module.subprocess, "run", no_local_terraform)
    cloud = StackCloud()
    stack_make(cloud, home).up()  # the VM is known: its address from the stack, its key from the state
    key = home / ".ssh" / "k"
    key.parent.mkdir(exist_ok=True)
    key.write_text("x")
    path = home / ".vash/oci/onboard.json"
    state = json.loads(path.read_text())
    state["ssh_key"] = str(key)
    path.write_text(json.dumps(state))
    assert stack_make(cloud, home, update=True, vash_source="git+https://example.org/vash.git@v9").up() == 0
    installs = [c for c in cloud.calls if c[0][0] == "ssh" and "vash-install.sh" in c[0][-1]]
    assert len(installs) == 1 and "203.0.113.9" in " ".join(installs[0][0])
    assert "rm -f /var/lib/vash/ready" in installs[0][0][-1]  # never reads the old result
    assert 'VASH_SOURCE="git+https://example.org/vash.git@v9"' in installs[0][1]["input"]


def test_status_shows_the_install_the_health_check_and_the_first_task(home, monkeypatch):
    monkeypatch.setattr(tf_module.subprocess, "run", no_local_terraform)
    cloud = StackCloud()
    stack_make(cloud, home).up()
    path = home / ".vash/oci/onboard.json"
    state = json.loads(path.read_text())
    state["ssh_key"] = str(home / "k")
    path.write_text(json.dumps(state))
    stack_make(cloud, home, status=True).up()
    reports = [c for c in cloud.calls if c[0][0] == "ssh" and "doctor.txt" in c[0][-1]]
    assert reports and "smoke.txt" in reports[-1][0][-1]


def test_the_vm_checks_itself_after_the_install():
    from vash.core.paths import vash_root
    script = (vash_root() / "iac" / "oci" / "cloud-init" / "vash-runner.sh").read_text()
    assert "vash doctor --repo" in script and "/var/lib/vash/doctor.txt" in script
    assert "vash init vash-smoke" in script and "vash ava T1" in script and "/var/lib/vash/smoke.txt" in script
    assert script.index("== vash onboard done") < script.index("vash ava T1")  # ready first, checks after


def test_keys_are_given_once_kept_in_the_vault_and_installed_on_the_vm(home, monkeypatch):
    import base64
    monkeypatch.setattr(tf_module.subprocess, "run", no_local_terraform)
    cloud = StackCloud()
    stack_make(cloud, home).up()
    path = home / ".vash/oci/onboard.json"
    state = json.loads(path.read_text())
    state["ssh_key"] = str(home / "k")
    state["stack"]["outputs"].update(vault_id="ocid1.vault..v", key_id="ocid1.key..k",
                                     compartment_ids={"security": "ocid1.compartment..sec"})
    path.write_text(json.dumps(state))
    ob = stack_make(cloud, home, keys=True)
    ob.secret = lambda q: "gsk_SECRET1" if q.startswith("groq") else ("csk_SECRET2" if q.startswith("cerebras") else "")
    assert ob.up() == 0
    names = sorted(x["secretName"] for x in cloud.saved_secrets)
    assert names == ["vash-gateway-cerebras-api-key", "vash-gateway-groq-api-key"]
    assert base64.b64decode(cloud.saved_secrets[0]["secretContentContent"]).decode().endswith("SECRET1") or \
        base64.b64decode(cloud.saved_secrets[0]["secretContentContent"]).decode().endswith("SECRET2")
    pushes = [c for c in cloud.calls if c[0][0] == "ssh" and "gateway.env" in c[0][-1]]
    assert len(pushes) == 1 and "GROQ_API_KEY=gsk_SECRET1" in pushes[0][1]["input"]
    assert all("SECRET" not in " ".join(c[0]) for c in cloud.calls)  # never on a command line
    assert "systemctl restart vash-gateway" in pushes[0][0][-1]


def test_no_key_given_changes_nothing(home, monkeypatch):
    monkeypatch.setattr(tf_module.subprocess, "run", no_local_terraform)
    cloud = StackCloud()
    stack_make(cloud, home).up()
    path = home / ".vash/oci/onboard.json"
    state = json.loads(path.read_text())
    state["ssh_key"] = str(home / "k")
    path.write_text(json.dumps(state))
    before = len(cloud.calls)
    assert stack_make(cloud, home, keys=True).up() == 0
    assert len(cloud.calls) == before


def test_chat_opens_the_harness_on_the_vm_in_this_terminal(home, monkeypatch):
    monkeypatch.setattr(tf_module.subprocess, "run", no_local_terraform)
    cloud = StackCloud()
    stack_make(cloud, home).up()
    path = home / ".vash/oci/onboard.json"
    state = json.loads(path.read_text())
    state["ssh_key"] = str(home / "k")
    path.write_text(json.dumps(state))
    stack_make(cloud, home, chat=True).up()
    chat = cloud.calls[-1]
    assert chat[0][:2] == ["ssh", "-t"] and chat[0][-1] == "vash-chat" and "capture_output" not in chat[1]


def test_gpu_token_is_given_once_kept_in_the_vault_and_put_in_the_vm_users_home(home, monkeypatch):
    monkeypatch.setattr(tf_module.subprocess, "run", no_local_terraform)
    cloud = StackCloud()
    stack_make(cloud, home).up()
    path = home / ".vash/oci/onboard.json"
    state = json.loads(path.read_text())
    state["ssh_key"] = str(home / "k")
    state["stack"]["outputs"].update(vault_id="ocid1.vault..v", key_id="ocid1.key..k",
                                     compartment_ids={"security": "ocid1.compartment..sec"})
    path.write_text(json.dumps(state))
    ob = stack_make(cloud, home, keys=True)
    ob.secret = lambda q: "KGAT_TOKEN123" if q.startswith("Kaggle") else ""
    assert ob.up() == 0
    assert [x["secretName"] for x in cloud.saved_secrets] == ["vash-gpu-kaggle-access-token"]
    pushes = [c for c in cloud.calls if c[0][0] == "ssh" and "access_token" in c[0][-1]]
    assert len(pushes) == 1 and pushes[0][1]["input"] == "KGAT_TOKEN123" and "umask 077" in pushes[0][0][-1]
    assert all("KGAT_TOKEN123" not in " ".join(c[0]) for c in cloud.calls)
    assert not [c for c in cloud.calls if c[0][0] == "ssh" and "gateway.env" in c[0][-1]]  # no model key given
