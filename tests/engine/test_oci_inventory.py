import pytest

from vash.adapters.cloud.oci.inventory import Inventory, review
from vash.core.exceptions import VashError

TEN = "ocid1.tenancy..t"


class FakeOci:
    def __init__(self, in_use=()):
        self.calls = []
        self.in_use = set(in_use)
        self.vcns = {
            "ocid1.vcn..a": {"name": "PoC_VCN", "comp": "ocid1.comp..x",
                              "subnets": [("ocid1.subnet..pub", "public subnet", False),
                                          ("ocid1.subnet..priv", "private subnet", True)]},
            "ocid1.vcn..b": {"name": "Old_VCN", "comp": "ocid1.comp..x",
                              "subnets": [("ocid1.subnet..old", "old subnet", False)]},
        }

    def __call__(self, *args):
        self.calls.append(args)
        a = list(args)
        if a[:3] == ["iam", "compartment", "list"] and a[a.index("--compartment-id") + 1] != TEN:
            return {"data": []}
        if a[:3] == ["network", "vcn", "list"]:
            comp = a[a.index("--compartment-id") + 1]
            return {"data": [{"id": k, "display-name": v["name"], "lifecycle-state": "AVAILABLE"}
                             for k, v in self.vcns.items() if v["comp"] == comp]}
        if a[:3] == ["compute", "instance", "list"]:
            comp = a[a.index("--compartment-id") + 1]
            if comp != "ocid1.comp..x" or getattr(self, "terminated", None):
                return {"data": []}
            return {"data": [{"id": "ocid1.instance..vm", "display-name": "kyc-vm", "lifecycle-state": "RUNNING"}]}
        if a[:3] == ["iam", "compartment", "list"]:
            return {"data": [{"id": "ocid1.comp..x", "name": "PoC", "lifecycle-state": "ACTIVE",
                              "compartment-id": TEN}]}
        if a[:3] == ["search", "resource", "structured-search"] and "instance" in a[-1]:
            return {"data": {"items": [{"identifier": "ocid1.instance..vm", "display-name": "kyc-vm",
                                        "lifecycle-state": "RUNNING", "compartment-id": "ocid1.comp..x"}]}}
        if a[:3] == ["compute", "instance", "list-vnics"]:
            return {"data": [{"id": "vnic-vm", "public-ip": "203.0.113.9"}]}
        if a[:3] == ["compute", "instance", "get"]:
            return {"data": {"compartment-id": "ocid1.comp..x", "availability-domain": "AD-1",
                             "display-name": "kyc-vm"}}
        if a[:3] == ["network", "vnic", "get"]:
            vid = a[a.index("--vnic-id") + 1]
            return {"data": {"compartment-id": "ocid1.comp..x", "time-created": "2026-11-04T01:39:02Z",
                             "display-name": f"name-of-{vid}"}}
        if a[:3] == ["compute", "vnic-attachment", "list"]:
            vid = a[a.index("--vnic-id") + 1]
            if vid == "vnic-vm":
                return {"data": [{"instance-id": "ocid1.instance..vm", "lifecycle-state": "ATTACHED"}]}
            return {"data": []}
        if a[:3] == ["search", "resource", "structured-search"] and "timeCreated" in a[-1]:
            return {"data": {"items": [
                {"resource-type": "Vnic", "display-name": "x", "time-created": "2026-11-04T01:39:02Z"},
                {"resource-type": "PrivateEndpoint", "display-name": "odoo-pe", "time-created": "2026-11-04T01:38:40Z",
                 "lifecycle-state": "ACTIVE"},
                {"resource-type": "Bucket", "display-name": "old", "time-created": "2026-10-01T00:00:00Z",
                 "lifecycle-state": "ACTIVE"}]}}
        if a[:3] == ["compute", "boot-volume-attachment", "list"]:
            return {"data": [{"boot-volume-id": "ocid1.bootvolume..b"}]}
        if a[:3] == ["compute", "volume-attachment", "list"]:
            return {"data": [{"volume-id": "ocid1.volume..data", "lifecycle-state": "ATTACHED"}]}
        if a[:3] == ["compute", "instance", "terminate"]:
            self.terminated = a[a.index("--instance-id") + 1]
            self.in_use = set()
            return {}
        if a[:3] == ["search", "resource", "structured-search"] and "compartmentId" not in a[-1]:
            return {"data": {"items": [{"identifier": k, "display-name": v["name"], "lifecycle-state": "AVAILABLE",
                                        "compartment-id": v["comp"]} for k, v in self.vcns.items()]}}
        if a[:3] == ["network", "subnet", "list"]:
            vcn = a[a.index("--vcn-id") + 1]
            return {"data": [{"id": s, "display-name": n, "lifecycle-state": "AVAILABLE",
                              "prohibit-public-ip-on-vnic": priv, "compartment-id": "ocid1.comp..x"}
                             for s, n, priv in self.vcns.get(vcn, {}).get("subnets", [])]}
        if a[:3] == ["network", "private-ip", "list"]:
            sid = a[a.index("--subnet-id") + 1]
            return {"data": [{"ip-address": "10.0.0.5", "display-name": "kyc-vm", "vnic-id": "vnic-vm"}]
                    if sid in self.in_use else []}
        if a[:3] == ["search", "resource", "structured-search"] and "compartmentId" in a[-1]:
            return {"data": {"items": [{"resource-type": "Instance", "display-name": "kyc-vm",
                                        "lifecycle-state": "RUNNING"}]}}
        if a[:3] == ["network", "subnet", "delete"]:
            sid = a[a.index("--subnet-id") + 1]
            if sid in self.in_use:
                raise VashError("oci network subnet delete failed: Conflict, subnet in use", "fix")
            for v in self.vcns.values():
                v["subnets"] = [s for s in v["subnets"] if s[0] != sid]
            return {}
        if a[:3] == ["network", "vcn", "get"]:
            return {"data": {"compartment-id": "ocid1.comp..x", "default-route-table-id": "rt-default",
                             "default-security-list-id": "sl-default", "default-dhcp-options-id": "dhcp-default"}}
        if a[:2] == ["network", "route-table"] and a[2] == "list":
            return {"data": [{"id": "rt-default"}, {"id": "rt-extra"}]}
        if a[:2] == ["network", "security-list"] and a[2] == "list":
            return {"data": [{"id": "sl-default"}, {"id": "sl-extra"}]}
        if a[:2] == ["network", "dhcp-options"] and a[2] == "list":
            return {"data": [{"id": "dhcp-default"}]}
        if a[:2] == ["network", "internet-gateway"] and a[2] == "list":
            return {"data": [{"id": "igw-1"}]}
        if a[2] == "list":
            return {"data": []}
        if a[:3] == ["network", "vcn", "delete"]:
            self.vcns.pop(a[a.index("--vcn-id") + 1])
            return {}
        return {}


