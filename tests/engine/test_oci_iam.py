"""Compartment create: IAM is eventually consistent, so a 404 right after the create is waited out."""
import pytest

from vash.adapters.cloud.oci.iam import create_compartment
from vash.core.exceptions import VashError


def fake(gets):
    calls = []
    answers = iter(gets)

    def oci(*args):
        calls.append(args)
        if args[:3] == ("iam", "compartment", "create"):
            assert "--wait-for-state" not in args
            return {"data": {"id": "ocid1.comp..new"}}
        answer = next(answers)
        if isinstance(answer, Exception):
            raise answer
        return {"data": {"lifecycle-state": answer}}
    return oci, calls


def test_not_found_right_after_create_is_waited_out():
    not_yet = VashError('oci iam compartment failed: {"code": "NotAuthorizedOrNotFound", "status": 404}', "")
    oci, calls = fake([not_yet, not_yet, "ACTIVE"])
    sleeps = []
    assert create_compartment(oci, lambda m: None, "ocid1.tenancy..t", "security", "d", sleeps.append) == "ocid1.comp..new"
    assert len(sleeps) == 2


def test_other_errors_still_stop():
    oci, _ = fake([VashError("oci iam compartment failed: TooManyRequests", "")])
    with pytest.raises(VashError):
        create_compartment(oci, lambda m: None, "t", "security", "d", lambda s: None)


def test_still_invisible_after_polling_continues_with_the_id():
    oci, _ = fake(["CREATING"] * 30)
    out = []
    assert create_compartment(oci, out.append, "t", "security", "d", lambda s: None) == "ocid1.comp..new"
    assert "still making it visible" in out[0]
