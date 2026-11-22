"""`vash gpu`: batch jobs on free GPUs (a model over a list of prompts), within each provider's free quota.

A job sends its prompts to the provider, so it must hold no client data (rule R2): until the gatekeeper masks
data, the owner confirms it with --no-client-data. Jobs are remembered in ~/.vash/gpu/jobs.json.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from vash.adapters.gpu import providers
from vash.core.exceptions import VashError
from vash.core.registry import load_adapter

STATE = Path.home() / ".vash" / "gpu"


def _jobs() -> dict[str, dict]:
    path = STATE / "jobs.json"
    return json.loads(path.read_text()) if path.exists() else {}


def _save(jobs: dict[str, dict]) -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    (STATE / "jobs.json").write_text(json.dumps(jobs, indent=2) + "\n")


def adapter(provider: str | None, settings: dict | None = None):
    names = providers()
    choice = provider or (names[0] if names else "")
    if choice not in names:
        raise VashError(f"No GPU provider '{provider}'", f"Use one of: {', '.join(names)}")
    return choice, load_adapter("gpu", choice, settings or {})


def quota(provider: str | None = None) -> int:
    name, gpu = adapter(provider)
    q = gpu.quota()
    left = max(0.0, q["total_hours"] - q["used_hours"])
    print(f"{name}: {q['used_hours']}h of {q['total_hours']}h used this week, {left:.1f}h left (resets {q['resets']})")
    return 0


def run(name: str, model: str, prompts_file: Path, no_client_data: bool, provider: str | None = None,
        min_hours: float = 1.0) -> int:
    if not no_client_data:
        raise VashError("A GPU job sends its prompts to the GPU provider",
                        "Confirm the prompts hold no client data with --no-client-data (rule R2)")
    lines = [line.strip() for line in prompts_file.read_text().splitlines() if line.strip()]
    prompts = [json.loads(line)["prompt"] if line.startswith("{") else line for line in lines]
    if not prompts:
        raise VashError(f"No prompts in {prompts_file}", "One prompt per line, or JSON lines with a 'prompt' field")
    pname, gpu = adapter(provider)
    q = gpu.quota()
    if q["total_hours"] - q["used_hours"] < min_hours:
        raise VashError(f"Only {q['total_hours'] - q['used_hours']:.1f}h of free GPU left on {pname} this week",
                        f"Wait until {q['resets']}, or use another GPU provider")
    ref = gpu.submit(name, model, prompts)
    jobs = _jobs()
    jobs[name] = {"provider": pname, "ref": ref, "model": model, "prompts": len(prompts), "started": time.time()}
    _save(jobs)
    print(f"GPU job {name} started on {pname} ({ref}): {model} over {len(prompts)} prompt(s). "
          "Ask `vash gpu status`, then `vash gpu result`.")
    return 0


def status(name: str | None = None) -> int:
    jobs = _jobs()
    if not jobs:
        print("No GPU jobs")
        return 0
    for job_name, job in sorted(jobs.items()):
        if name and job_name != name:
            continue
        _, gpu = adapter(job["provider"])
        print(f"{job_name}: {gpu.status(job['ref'])} ({job['provider']}, {job['model']}, {job['prompts']} prompt(s))")
    return 0


def result(name: str, dest: Path) -> int:
    job = _jobs().get(name)
    if not job:
        raise VashError(f"No GPU job '{name}'", "See `vash gpu status`")
    _, gpu = adapter(job["provider"])
    path = gpu.fetch(job["ref"], dest / name)
    print(f"Answers of {name}: {path}")
    return 0
