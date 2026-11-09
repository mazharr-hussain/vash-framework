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
        if a[:3] == ["iam", "compartment", "list"]:
            return {"data": [{"id": "ocid1.comp..x", "name": "PoC", "lifecycle-state": "ACTIVE",
                              "compartment-id": TEN}]}
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
            return {"data": [{"ip-address": "10.0.0.5", "display-name": "kyc-vm"}] if sid in self.in_use else []}
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
    assert picked == "ocid1.subnet..pub"


def test_review_no_check_does_nothing():
    fake = FakeOci()
    assert review(Inventory(fake, lambda m: None), TEN, lambda q: False, lambda q, d: "", True) == ""
    assert fake.calls == []


def test_private_subnet_cannot_be_picked():
    fake = FakeOci()
    inv = Inventory(fake, lambda m: None)
    priv = next(r.no for r in inv.rows(TEN) if r.ocid == "ocid1.subnet..priv")
    answers = {"check": True, "delete any": False}
    picked = review(inv, TEN, lambda q: next(v for k, v in answers.items() if k in q),
                    lambda q, d: str(priv), want_subnet=True)
    assert picked == ""


def test_in_use_subnet_is_blocked_and_not_deleted():
    fake = FakeOci(in_use={"ocid1.subnet..pub"})
    out, echo = lines()
    inv = Inventory(fake, echo)
    no = next(r.no for r in inv.rows(TEN) if r.ocid == "ocid1.subnet..pub")
    review(inv, TEN, lambda q: True, lambda q, d: str(no) if "delete" in q else "", want_subnet=False)
    assert not any(c[2] == "delete" for c in fake.calls)
    assert any("still in use: IP 10.0.0.5 (kyc-vm)" in line for line in out)
    assert any("every choice is still in use" in line for line in out)


def test_vcn_dependencies_listed_and_in_use_child_blocks():
    fake = FakeOci(in_use={"ocid1.subnet..priv"})
    inv = Inventory(fake, lambda m: None)
    vcn = next(r for r in inv.rows(TEN) if r.ocid == "ocid1.vcn..a")
    also, blockers = inv.dependencies(vcn)
    assert "subnet public subnet" in also and "internet-gateway igw-1" in also
    assert "route-table rt-extra" in also and not any("rt-default" in a for a in also)
    assert blockers == ["subnet private subnet: IP 10.0.0.5 (kyc-vm)"]


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
