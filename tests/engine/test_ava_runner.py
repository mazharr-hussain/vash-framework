"""Tests for the AvA runner (C-14)."""
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock
from vash.ava.runner import run_activity
from tests.mocks.adapters.fake_llm import FakeLLM

def test_run_activity_approve(tmp_repo, monkeypatch, tmp_path):
    prompt_dir = tmp_repo / "audit" / "prompts"
    prompt_dir.mkdir(parents=True)
    (prompt_dir / "t1_prompt.md").write_text("type: code\nWrite code")

    coder = FakeLLM({}, ["```python\nx = 1\n```"])
    critic = FakeLLM({}, ["Score: 95\nLooks good."])

    res = run_activity("t1", tmp_repo, llm={"local": coder, "review": critic})
    assert res.verdict == "APPROVED"
    assert res.scores == [95]

def test_run_activity_modify(tmp_repo, monkeypatch, tmp_path):
    prompt_dir = tmp_repo / "audit" / "prompts"
    prompt_dir.mkdir(parents=True)
    (prompt_dir / "t1_prompt.md").write_text("Write code")

    coder = FakeLLM({}, ["bad code"] * 3)
    critic = FakeLLM({}, ["Score: 50\nFix this."] * 3)

    res = run_activity("t1", tmp_repo, llm={"local": coder, "review": critic})
    assert res.verdict == "ESCALATED"
    assert len(res.scores) == 3

def test_run_activity_gate1_fail(tmp_repo, monkeypatch, tmp_path):
    prompt_dir = tmp_repo / "audit" / "prompts"
    prompt_dir.mkdir(parents=True)
    (prompt_dir / "t1_prompt.md").write_text("Write code")

    coder = FakeLLM({}, ['TOKEN = "' + "ghp_" + "A" * 36 + '"'] * 3)
    critic = FakeLLM({}, ["Score: 95"] * 3)

    res = run_activity("t1", tmp_repo, llm={"local": coder, "review": critic})
    assert res.verdict == "FAIL"
    assert res.scores == []
    assert len(res.log_paths) == 3

def test_run_activity_missing_prompt(tmp_repo):
    with pytest.raises(Exception):
        run_activity("missing", tmp_repo)
