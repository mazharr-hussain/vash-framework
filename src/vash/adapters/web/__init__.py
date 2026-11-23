"""Web access to the VM: a public address with a login in front, and no port opened on the VM.

Each provider is a package here with an Adapter (core.interfaces.WebAccessAdapter)."""
import pkgutil
from pathlib import Path


def providers() -> list[str]:
    """The web access providers VASH has adapters for, in a stable order."""
    return sorted(m.name for m in pkgutil.iter_modules([str(Path(__file__).parent)]) if m.ispkg)
