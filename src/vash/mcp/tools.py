"""VASH's tools for a chat harness (MCP): projects, tasks, AvA runs, status and the health check.

Plain functions over the files and the `vash` command, so they work and are tested without the MCP library; server.py
only exposes them. Every project lives under one folder (VASH_PROJECTS, default ~/projects); names are checked so a
tool can never reach outside it. A task runs in the background (an AvA loop can take many minutes on the VM's model);
`task_status` reads its result.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,62}$")
KINDS = ("code", "test", "artifact", "feature", "prompt", "manual_step")


class ToolError(ValueError):
    """A wrong argument; the message tells the harness what to send instead."""


def root() -> Path:
    path = Path(os.environ.get("VASH_PROJECTS", str(Path.home() / "projects"))).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    return path


def _name(value: str, what: str) -> str:
    if not NAME.match(value or ""):
        raise ToolError(f"Invalid {what} '{value}': a letter, then letters, digits, '-' or '_' (at most 63)")
    return value


def _project(name: str) -> Path:
    path = root() / _name(name, "project name")
    if not (path / "project-stack.json").exists():
        raise ToolError(f"No project '{name}'. Projects: {', '.join(list_projects()) or 'none'}")
    return path


def _vash(args: list[str], cwd: Path | None = None, timeout: int = 600) -> str:
    exe = shutil.which("vash")
    cmd = [exe, *args] if exe else [sys.executable, "-m", "vash.cli", *args]
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False)
    return (res.stdout + res.stderr).strip()


def list_projects() -> list[str]:
    return sorted(p.name for p in root().iterdir() if (p / "project-stack.json").exists())


def new_project(name: str) -> str:
    target = root() / _name(name, "project name")
    if target.exists():
        raise ToolError(f"Project '{name}' already exists")
    out = _vash(["init", name], cwd=root())
    subprocess.run(["git", "init", "-q"], cwd=target, check=False)
    return f"Project '{name}' created in {target}. {out}".strip()


def new_task(project: str, task_id: str, kind: str, request: str) -> str:
    """Write the task: what to do (the request) and its kind of work, which picks the writer and reviewer models."""
    path = _project(project)
    _name(task_id, "task id")
    if kind not in KINDS:
        raise ToolError(f"Unknown kind '{kind}': use one of {', '.join(KINDS)}")
    if not request.strip():
        raise ToolError("The request is empty: say what the task must produce")
    prompt = path / "audit" / "prompts" / f"{task_id}_prompt.md"
    prompt.parent.mkdir(parents=True, exist_ok=True)
    prompt.write_text(f"type: {kind}\n\n{request.strip()}\n", encoding="utf-8")
    return f"Task {task_id} ({kind}) written to {prompt.relative_to(root())}. Start it with run_task."


def _run_dir(path: Path) -> Path:
    d = path / "audit" / ".runs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def run_task(project: str, task_id: str) -> str:
    """Start the AvA loop for a task in the background and return at once."""
    path = _project(project)
    _name(task_id, "task id")
    if not (path / "audit" / "prompts" / f"{task_id}_prompt.md").exists():
        raise ToolError(f"No task {task_id} in {project}: write it first with new_task")
    runs = _run_dir(path)
    pid_file = runs / f"{task_id}.pid"
    if pid_file.exists() and _alive(int(pid_file.read_text() or 0)):
        return f"Task {task_id} is already running; ask task_status"
    exe = shutil.which("vash")
    cmd = [exe, "ava", task_id] if exe else [sys.executable, "-m", "vash.cli", "ava", task_id]
    with open(runs / f"{task_id}.log", "w") as log:
        proc = subprocess.Popen(cmd, cwd=path, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    pid_file.write_text(str(proc.pid))
    return f"Task {task_id} started (AvA: writer, Gate 1, reviewer; minutes on the VM's model). Ask task_status."


def _alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    try:  # a finished child of this process stays as a zombie until reaped
        done, _ = os.waitpid(pid, os.WNOHANG)
        return done == 0
    except ChildProcessError:
        return True


def task_status(project: str, task_id: str) -> str:
    path = _project(project)
    _name(task_id, "task id")
    runs = _run_dir(path)
    pid_file, log = runs / f"{task_id}.pid", runs / f"{task_id}.log"
    if not pid_file.exists():
        return f"Task {task_id} has not been started"
    output = log.read_text(errors="replace").strip() if log.exists() else ""
    if _alive(int(pid_file.read_text() or 0)):
        return f"Task {task_id} is running." + (f" So far:\n{output[-1500:]}" if output else "")
    logs = sorted((path / "audit" / "ava_logs").glob(f"{task_id.replace('.', '-')}_round*.md"))
    lines = []
    for f in logs:
        text = f.read_text(errors="replace")
        score = re.search(r"\*\*SCORE:\*\*\s*(\S+)", text)
        verdict = re.search(r"\*\*VERDICT:\*\*\s*(\S+)", text)
        lines.append(f"{f.name}: score {score.group(1) if score else '?'}, {verdict.group(1) if verdict else '?'}")
    return f"Task {task_id} finished.\n{output[-1500:]}\nRounds:\n" + ("\n".join(lines) or "none")


def read_result(project: str, task_id: str) -> str:
    path = _project(project)
    _name(task_id, "task id")
    found = sorted((path / "audit" / "artifacts").glob(f"{task_id}_artifact.*"))
    if not found:
        raise ToolError(f"No result for {task_id} yet: ask task_status")
    return found[0].read_text(errors="replace")[:20000]


def list_tasks(project: str) -> str:
    path = _project(project)
    tasks = sorted(p.name.removesuffix("_prompt.md") for p in (path / "audit" / "prompts").glob("*_prompt.md"))
    return "\n".join(f"{t}: {task_status(project, t).splitlines()[0]}" for t in tasks) or "No tasks yet"


def doctor(project: str = "") -> str:
    """VASH's health check here: engine, models (the gateway and the VM's model) and the runner."""
    return _vash(["doctor", "--repo", str(_project(project) if project else root())])


def gpu_quota() -> str:
    """This week's free GPU hours (used, total, when they reset)."""
    return _vash(["gpu", "quota"])


def gpu_run(name: str, model: str, prompts: list[str], no_client_data: bool) -> str:
    """Run a model (e.g. qwen2.5-coder:32b) over prompts on a free GPU, as a batch job. The prompts leave the VM:
    set no_client_data only when they hold no client data."""
    _name(name, "job name")
    if not prompts:
        raise ToolError("No prompts: give at least one")
    folder = root() / ".gpu"
    folder.mkdir(exist_ok=True)
    path = folder / f"{name}.jsonl"
    import json
    path.write_text("".join(json.dumps({"prompt": p}) + "\n" for p in prompts))
    return _vash(["gpu", "run", name, "--model", model, "--prompts", str(path)]
                 + (["--no-client-data"] if no_client_data else []))


def gpu_status(name: str = "") -> str:
    """State of the free GPU jobs (or of one)."""
    if name:
        _name(name, "job name")
    return _vash(["gpu", "status"] + ([name] if name else []))


def gpu_result(name: str) -> str:
    """The answers of a finished GPU job."""
    _name(name, "job name")
    dest = root() / ".gpu" / "results"
    out = _vash(["gpu", "result", name, "--dest", str(dest)])
    found = dest / name / "results.jsonl"
    return found.read_text(errors="replace")[:20000] if found.exists() else out
