"""Kaggle: a private notebook on a free GPU runs a model over a list of prompts and saves the answers.

Through Kaggle's official client (the `kaggle` package, Apache-2.0, pinned on the VM). It signs in with an API
token (KAGGLE_API_TOKEN or ~/.kaggle/access_token, given once with `vash onboard oci --keys`). The notebook only
connects out (it installs Ollama, pulls the model, answers, stops); nothing is served from Kaggle. The weekly GPU
quota is read from Kaggle itself, so VASH never runs past it.
"""
from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path
from typing import Any, Mapping

from vash.core.exceptions import VashError
from vash.core.interfaces import GPUAdapter

ACCELERATOR = "NvidiaTeslaT4"  # T4 x2, the free GPU
# How the owner gives the token once (vash onboard oci --keys): where to get it and where it goes on the VM.
TOKEN = {"label": "Kaggle API token", "signup": "https://www.kaggle.com/settings (API, Generate New Token)",
         "file": ".kaggle/access_token"}
OLLAMA_VERSION = "0.40.16"  # the same pin as on the VM
RESULTS = "results.jsonl"

JOB = '''# Made by VASH (vash gpu run). Runs on a free Kaggle GPU: installs Ollama, pulls the model, answers the prompts,
# saves them to results.jsonl and stops. It only connects out.
import json, os, subprocess, time, urllib.request

MODEL = __MODEL__
PROMPTS = __PROMPTS__

subprocess.run("curl -fsSL https://ollama.com/install.sh | OLLAMA_VERSION=__OLLAMA__ sh", shell=True, check=True)
server = subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for _ in range(60):
    try:
        urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=5)
        break
    except OSError:
        time.sleep(2)
subprocess.run(["ollama", "pull", MODEL], check=True)
with open("/kaggle/working/__RESULTS__", "w") as out:
    for i, prompt in enumerate(PROMPTS):
        started = time.time()
        req = urllib.request.Request("http://127.0.0.1:11434/api/generate", method="POST",
                                     data=json.dumps({"model": MODEL, "prompt": prompt, "stream": False}).encode(),
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=1800) as r:
                answer = json.loads(r.read())
            row = {"id": i, "response": answer.get("response", ""), "seconds": round(time.time() - started, 1),
                   "tokens": answer.get("eval_count")}
        except Exception as e:  # one failed prompt does not stop the others
            row = {"id": i, "error": str(e)}
        out.write(json.dumps(row) + "\\n")
        out.flush()
server.terminate()
'''


def job_script(model: str, prompts: list[str]) -> str:
    return (JOB.replace("__MODEL__", json.dumps(model)).replace("__PROMPTS__", json.dumps(prompts, indent=1))
            .replace("__OLLAMA__", OLLAMA_VERSION).replace("__RESULTS__", RESULTS))


def metadata(user: str, slug: str) -> dict[str, Any]:
    return {"id": f"{user}/{slug}", "title": slug, "code_file": "job.py", "language": "python",
            "kernel_type": "script", "is_private": True, "enable_gpu": True, "enable_tpu": False,
            "enable_internet": True, "machine_shape": ACCELERATOR, "dataset_sources": [],
            "competition_sources": [], "kernel_sources": [], "model_sources": []}


class Adapter(GPUAdapter):
    def __init__(self, settings: Mapping[str, Any]):
        super().__init__(settings)
        self._api = settings.get("api")  # tests pass a stand-in

    def api(self) -> Any:
        if self._api is None:
            try:
                from kaggle.api.kaggle_api_extended import KaggleApi
            except ImportError as e:
                raise VashError(f"The Kaggle client is missing ({e})", "pip install 'kaggle==2.2.5' six")
            api = KaggleApi()
            try:
                api.authenticate()
            except (SystemExit, Exception) as e:  # it exits when no token is found
                raise VashError(f"Kaggle sign-in failed ({e})",
                                "Give the Kaggle API token once: vash onboard oci --keys") from None
            self._api = api
        return self._api

    def user(self) -> str:
        api = self.api()
        name = getattr(api, "config_values", {}).get("username") or getattr(api, "get_config_value",
                                                                              lambda _k: "")("username")
        if not name:
            raise VashError("Kaggle did not say whose token this is", "Give the token again: vash onboard oci --keys")
        return name

    def quota(self) -> dict[str, Any]:
        r = self.api().quota_view()
        gpu = r.gpu_quota
        if gpu is None:
            return {"used_hours": 0.0, "total_hours": 0.0, "resets": ""}
        used = gpu.time_used.total_seconds() / 3600
        total = gpu.total_time_allowed.total_seconds() / 3600
        resets = r.quota_refresh_time.isoformat() if r.quota_refresh_time else ""
        return {"used_hours": round(used, 2), "total_hours": round(total, 2), "resets": resets}

    def submit(self, name: str, model: str, prompts: list[str]) -> str:
        slug = re.sub(r"[^a-z0-9-]+", "-", f"vash-{name}".lower()).strip("-")[:50]
        user = self.user()
        with tempfile.TemporaryDirectory(prefix="vash-gpu-") as folder:
            (Path(folder) / "job.py").write_text(job_script(model, prompts))
            (Path(folder) / "kernel-metadata.json").write_text(json.dumps(metadata(user, slug), indent=2))
            self.api().kernels_push(folder, acc=ACCELERATOR)
        return f"{user}/{slug}"

    def status(self, ref: str) -> str:
        r = self.api().kernels_status(ref)
        state = str(getattr(r, "status", r)).split(".")[-1].lower()
        message = getattr(r, "failure_message", "") or ""
        return f"{state}: {message}" if message else state

    def fetch(self, ref: str, dest: Path) -> Path:
        dest.mkdir(parents=True, exist_ok=True)
        self.api().kernels_output(ref, str(dest), file_pattern=RESULTS, force=True, quiet=True)
        found = dest / RESULTS
        if not found.exists():
            raise VashError(f"No {RESULTS} from {ref} yet", "Ask `vash gpu status`; the job may still be running")
        return found