def lines():
    out = []
    return out, out.append


def test_table_lists_compartments_vcns_and_subnets_with_owner():
    out, echo = lines()
    inv = Inventory(FakeOci(), echo)
    rows = inv.rows(TEN)
    assert [(r.no, r.kind) for r in rows][:3] == [(1, "Compartment"), (2, "VCN"), (3, "Subnet")]
    sub = next(r for r in rows if r.ocid == "ocid1.subnet..pub")
    assert sub.parent == "PoC_VCN" and sub.public == "yes"
    assert any(line.startswith("Reading ") for line in out)
    out.clear()
    inv.show(rows)
    assert "S.No" in out[1] and "Belongs to" in out[1]


def test_select_by_number_and_ocid():
    inv = Inventory(FakeOci(), lambda m: None)
    rows = inv.rows(TEN)
    chosen, unknown = inv.select(rows, "2, ocid1.subnet..old, 99, 2")
    assert [r.ocid for r in chosen] == ["ocid1.vcn..a", "ocid1.subnet..old"]
    assert unknown == ["99"]


def test_vcn_delete_removes_children_in_order_and_keeps_defaults():
    fake = FakeOci()
    inv = Inventory(fake, lambda m: None)
    rows = inv.rows(TEN)
    inv.delete([r for r in rows if r.ocid == "ocid1.vcn..b"])
    ops = [c[:3] for c in fake.calls if c[2] in ("delete", "update")]
    assert ops[0] == ("network", "subnet", "delete")
    assert ("network", "route-table", "update") in ops  # default table emptied, not deleted
    deleted_ids = [c[c.index(f) + 1] for c in fake.calls if c[2] == "delete"
                   for f in c if f.endswith("-id") and f.startswith("--")]
    assert "sl-default" not in deleted_ids and "sl-extra" in deleted_ids
    assert ops[-1] == ("network", "vcn", "delete")
    assert "ocid1.vcn..b" not in fake.vcns


