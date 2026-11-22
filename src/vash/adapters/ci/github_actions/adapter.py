"""GitHub Actions CI adapter over the REST API."""
import json
import os
import time
import urllib.request
import urllib.error
import urllib.parse
from typing import Any, Mapping, Sequence, Callable
from pathlib import Path
from vash.core.interfaces import CIAdapter, RunRef, RunResult
from vash.core.exceptions import VashError, RouteUnavailable

class Adapter(CIAdapter):
    """GitHub Actions CI adapter."""
    def __init__(self, settings: Mapping[str, Any]):
        super().__init__(settings)
        self.repo = self.settings.get("repo", "")
        self.timeout_s = int(self.settings.get("timeout_s", 30))
        self.base_url = "https://api.github.com"
        if not self.repo or "/" not in self.repo:
            raise VashError(
                f"Invalid or missing repo setting: {self.repo}",
                "Set ci.settings.repo to 'owner/name'"
            )

    def _request(self, method: str, path: str, data: dict | None = None) -> Any:
        token = os.environ.get("GITHUB_TOKEN", "")
        if not token:
            raise RouteUnavailable(
                "GITHUB_TOKEN environment variable is missing",
                "Set GITHUB_TOKEN to a valid personal access token"
            )
        url = f"{self.base_url}{path}"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "VASH-Engine"
        }
        req_data = json.dumps(data).encode("utf-8") if data else None
        req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as response:
                if response.status == 204:
                    return None
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise VashError(
                f"GitHub Actions API error {e.code}: {body}",
                "Check API limits or token permissions"
            )
        except (urllib.error.URLError, TimeoutError) as e:
            raise RouteUnavailable(
                f"GitHub Actions connection failed: {e}",
                "Check network connection"
            )
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            raise VashError(
                f"Invalid JSON response from GitHub Actions: {e}",
                "The API may be degraded"
            )

    def start_run(self, workflow: str, ref: str, inputs: Mapping[str, str], sleep_fn: Callable[[float], None] = time.sleep) -> RunRef:
        created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        data = {"ref": ref, "inputs": dict(inputs)}
        self._request("POST", f"/repos/{self.repo}/actions/workflows/{workflow}/dispatches", data)

        for _ in range(10):
            sleep_fn(2)
            params = {
                "event": "workflow_dispatch",
                "branch": ref,
                "created": f">={created_at}",
                "per_page": "1"
            }
            query = urllib.parse.urlencode(params)
            res = self._request("GET", f"/repos/{self.repo}/actions/workflows/{workflow}/runs?{query}")

            if res and "workflow_runs" in res and len(res["workflow_runs"]) > 0:
                run = res["workflow_runs"][0]
                return RunRef(run_id=str(run["id"]), url=run["html_url"])

        raise VashError(
            "Could not find the dispatched run after 10 attempts",
            "Check the workflow name and the repository permissions"
        )

    def get_run(self, run_id: str) -> RunResult:
        res = self._request("GET", f"/repos/{self.repo}/actions/runs/{run_id}")
        if not res:
            raise VashError(f"Run {run_id} not found", "Check run ID")
        return RunResult(
            run_id=str(res["id"]), status=res["status"], conclusion=res.get("conclusion"),
            url=res["html_url"]
        )

    def register_runner(self, labels: Sequence[str]) -> str | None:
        data = {"name": "vash-runner", "labels": list(labels)}
        res = self._request("POST", f"/repos/{self.repo}/actions/runners/registration-token", data)
        if res and "token" in res:
            return res["token"]
        return None

    def install_hooks(self, repo_root: Path) -> list[Path]:
        return []

    @classmethod
    def runner_status(cls) -> tuple[bool | None, str, str]:
        """The self-hosted runner on this machine: its files, its registration and its service."""
        import subprocess
        home = Path(os.environ.get("VASH_RUNNER_DIR", str(Path.home() / "actions-runner")))
        if not (home / "config.sh").exists():
            return None, "no runner files on this machine", ""
        if not (home / ".runner").exists():
            return False, f"runner files in {home}, not registered", (
                "Repository Settings, Actions, Runners, New self-hosted runner: copy the token, then "
                f"cd {home} && ./config.sh --url https://github.com/<owner>/<repo> --token <TOKEN> "
                "--labels self-hosted,vash --unattended && sudo ./svc.sh install && sudo ./svc.sh start")
        try:
            repo = json.loads((home / ".runner").read_text(encoding="utf-8-sig")).get("gitHubUrl", "")
        except (ValueError, OSError):
            repo = ""
        try:
            out = subprocess.run(["systemctl", "list-units", "--type=service", "--all", "--no-legend",
                                  "--plain", "actions.runner.*"], capture_output=True, text=True, check=False)
            units = [line.split()[0] for line in out.stdout.splitlines() if line.strip()]
            active = [u for u in units if subprocess.run(["systemctl", "is-active", "--quiet", u],
                                                         check=False).returncode == 0]
        except (FileNotFoundError, IndexError):
            units, active = [], []
        if not active:
            return False, f"registered for {repo or 'a repository'}, but its service is not running", (
                f"cd {home} && sudo ./svc.sh install && sudo ./svc.sh start")
        return True, f"registered for {repo or 'a repository'}, service running", ""
