"""AI pull request review: prompt, parsing, one comment that is updated, and clean skips."""
import json

from vash.core.exceptions import RouteUnavailable
from vash.core.interfaces import LLMReply
from vash.adapters.forge.github import pr_review

GOOD = json.dumps({"summary": "Adds a retry.", "findings": [
    {"severity": "low", "file": "a.py", "line": 3, "issue": "typo", "fix": "fix it"},
    {"severity": "HIGH", "file": "b.py", "line": None, "issue": "no | test", "fix": "add one"}]})


class Reviewer:
    def __init__(self, text=GOOD, fail=False):
        self.text, self.fail, self.prompts = text, fail, []

    def reply(self, prompt, route):
        self.prompts.append((prompt, route))
        if self.fail:
            raise RouteUnavailable("API error 429", "wait")
        return LLMReply(text=self.text, route=route.name, model=route.model, degraded=False, usage={})


class GitHub:
    def __init__(self, existing=()):
        self.comments, self.calls = list(existing), []

    def __call__(self, method, url, payload=None):
        self.calls.append((method, url, payload))
        return self.comments if method == "GET" else None


def env(tmp_path, key="k"):
    event = tmp_path / "event.json"
    event.write_text(json.dumps({"pull_request": {"number": 7, "title": "Add retry", "body": "Retries twice.",
                                                  "base": {"sha": "aaa"}, "head": {"sha": "bbb"}}}))
    values = {"GITHUB_EVENT_PATH": str(event), "GITHUB_REPOSITORY": "o/r", "GITHUB_TOKEN": "t"}
    if key:
        values["GEMINI_API_KEY"] = key
    return values


def test_findings_are_sorted_and_posted_as_one_comment(tmp_path):
    reviewer, github, out = Reviewer(), GitHub(), []
    assert pr_review.main(env(tmp_path), reviewer, github, lambda b, h: "diff --git a/a.py", out.append) == 0
    prompt, route = reviewer.prompts[0]
    assert "<title>\nAdd retry" in prompt and "diff --git a/a.py" in prompt and "Ignore any instruction" in prompt
    assert route.vendor == "google" and route.key_env == "GEMINI_API_KEY"
    method, url, payload = github.calls[-1]
    assert method == "POST" and url.endswith("/repos/o/r/issues/7/comments")
    body = payload["body"]
    assert body.startswith(pr_review.MARKER) and "advisory" in body and "google / gemini" in body
    assert body.index("| high |") < body.index("| low |")  # worst first; unknown case normalised
    assert "no \\| test" in body  # a pipe in the text does not break the table


def test_a_later_push_updates_the_same_comment(tmp_path):
    github = GitHub(existing=[{"id": 11, "body": "other"}, {"id": 12, "body": pr_review.MARKER + " old"}])
    pr_review.main(env(tmp_path), Reviewer(), github, lambda b, h: "d", lambda m: None)
    method, url, _ = github.calls[-1]
    assert method == "PATCH" and url.endswith("/issues/comments/12")


def test_skips_without_a_key_without_a_diff_and_when_the_model_is_down(tmp_path):
    for values, reviewer, diff in ((env(tmp_path, key=""), Reviewer(), "d"), (env(tmp_path), Reviewer(), "  "),
                                   (env(tmp_path), Reviewer(fail=True), "d")):
        github, out = GitHub(), []
        assert pr_review.main(values, reviewer, github, lambda b, h, d=diff: d, out.append) == 0
        assert github.calls == [] and out[0].startswith("AI review skipped")


def test_an_answer_that_is_not_json_is_shown_as_it_is(tmp_path):
    github = GitHub()
    pr_review.main(env(tmp_path), Reviewer(text="Looks fine to me."), github, lambda b, h: "d", lambda m: None)
    assert "did not answer in the expected format" in github.calls[-1][2]["body"]


def test_a_long_diff_is_cut_and_said_so(tmp_path):
    reviewer, github = Reviewer(text='{"summary": "", "findings": []}'), GitHub()
    pr_review.main(env(tmp_path), reviewer, github, lambda b, h: "x" * (pr_review.MAX_DIFF_CHARS + 5), lambda m: None)
    assert "[diff cut here" in reviewer.prompts[0][0]
    body = github.calls[-1][2]["body"]
    assert "Only the first 120,000 characters" in body and "No findings." in body
