"""Free-tier guardrails: quota names come from the tenancy, a yes is needed, CD3 modules apply them."""
from vash.adapters.cloud.oci.guardrails import Guardrails

TEN = "ocid1.tenancy..t"
NAMES = {
    "compute": ["standard-a1-core-count", "standard-a1-core-regional-count", "standard-a1-memory-count",
                "standard-a1-memory-regional-count", "standard-e2-micro-core-count", "standard-e4-core-count"],
    "block-storage": ["total-storage-gb"],
    "database": ["adb-free-count", "atp-ocpu-count"],
}


class FakeBuild:
    def __init__(self):
        self.applied = None

    def guardrails(self, statements, email):
        self.applied = (statements, email)


def oci(names):
    def call(*args):
        service = args[args.index("--service-name") + 1]
        return {"data": [{"name": n} for n in names.get(service, [])]}
    return call


def test_free_amounts_are_allowed_and_paid_families_zeroed():
    out, build = [], FakeBuild()
    assert Guardrails(oci(NAMES), out.append, lambda q: True, build).apply(TEN, "owner@example.com")
    statements, email = build.applied
    assert statements[:3] == ["zero compute-core quotas in tenancy", "zero compute-memory quotas in tenancy",
                              "zero database quotas in tenancy"]
    assert "set compute-core quota standard-a1-core-count to 4 in tenancy" in statements
    assert "set compute-memory quota standard-a1-memory-count to 24 in tenancy" in statements
    # OCI also checks the regional A1 limits; "zero" covers them, so they must be allowed again (seen live)
    assert "set compute-core quota standard-a1-core-regional-count to 4 in tenancy" in statements
    assert "set compute-memory quota standard-a1-memory-regional-count to 24 in tenancy" in statements
    assert not any("e4" in s for s in statements)
    assert "set compute-core quota standard-e2-micro-core-count to 2 in tenancy" in statements
    assert "set block-storage quota total-storage-gb to 200 in tenancy" in statements
    assert "set database quota adb-free-count to 2 in tenancy" in statements
    assert email == "owner@example.com"


def test_a_family_without_its_free_limit_name_is_not_zeroed():
    names = {**NAMES, "database": ["atp-ocpu-count"]}  # no free ADB limit found
    out, build = [], FakeBuild()
    Guardrails(oci(names), out.append, lambda q: True, build).apply(TEN, "")
    statements, _ = build.applied
    assert "zero database quotas in tenancy" not in statements
    assert any("Always Free Autonomous Databases" in line and "left out" in line for line in out)


def test_nothing_is_applied_without_a_yes():
    build = FakeBuild()
    assert not Guardrails(oci(NAMES), lambda m: None, lambda q: False, build).apply(TEN, "owner@example.com")
    assert build.applied is None


def test_regional_a1_limits_are_allowed_even_when_not_listed():
    names = {**NAMES, "compute": ["standard-a1-core-count", "standard-a1-memory-count"]}  # no regional names listed
    build = FakeBuild()
    Guardrails(oci(names), lambda m: None, lambda q: True, build).apply(TEN, "")
    statements, _ = build.applied
    assert "set compute-core quota standard-a1-core-regional-count to 4 in tenancy" in statements
    assert "set compute-memory quota standard-a1-memory-regional-count to 24 in tenancy" in statements