def test_subnet_in_use_stops_with_oci_error():
    inv = Inventory(FakeOci(in_use={"ocid1.subnet..pub"}), lambda m: None)
    rows = inv.rows(TEN)
    with pytest.raises(VashError, match="in use"):
        inv.delete([r for r in rows if r.ocid == "ocid1.subnet..pub"])


def test_review_asks_twice_before_deleting():
    fake = FakeOci()
    answers = {"check": True, "delete any": True, "Delete these now": False}
    def confirm(q):
        return next(v for k, v in answers.items() if k in q)
    inv = Inventory(fake, lambda m: None)
    review(inv, TEN, confirm, lambda q, d: "3" if "delete" in q else "", want_subnet=True)
    assert not any(c[2] == "delete" for c in fake.calls)


def test_review_deletes_after_final_yes_and_picks_subnet():
    fake = FakeOci()
    inv = Inventory(fake, lambda m: None)
    rows = inv.rows(TEN)
    old_vcn = next(r.no for r in rows if r.ocid == "ocid1.vcn..b")
    pub = next(r.no for r in rows if r.ocid == "ocid1.subnet..pub")
    picked = review(inv, TEN, lambda q: True,
                    lambda q, d: str(old_vcn) if "delete" in q else str(pub), want_subnet=True)
    assert "ocid1.vcn..b" not in fake.vcns
    assert picked.subnet_id == "ocid1.subnet..pub" and picked.vm is None


def test_review_no_check_does_nothing():
    fake = FakeOci()
    assert review(Inventory(fake, lambda m: None), TEN, lambda q: False, lambda q, d: "", True).subnet_id == ""
    assert fake.calls == []


def test_private_subnet_cannot_be_picked():
    fake = FakeOci()
    inv = Inventory(fake, lambda m: None)
    priv = next(r.no for r in inv.rows(TEN) if r.ocid == "ocid1.subnet..priv")
    answers = {"check": True, "delete any": False}
    picked = review(inv, TEN, lambda q: next(v for k, v in answers.items() if k in q),
                    lambda q, d: str(priv), want_subnet=True)
    assert picked.subnet_id == "" and picked.vm is None


def test_in_use_subnet_is_blocked_and_not_deleted():
    fake = FakeOci(in_use={"ocid1.subnet..pub"})
    out, echo = lines()
    inv = Inventory(fake, echo)
    no = next(r.no for r in inv.rows(TEN) if r.ocid == "ocid1.subnet..pub")
    review(inv, TEN, lambda q: True, lambda q, d: str(no) if "delete" in q else "", want_subnet=False)
    assert not any(c[2] == "delete" for c in fake.calls)
    assert any("still in use: IP 10.0.0.5: VM kyc-vm" in line for line in out)
    assert any("every choice is still in use" in line for line in out)


