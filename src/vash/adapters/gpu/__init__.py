"""Free GPUs for batch jobs. Each provider is a package here with an Adapter (core.interfaces.GPUAdapter)."""
import pkgutil
from pathlib import Path


def providers() -> list[str]:
    """The GPU providers VASH has adapters for, in a stable order."""
    return sorted(m.name for m in pkgutil.iter_modules([str(Path(__file__).parent)]) if m.ispkg)
