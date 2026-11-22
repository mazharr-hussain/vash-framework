"""`vash doctor`: every check says what it found and how to fix it; model checks spend no tokens."""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from vash.adapters.ci.github_actions.adapter import Adapter as Actions
from vash.adapters.llm.ollama.adapter import Adapter as Ollama
from vash.adapters.llm.openai_compatible.adapter import Adapter as OpenAICompatible
from vash.core.interfaces import RouteSettings
from vash.tools import doctor


class Server:
    """A stand-in model server: /api/tags (Ollama) and /v1/models (OpenAI format)."""

    def __init__(self, models=("qwen2.5-coder:7b",), status=200):
        outer = self
        self.paths = []

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):  # noqa: N802
                outer.paths.append(self.path)
                body = json.dumps({"models": [{"name": m} for m in models], "data": []}).encode()
                self.send_response(status)
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *a):
                pass

        self.httpd = HTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_port}"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self):
        self.httpd.shutdown()


def route(adapter, model, base_url, key_env=None):
    return RouteSettings(name="r", adapter=adapter, model=model, vendor="v", base_url=base_url, key_env=key_env,
                         timeout_s=5)


def test_ollama_ready_missing_model_and_down():
    srv = Server()
    try:
        assert Ollama({}).check(route("ollama", "qwen2.5-coder:7b", srv.url))[0]
        ok, found, fix = Ollama({}).check(route("ollama", "llama3.1:8b", srv.url))
        assert not ok and "not pulled" in found and fix == "ollama pull llama3.1:8b"
        assert all(p == "/api/tags" for p in srv.paths)  # listing only, no generation
    finally:
        srv.close()
    ok, _, fix = Ollama({}).check(route("ollama", "qwen2.5-coder:7b", "http://127.0.0.1:9"))
    assert not ok and "systemctl start ollama" in fix


def test_openai_compatible_key_and_answer(monkeypatch):
    ok, found, fix = OpenAICompatible({}).check(route("openai_compatible", "m", "http://x/v1", "NO_SUCH_KEY"))
    assert not ok and "NO_SUCH_KEY" in fix
    monkeypatch.setenv("TEST_KEY", "k")
    srv = Server()
    try:
        assert OpenAICompatible({}).check(route("openai_compatible", "m", srv.url + "/v1", "TEST_KEY"))[0]
        assert srv.paths == ["/v1/models"]
    finally:
        srv.close()
    bad = Server(status=401)
    try:
        ok, found, _ = OpenAICompatible({}).check(route("openai_compatible", "m", bad.url + "/v1", "TEST_KEY"))
        assert not ok and "401" in found
    finally:
        bad.close()


def test_runner_not_present_not_registered_and_registered(tmp_path, monkeypatch):
    monkeypatch.setenv("VASH_RUNNER_DIR", str(tmp_path / "actions-runner"))
    assert Actions.runner_status()[0] is None
    (tmp_path / "actions-runner").mkdir()
    (tmp_path / "actions-runner" / "config.sh").write_text("")
    ok, found, fix = Actions.runner_status()
    assert ok is False and "not registered" in found and "config.sh --url" in fix
    (tmp_path / "actions-runner" / ".runner").write_text(json.dumps({"gitHubUrl": "https://github.com/o/r"}))
    ok, found, fix = Actions.runner_status()
    assert "https://github.com/o/r" in found  # running or not depends on this machine's systemd


def test_doctor_outside_a_project_checks_what_init_would_use(tmp_path, monkeypatch, capsys):
    srv = Server(models=("qwen2.5-coder:7b",))
    monkeypatch.setenv("OLLAMA_HOST", srv.url)
    monkeypatch.setenv("VASH_RUNNER_DIR", str(tmp_path / "none"))
    try:
        code = doctor.run(tmp_path)
    finally:
        srv.close()
    out = capsys.readouterr().out
    assert "not in a project" in out and "Model route local (intake, coder, fallback)" in out
    assert "qwen2.5-coder:7b ready" in out
    assert code in (0, 1)  # 1 only when git is missing here


def test_doctor_fails_and_says_how_when_the_model_is_down(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("OLLAMA_HOST", "http://127.0.0.1:9")
    monkeypatch.setenv("VASH_RUNNER_DIR", str(tmp_path / "none"))
    assert doctor.run(tmp_path) == 1
    out = capsys.readouterr().out
    assert "[FAIL] Model route local" in out and "fix: sudo systemctl start ollama" in out


@pytest.mark.parametrize("path", ["scaffold/project/project-stack.json", "project-stack.json"])
def test_local_model_gets_time_to_answer_on_a_cpu(path):
    """A 7B model on 4 Arm cores needs minutes for a code answer; 60 seconds made the first task time out."""
    from vash.core.paths import vash_root
    routes = json.loads((vash_root() / path).read_text())["models"]["routes"]
    assert all(r["timeout_s"] >= 600 for r in routes.values() if r["adapter"] == "ollama")
