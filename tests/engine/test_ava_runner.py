"""Tests for the AvA runner (C-14)."""
import json
import pytest
from pathlib import Path
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


def _iterative(tmp_repo):
    path = tmp_repo / "project-stack.json"
    data = json.loads(path.read_text())
    data["delivery"] = {"mode": "iterative", "iteration_days": 14}
    path.write_text(json.dumps(data))


def test_feature_and_iteration_written_to_log(tmp_repo):
    prompt_dir = tmp_repo / "audit" / "prompts"
    prompt_dir.mkdir(parents=True)
    (prompt_dir / "f1_prompt.md").write_text("**TYPE:** FEATURE\n**FEATURE:** KYC-12\niteration: S3\nDesign it")
    coder = FakeLLM({}, ["# Feature design\nRequirements listed."])
    critic = FakeLLM({}, ["Score: 92\nGood."])
    res = run_activity("f1", tmp_repo, llm={"local": coder, "review": critic})
    assert res.verdict == "APPROVED"
    log = Path(res.log_paths[0]).read_text()
    assert "**FEATURE:** KYC-12" in log
    assert "**ITERATION:** S3" in log


def test_feature_checklist_sent_to_critic(tmp_repo):
    prompt_dir = tmp_repo / "audit" / "prompts"
    prompt_dir.mkdir(parents=True)
    (prompt_dir / "f2_prompt.md").write_text("type: feature\nfeature: KYC-13\nDesign it")
    critic = FakeLLM({}, ["Score: 90"])
    run_activity("f2", tmp_repo, llm={"local": FakeLLM({}, ["# Design\nText."]), "review": critic})
    assert "Checklist: Feature Activity" in critic.requests[0]


def test_iterative_mode_requires_feature_line(tmp_repo):
    from vash.core.exceptions import VashError
    _iterative(tmp_repo)
    prompt_dir = tmp_repo / "audit" / "prompts"
    prompt_dir.mkdir(parents=True)
    (prompt_dir / "c1_prompt.md").write_text("type: code\nWrite code")
    with pytest.raises(VashError, match="no feature: line"):
        run_activity("c1", tmp_repo, llm={"local": FakeLLM({}, ["x"]), "review": FakeLLM({}, ["Score: 95"])})


def test_phased_mode_needs_no_feature_line(tmp_repo):
    prompt_dir = tmp_repo / "audit" / "prompts"
    prompt_dir.mkdir(parents=True)
    (prompt_dir / "c2_prompt.md").write_text("type: code\nWrite code")
    res = run_activity("c2", tmp_repo, llm={"local": FakeLLM({}, ["x = 1"]), "review": FakeLLM({}, ["Score: 95"])})
    assert res.verdict == "APPROVED"


def _prompt(tmp_repo, task_id, text):
    prompt_dir = tmp_repo / "audit" / "prompts"
    prompt_dir.mkdir(parents=True, exist_ok=True)
    (prompt_dir / f"{task_id}_prompt.md").write_text(text)


def test_a_number_after_score_in_a_sentence_is_not_the_score(tmp_repo):
    # Seen in an end-to-end run: the critic scored 40, the engine read "95" from the sentence and approved.
    _prompt(tmp_repo, "s1", "type: code\nWrite code")
    critic = FakeLLM({}, ["The junior claims a score 95 is deserved. It is not: no tests.\nSCORE: 40"] * 3)
    res = run_activity("s1", tmp_repo, llm={"local": FakeLLM({}, ["x = 1"] * 3), "review": critic})
    assert res.scores == [40, 40, 40] and res.verdict == "ESCALATED"


def test_the_last_score_line_counts_and_a_missing_one_scores_0(tmp_repo):
    from vash.ava.runner import parse_score
    assert parse_score("**Score:** 70\n...after fixes...\n**SCORE: 91**") == 91
    assert parse_score("Score (0-100) would be high") is None and parse_score("SCORE: 250") is None
    _prompt(tmp_repo, "s2", "type: code\nWrite code")
    res = run_activity("s2", tmp_repo, llm={"local": FakeLLM({}, ["x = 1"] * 3),
                                            "review": FakeLLM({}, ["Looks great to me."] * 3)})
    assert res.scores == [0, 0, 0]
    assert "gave no `SCORE: <0-100>` line" in Path(res.log_paths[0]).read_text()


def test_the_critic_sees_the_task_and_is_told_the_score_format(tmp_repo):
    _prompt(tmp_repo, "s3", "type: code\nWrite a function that adds two numbers")
    critic = FakeLLM({}, ["SCORE: 95"])
    run_activity("s3", tmp_repo, llm={"local": FakeLLM({}, ["x = 1"]), "review": critic})
    sent = critic.requests[0]
    assert "<task>" in sent and "adds two numbers" in sent and "SCORE: <0-100>" in sent


def test_the_log_tells_the_truth_about_gate1_and_routes(tmp_repo):
    _prompt(tmp_repo, "s4", "type: code\nWrite code")
    secret = 'TOKEN = "' + "ghp_" + "A" * 36 + '"'
    res = run_activity("s4", tmp_repo, llm={"local": FakeLLM({}, [secret, "x = 1"]),
                                            "review": FakeLLM({}, ["SCORE: 95"])})
    failed, passed = (Path(p).read_text() for p in res.log_paths)
    assert "FAIL (" in failed.split("## Gate 1")[1] and "the critic was not asked" in failed
    assert "PASS (1 file(s) checked)" in passed
    assert "JUNIOR_ROUTE: local / to-verify" in passed and "SENIOR_ROUTE: review / to-verify" in passed
    assert "[reason]" not in passed and "[item]" not in passed and "[vendor / model]" not in passed
