"""The gatekeeper: nothing leaves the VM unmasked (method/requirements.md point 3, rule R2).

Client terms (the owner's list), structured personal data (with checksums where there is one) and secrets are
replaced by placeholders before text is sent to any model outside the VM; the map from placeholder to value stays
on the VM. After masking, a deterministic gate scans the text again: if anything sensitive is left, the text must
stay on the VM. No model can overrule the gate.
"""
from .masker import Finding, Masker, gate, unmask

__all__ = ["Finding", "Masker", "gate", "unmask"]
