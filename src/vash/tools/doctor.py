"""`vash doctor`: is everything VASH needs on this machine there and working? Each line says how to fix it.

Outside a project it checks what a new project would use (the scaffold's settings). The checks of a vendor
(a model server, a CI runner) live in that vendor's adapter; this file only collects and prints them.
"""
from __future__ import annotations

import importlib
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from vash.core.exceptions import VashError
from vash.core.freeze import load_freeze
from vash.core.paths import vash_commit, vash_root
from vash.core.registry import load_adapter

MARK = {"ok": "OK  ", "warn": "WARN", "fail": "FAIL", "info": "    "}


@dataclass(frozen=True)
class Check:
    area: str
    state: str  # ok, warn, fail, info
    found: str
    fix: str = ""


def _version(cmd: list[str]) -> str:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=20)
        return (out.stdout or out.stderr).strip().splitlines()[0] if (out.stdout or out.stderr).strip() else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def engine() -> list[Check]:
    from importlib.metadata import PackageNotFoundError, version
    try:
        v = version("vash")
    except PackageNotFoundError:
        v = "not installed as a package"
    checks = [Check("VASH", "ok", f"{v} (commit {vash_commit()[:12]}) on Python {platform.python_version()}")]
    if sys.version_info < (3, 11):
        checks.append(Check("Python", "fail", platform.python_version(), "VASH needs Python 3.11 or newer"))
    for tool, need, fix in (("git", "fail", "sudo apt-get install -y git"),
                            ("terraform", "warn", "needed only to build cloud resources; see the onboarding")):
        path = shutil.which(tool)
        checks.append(Check(tool, "ok", _version([tool, "--version"]) or path) if path
                      else Check(tool, need, "not found", fix))
    return checks


def project(repo: Path) -> tuple[list[Check], object | None, bool]:
    """The project's freeze, else the scaffold's (what a new project gets)."""
    try:
        return [Check("Project", "ok", f"{repo} (project-stack.json)")], load_freeze(repo), True
    except VashError:
        scaffold = vash_root() / "scaffold" / "project"
        try:
            return ([Check("Project", "info", f"not in a project ({repo}); checking what `vash init` sets up")],
                    load_freeze(scaffold), False)
        except VashError as e:
            return [Check("Project", "fail", f"no project and no scaffold: {e}", "Reinstall VASH")], None, False


def models(freeze) -> list[Check]:
    used = {role: name for role, name in freeze.data.get("models", {}).items() if isinstance(name, str)}
    checks = []
    for name, route in freeze.routes.items():
        roles = ", ".join(r for r, n in used.items() if n == name) or "unused"
        try:
            adapter = load_adapter("llm", route.adapter, {"route": name, "model": route.model,
                                                          "base_url": route.base_url, "key_env": route.key_env})
            ok, found, fix = adapter.check(route)  # type: ignore[attr-defined]
        except VashError as e:
            ok, found, fix = False, e.message, e.fix
        state = "ok" if ok else ("fail" if roles != "unused" else "warn")
        checks.append(Check(f"Model route {name} ({roles})", state, found, fix))
    return checks


def runner(freeze) -> list[Check]:
    choice = freeze.ci[0] if freeze else ""
    if not choice:
        return []
    try:
        module = importlib.import_module(f"vash.adapters.ci.{choice.replace('-', '_')}")
        ok, found, fix = module.Adapter.runner_status()
    except (ImportError, AttributeError) as e:
        return [Check("CI runner", "warn", f"cannot check the {choice} runner: {e}")]
    if ok is None:
        return [Check("CI runner", "info", found)]
    return [Check("CI runner", "ok" if ok else "fail", found, fix)]


def run(repo: Path) -> int:
    checks = engine()
    found, freeze, _ = project(repo)
    checks += found
    if freeze is not None:
        checks += models(freeze) + runner(freeze)
    for c in checks:
        print(f"[{MARK[c.state]}] {c.area}: {c.found}")
        if c.fix:
            print(f"         fix: {c.fix}")
    failed = [c for c in checks if c.state == "fail"]
    print(f"\n{len(failed)} problem(s)" if failed else "\nAll checks passed")
    return 1 if failed else 0
