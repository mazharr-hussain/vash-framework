"""The gatekeeper: mask before anything leaves the VM, gate what is left, unmask on the VM."""
import json

from vash.gatekeeper import Masker, gate, unmask
from vash.gatekeeper.detectors import _iban_ok, _luhn_ok


def test_structured_values_and_secrets_are_masked_and_come_back():
    m = Masker(terms=["Acme Bank", "acme.local"])
    text = ('Acme Bank, IBAN SA03 8000 0000 6080 1016 7519, mail a.k@acme.local, ID 1023456789, host db01.acme.local '
            '10.2.3.4, card 4111 1111 1111 1111, password = "Sup3rS3cret!x", '  # pragma: allowlist secret (a test value)
            'ocid1.vault.oc1.eu-frankfurt-1.amaaaaaajp4k5miai5b4b72fmqa3ua2ocfarkck')
    masked = m.mask(text)
    for value in ("Acme Bank", "SA03", "a.k@acme.local", "1023456789", "10.2.3.4", "4111", "Sup3rS3cret", "ocid1."):
        assert value not in masked
    assert gate(masked, m.terms) == []
    assert unmask(masked, m.mapping) == text


def test_the_same_value_gets_the_same_placeholder():
    m = Masker(terms=["Acme"])
    assert m.mask("Acme and acme") == "<TERM_1> and <TERM_1>"


def test_checksums_avoid_false_hits():
    assert _iban_ok("SA03 8000 0000 6080 1016 7519") and not _iban_ok("SA03 8000 0000 6080 1016 7518")
    assert _luhn_ok("4111 1111 1111 1111") and not _luhn_ok("4111 1111 1111 1112")
    m = Masker()
    assert m.mask("version 1.2.3.4 and order 1234567890123") == "version 1.2.3.4 and order 1234567890123" or \
        "<CARD" not in m.mask("order 1234567890123")


def test_code_is_left_alone():
    code = "PROCEDURE create_party(p_name IN VARCHAR2) IS BEGIN NULL; END;"
    m = Masker(prose=Masker.is_prose("x.pkb"))
    assert m.mask(code) == code and not Masker.is_prose("pkg.pks") and Masker.is_prose("README.md")


def test_the_gate_blocks_what_was_not_masked():
    assert [f.kind for f in gate("mail me at someone@example.org")] == ["EMAIL"]
    assert gate("see <EMAIL_1> and <TERM_2>") == []


def test_the_map_stays_private(tmp_path):
    m = Masker(terms=["Acme"])
    m.mask("Acme")
    path = tmp_path / "map.json"
    m.save(path)
    assert json.loads(path.read_text()) == {"<TERM_1>": "Acme"} and oct(path.stat().st_mode & 0o777) == "0o600"