def test_vcn_dependencies_listed_and_in_use_child_blocks():
    fake = FakeOci(in_use={"ocid1.subnet..priv"})
    inv = Inventory(fake, lambda m: None)
    vcn = next(r for r in inv.rows(TEN) if r.ocid == "ocid1.vcn..a")
    also, blockers = inv.dependencies(vcn)
    assert "subnet public subnet" in also and "internet-gateway igw-1" in also
    assert "route-table rt-extra" in also and not any("rt-default" in a for a in also)
    assert blockers == ["subnet private subnet: IP 10.0.0.5: VM kyc-vm"]


def test_non_empty_compartment_is_blocked():
    inv = Inventory(FakeOci(), lambda m: None)
    comp = next(r for r in inv.rows(TEN) if r.kind == "Compartment")
    _, blockers = inv.dependencies(comp)
    assert blockers == ["Instance kyc-vm"]


def test_only_free_objects_are_deleted_from_a_mixed_choice():
    fake = FakeOci(in_use={"ocid1.subnet..pub"})
    inv = Inventory(fake, lambda m: None)
    rows = inv.rows(TEN)
    pub = next(r.no for r in rows if r.ocid == "ocid1.subnet..pub")
    old = next(r.no for r in rows if r.ocid == "ocid1.subnet..old")
    asked = []
    def confirm(q):
        asked.append(q)
        return True
    review(inv, TEN, confirm, lambda q, d: f"{pub},{old}" if "delete" in q else "", want_subnet=False)
    deleted = [c[c.index("--subnet-id") + 1] for c in fake.calls if c[:3] == ("network", "subnet", "delete")]
    assert deleted == ["ocid1.subnet..old"]
    assert any("Delete these now" in q and "old subnet" in q and "public subnet" not in q for q in asked)


def test_vm_dependencies_show_boot_volume_and_kept_volumes():
    inv = Inventory(FakeOci(), lambda m: None)
    vm = next(r for r in inv.rows(TEN) if r.kind == "VM")
    assert vm.public == "203.0.113.9" and vm.parent == "PoC"
    also, blockers = inv.dependencies(vm)
    assert any("boot volume ocid1.bootvolume..b" in a for a in also)
    assert any(a.startswith("block volume ocid1.volume..data") and a.endswith("detached and kept") for a in also)
    assert blockers == []


def test_vm_needs_its_name_typed():
    fake = FakeOci()
    inv = Inventory(fake, lambda m: None)
    vm = next(r for r in inv.rows(TEN) if r.kind == "VM")
    answers = {"delete, comma": str(vm.no), "Type the VM name": "wrong-name"}
    review(inv, TEN, lambda q: True, lambda q, d: next((v for k, v in answers.items() if k in q), ""),
           want_subnet=False)
    assert not any(c[:3] == ("compute", "instance", "terminate") for c in fake.calls)


def test_vm_and_its_subnet_go_together_vm_first():
    fake = FakeOci(in_use={"ocid1.subnet..pub"})  # the VM's IP is in this subnet
    out, echo = lines()
    inv = Inventory(fake, echo)
    rows = inv.rows(TEN)
    vm = next(r for r in rows if r.kind == "VM")
    sub = next(r for r in rows if r.ocid == "ocid1.subnet..pub")
    answers = {"delete, comma": f"{sub.no},{vm.no}", "Type the VM name": "kyc-vm"}
    review(inv, TEN, lambda q: True, lambda q, d: next((v for k, v in answers.items() if k in q), ""),
           want_subnet=False)
    ops = [c[:3] for c in fake.calls if c[2] in ("terminate", "delete")]
    assert ops == [("compute", "instance", "terminate"), ("network", "subnet", "delete")]
    assert not any("still in use" in line for line in out)


def test_existing_vm_can_be_picked():
    inv = Inventory(FakeOci(), lambda m: None)
    vm = next(r for r in inv.rows(TEN) if r.kind == "VM")
    answers = {"check": True, "delete any": False}
    choice = review(inv, TEN, lambda q: next(v for k, v in answers.items() if k in q),
                    lambda q, d: str(vm.no) if "existing VM" in q else "", want_subnet=True)
    assert choice.vm == vm and choice.subnet_id == ""


