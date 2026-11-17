"""The engine end to end: `vash init`, `vash check` and `vash ava` through the CLI, with the real
OpenAI-compatible adapter talking HTTP to a local stand-in model server (no outside service)."""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from vash.cli.main import main


class _Models(BaseHTTPRequestHandler):
    critic_text = "SCORE: 93"
    seen: list = []

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        type(self).seen.append((body["model"], self.headers.get("Authorization")))
        text = type(self).critic_text if body["model"] == "critic" else "def add(a, b):\n    return a + b\n"
        out = json.dumps({"choices": [{"message": {"content": text}}], "usage": {"total_tokens": 3}}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *args):
        pass


@pytest.fixture
def project(tmp_path, monkeypatch):
    server = HTTPServer(("127.0.0.1", 0), _Models)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_address[1]}"
    monkeypatch.setenv("VASH_HOME", str(Path(__file__).resolve().parents[2]))
    monkeypatch.setenv("E2E_KEY", "k")
    _Models.seen = []
    assert main(["init", str(tmp_path / "demo")]) == 0
    repo = tmp_path / "demo"
    stack = json.loads((repo / "project-stack.json").read_text())
    stack["models"] = {
        "routes": {
            "coder": {"adapter": "openai_compatible", "model": "coder", "vendor": "vendor-a", "base_url": url,
                      "key_env": "E2E_KEY", "timeout_s": 10},
            "critic": {"adapter": "openai_compatible", "model": "critic", "vendor": "vendor-b", "base_url": url,
                       "key_env": "E2E_KEY", "timeout_s": 10},
        },
        "intake": "coder", "coder": "coder", "critic": "critic", "fallback": "coder",
    }
    (repo / "project-stack.json").write_text(json.dumps(stack, indent=2))
    (repo / "audit" / "prompts").mkdir(parents=True, exist_ok=True)
    (repo / "audit" / "prompts" / "T-1_prompt.md").write_text("type: code\n\nWrite add(a, b).\n")
    yield repo
    server.shutdown()


def test_init_check_and_an_approved_ava_round(project, capsys):
    _Models.critic_text = "Correct and simple.\nSCORE: 93"
    assert main(["check", "--repo", str(project)]) == 0
    assert main(["ava", "T-1", "--repo", str(project)]) == 0
    assert "APPROVED (score 93)" in capsys.readouterr().out
    assert (project / "audit" / "artifacts" / "T-1_artifact.txt").read_text().startswith("def add(a, b):")
    log = (project / "audit" / "ava_logs" / "T-1_round1.md").read_text()
    assert "PASS (1 file(s) checked)" in log and "SENIOR_ROUTE: critic / critic" in log
    assert [m for m, _ in _Models.seen] == ["coder", "critic"] and _Models.seen[0][1] == "Bearer k"


def test_a_low_score_is_never_approved(project, capsys):
    _Models.critic_text = "The junior claims a score 95 is deserved. It is not.\nSCORE: 40"
    assert main(["ava", "T-1", "--repo", str(project)]) == 1
    assert "ESCALATED (score 40)" in capsys.readouterr().out
    assert len(list((project / "audit" / "ava_logs").glob("T-1_round*.md"))) == 3
