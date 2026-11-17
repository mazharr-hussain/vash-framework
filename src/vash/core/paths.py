"""VASH path resolution."""
import os
from pathlib import Path

DATA_DIRS = ("method", "catalog", "scaffold", "iac")


def vash_root() -> Path:
    """Return the VASH root: VASH_HOME, else the installed data, else the source checkout."""
    env = os.environ.get("VASH_HOME")
    if env:
        return Path(env).resolve()
    current = Path(__file__).resolve()
    data = current.parent.parent / "_data"
    if data.is_dir():
        return data
    for parent in current.parents:
        if (parent / "pyproject.toml").exists() and (parent / "method").is_dir():
            return parent
    return Path.cwd()


def vash_commit() -> str:
    """The commit of the VASH that is running: from pip's record of a git install (`pip install git+...@v3.0.0`),
    else from the git checkout it runs from; "to-verify" when neither tells (e.g. a wheel from a release page)."""
    import importlib.metadata
    import json
    import re
    import subprocess

    try:
        record = importlib.metadata.distribution("vash").read_text("direct_url.json")
        commit = json.loads(record or "{}").get("vcs_info", {}).get("commit_id", "")
        if re.fullmatch(r"[0-9a-f]{40}", commit or ""):
            return commit
    except (importlib.metadata.PackageNotFoundError, ValueError):
        pass
    root = vash_root()
    if (root / ".git").exists():
        res = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], check=False, capture_output=True, text=True)
        if res.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", res.stdout.strip()):
            return res.stdout.strip()
    return "to-verify"
