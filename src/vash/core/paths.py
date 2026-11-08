"""VASH path resolution."""
import os
from pathlib import Path


def vash_root() -> Path:
    """Return the VASH installation root."""
    env = os.environ.get("VASH_HOME")
    if env:
        return Path(env).resolve()
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    return Path.cwd()
