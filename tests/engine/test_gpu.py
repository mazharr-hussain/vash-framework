"""Free GPU batch jobs (`vash gpu`): Kaggle through its official client, within the weekly free quota."""
import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from vash.adapters.gpu import providers
from vash.adapters.gpu.kaggle.adapter import Adapter, job_script, metadata
from vash.core.exceptions import VashError
from vash.tools import gpu


class FakeKaggle:
    """Stands in for kaggle.api.kaggle_api_extended.KaggleApi."""

    def __init__(self, used_h=2.0, total_h=30.0):
        self.config_values = {"username": "owner"}
        self.used, self.total = used_h, total_h
        self.pushed = []

    def quota_view(self):
        return SimpleNamespace(
            gpu_quota=SimpleNamespace(time_used=timedelta(hours=self.used), total_time_allowed=timedelta(hours=self.total)),
            quota_refresh_time=datetime(2026, 11, 29, tzinfo=timezone.utc))

    def kernels_push(self, folder, acc=None):
        from pathlib import Path
        self.pushed.append({"acc": acc, "meta": json.loads((Path(folder) / "kernel-metadata.json").read_text()),
                            "job": (Path(folder) / "job.py").read_text()})

    def kernels_status(self, ref):
        return SimpleNamespace(status="KernelWorkerStatus.COMPLETE", failure_message="")

    def kernels_output(self, ref, path, file_pattern=None, force=False, quiet=True):
        from pathlib import Path
        Path(path, file_pattern).write_text('{"id": 0, "response": "def add(a, b): return a + b"}\n')
        return [file_pattern], ""


@pytest.fixture
def kaggle(monkeypatch, tmp_path):
    fake = FakeKaggle()
    monkeypatch.setattr(gpu, "STATE", tmp_path / "state")
    real = gpu.load_adapter
    monkeypatch.setattr(gpu, "load_adapter", lambda cat, choice, settings: real(cat, choice, {**settings, "api": fake}))
    return fake


def test_kaggle_is_a_gpu_provider():
    assert "kaggle" in providers()


def test_job_runs_a_model_over_the_prompts_on_a_private_gpu_notebook():
    src = job_script("qwen2.5-coder:32b", ['say "hi"', "two\nlines"])
    compile(src, "job.py", "exec")
    assert 'MODEL = "qwen2.5-coder:32b"' in src and "OLLAMA_VERSION=0.40.16" in src
    meta = metadata("owner", "vash-t1")
    assert meta["is_private"] and meta["enable_gpu"] and meta["enable_internet"] and meta["id"] == "owner/vash-t1"


def test_run_checks_the_quota_and_never_sends_client_data_unconfirmed(kaggle, tmp_path, capsys):
    prompts = tmp_path / "p.txt"
    prompts.write_text("Write add(a, b).\n{\"prompt\": \"Write sub(a, b).\"}\n")
    with pytest.raises(VashError, match="no client data"):
        gpu.run("t1", "qwen2.5-coder:32b", prompts, no_client_data=False)
    assert kaggle.pushed == []
    assert gpu.run("t1", "qwen2.5-coder:32b", prompts, no_client_data=True) == 0
    pushed = kaggle.pushed[0]
    assert pushed["acc"] == "NvidiaTeslaT4" and pushed["meta"]["id"] == "owner/vash-t1"
    assert "Write sub(a, b)." in pushed["job"]
    gpu.status()
    gpu.result("t1", tmp_path / "out")
    out = capsys.readouterr().out
    assert "complete" in out and (tmp_path / "out/t1/results.jsonl").exists()


def test_no_job_when_the_free_hours_are_used_up(kaggle, tmp_path):
    kaggle.used = 29.6
    prompts = tmp_path / "p.txt"
    prompts.write_text("x\n")
    with pytest.raises(VashError, match="free GPU left"):
        gpu.run("t2", "m", prompts, no_client_data=True)
    assert kaggle.pushed == []


def test_quota_is_read_from_the_provider(kaggle, capsys):
    gpu.quota()
    assert "2.0h of 30.0h used" in capsys.readouterr().out


def test_a_missing_kaggle_client_says_how_to_install_it(monkeypatch):
    import builtins
    real_import = builtins.__import__

    def no_kaggle(name, *args, **kw):
        if name.startswith("kaggle"):
            raise ImportError("No module named 'kaggle'")
        return real_import(name, *args, **kw)
    monkeypatch.setattr(builtins, "__import__", no_kaggle)
    with pytest.raises(VashError) as err:
        Adapter({}).api()
    assert "kaggle==2.2.5" in err.value.fix
