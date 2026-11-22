"""VASH's tools for a chat harness (MCP): projects, tasks, AvA runs in the background, safe names."""
import json
import sys
import time

import pytest

from vash.mcp import tools


@pytest.fixture
def projects(tmp_path, monkeypatch):
    monkeypatch.setenv("VASH_PROJECTS", str(tmp_path / "projects"))
    # `vash` for the tools: this checkout, through the interpreter running the tests
    monkeypatch.setattr(tools.shutil, "which", lambda name: None)
    return tmp_path / "projects"


def test_project_and_task_are_written_where_vash_expects_them(projects):
    assert "created" in tools.new_project("hello")
    assert tools.list_projects() == ["hello"]
    out = tools.new_task("hello", "T1", "code", "Write is_valid_iban.")
    assert "T1 (code)" in out
    assert (projects / "hello/audit/prompts/T1_prompt.md").read_text().startswith("type: code\n")


@pytest.mark.parametrize("project,task,kind", [("../etc", "T1", "code"), ("hello", "../x", "code"),
                                               ("hello", "T1", "shell"), ("/abs", "T1", "code")])
def test_names_and_kinds_are_checked(projects, project, task, kind):
    tools.new_project("hello")
    with pytest.raises(tools.ToolError):
        tools.new_task(project, task, kind, "x")


def test_a_task_runs_in_the_background_and_reports_its_result(projects, monkeypatch):
    tools.new_project("hello")
    tools.new_task("hello", "T1", "code", "Write add(a, b).")
    # stand-in for `vash ava`: writes the round log and the artifact like the real one
    fake = projects.parent / "fake_vash.py"
    fake.write_text(
        "import pathlib, sys, time\n"
        "time.sleep(0.5)\n"
        "pathlib.Path('audit/ava_logs').mkdir(parents=True, exist_ok=True)\n"
        "pathlib.Path('audit/artifacts').mkdir(parents=True, exist_ok=True)\n"
        "pathlib.Path('audit/ava_logs/T1_round1.md').write_text('**SCORE:** 93\\n**VERDICT:** APPROVED\\n')\n"
        "pathlib.Path('audit/artifacts/T1_artifact.txt').write_text('def add(a, b):\\n    return a + b\\n')\n"
        "print('Activity T1: APPROVED (score 93)')\n")
    monkeypatch.setattr(tools.shutil, "which", lambda name: str(fake))
    monkeypatch.setattr(tools.subprocess, "Popen", _python_popen(tools.subprocess.Popen))
    assert "started" in tools.run_task("hello", "T1")
    assert "running" in tools.task_status("hello", "T1") or "finished" in tools.task_status("hello", "T1")
    for _ in range(50):
        status = tools.task_status("hello", "T1")
        if "finished" in status:
            break
        time.sleep(0.1)
    assert "T1_round1.md: score 93, APPROVED" in status
    assert tools.read_result("hello", "T1").startswith("def add")
    assert "finished" in tools.list_tasks("hello")


def _python_popen(real):
    def popen(cmd, **kw):  # run the stand-in script with this interpreter
        return real([sys.executable, *cmd], **kw)
    return popen


def test_unknown_project_lists_the_ones_that_exist(projects):
    tools.new_project("alpha")
    with pytest.raises(tools.ToolError, match="Projects: alpha"):
        tools.run_task("beta", "T1")


def test_the_mcp_server_offers_the_tools():
    pytest.importorskip("mcp.server.mcpserver")
    import asyncio
    from vash.mcp.server import build
    names = [t.name for t in asyncio.run(build().list_tools())]
    assert names == ["list_projects", "new_project", "new_task", "run_task", "task_status", "read_result",
                     "list_tasks", "doctor", "gpu_quota", "gpu_run", "gpu_status", "gpu_result"]


def test_vm_setup_installs_the_chat_harness_wired_to_the_gateway_and_vash():
    from vash.core.paths import vash_root
    script = (vash_root() / "iac" / "oci" / "cloud-init" / "vash-runner.sh").read_text()
    start = script.index("cat > /etc/opencode/opencode.json <<'JSON'") + len("cat > /etc/opencode/opencode.json <<'JSON'")
    settings = json.loads(script[start:script.index("\nJSON\n", start)])
    assert settings["providers"]["vash"]["settings"]["baseURL"] == "http://127.0.0.1:4000/v1"
    assert settings["mcp"]["servers"]["vash"]["command"] == ["/usr/local/bin/vash", "mcp"]
    assert settings["model"] == "vash/vash-coding"
    assert '"@opencode/cli@$HARNESS_VERSION"' in script and 'pip install "mcp==$MCP_VERSION"' in script