class FakeCleaner:
    def __init__(self, dry=0, real=0):
        self.calls = []
        self.codes = {False: dry, True: real}

    def run(self, compartment_id, backup_id, execute):
        self.calls.append((compartment_id, backup_id, execute))
        return self.codes[execute]


def _pick_compartment(inv):
    return next(r for r in inv.rows(TEN) if r.kind == "Compartment")


def test_compartment_with_resources_goes_to_the_cleaner_dry_run_first():
    fake, cleaner = FakeOci(), FakeCleaner()
    inv = Inventory(fake, lambda m: None, cleaner)
    comp = _pick_compartment(inv)
    review(inv, TEN, lambda q: True, lambda q, d: str(comp.no) if "delete, comma" in q else "", want_subnet=False)
    assert cleaner.calls == [(comp.ocid, TEN, False), (comp.ocid, TEN, True)]
    assert any(c[:3] == ("iam", "compartment", "delete") for c in fake.calls)


def test_cleaner_stops_after_a_no_to_the_plan():
    fake, cleaner = FakeOci(), FakeCleaner()
    inv = Inventory(fake, lambda m: None, cleaner)
    comp = _pick_compartment(inv)
    review(inv, TEN, lambda q: "Run that plan" not in q,
           lambda q, d: str(comp.no) if "delete, comma" in q else "", want_subnet=False)
    assert cleaner.calls == [(comp.ocid, TEN, False)]
    assert not any(c[:3] == ("iam", "compartment", "delete") for c in fake.calls)


def test_failed_dry_run_deletes_nothing():
    fake, cleaner = FakeOci(), FakeCleaner(dry=1)
    inv = Inventory(fake, lambda m: None, cleaner)
    comp = _pick_compartment(inv)
    review(inv, TEN, lambda q: True, lambda q, d: str(comp.no) if "delete, comma" in q else "", want_subnet=False)
    assert [c[2] for c in cleaner.calls] == [False]
    assert not any(c[:3] == ("iam", "compartment", "delete") for c in fake.calls)


def test_sub_compartment_blocks_the_cleaner():
    fake, cleaner = FakeOci(), FakeCleaner()
    real = fake.__call__

    def with_child(*args):
        a = list(args)
        if a[:3] == ["iam", "compartment", "list"] and a[a.index("--compartment-id") + 1] == "ocid1.comp..x":
            return {"data": [{"id": "ocid1.comp..child", "name": "Child"}]}
        return real(*args)
    inv = Inventory(with_child, lambda m: None, cleaner)
    comp = _pick_compartment(inv)
    _, blockers = inv.dependencies(comp)
    assert "sub-compartment Child (remove it first)" in blockers
    review(inv, TEN, lambda q: True, lambda q, d: str(comp.no) if "delete, comma" in q else "", want_subnet=False)
    assert cleaner.calls == []


def test_service_vnic_owner_is_named():
    inv = Inventory(FakeOci(), lambda m: None)
    owner = inv.vnic_owner("vnic-service")
    assert owner.startswith("probably PrivateEndpoint odoo-pe")
    assert "name-of-vnic-service" in owner


def test_vm_name_gets_three_tries():
    fake = FakeOci()
    out, echo = lines()
    inv = Inventory(fake, echo)
    vm = next(r for r in inv.rows(TEN) if r.kind == "VM")
    typed = iter(["intance1", "kyc-vm"])
    review(inv, TEN, lambda q: True,
           lambda q, d: str(vm.no) if "delete, comma" in q else (next(typed) if "Type the VM" in q else ""),
           want_subnet=False)
    assert any(c[:3] == ("compute", "instance", "terminate") for c in fake.calls)
    assert any("try again" in line for line in out)
