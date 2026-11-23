"""VASH adapter interfaces (C-03)."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence, Mapping, Any


@dataclass(frozen=True)
class IssueRef:
    number: int
    title: str
    url: str
    state: str
    labels: tuple[str, ...]


@dataclass(frozen=True)
class BoardItem:
    item_id: str
    title: str
    status: str
    issue_number: int | None


@dataclass(frozen=True)
class PullRequestRef:
    number: int
    url: str
    head: str
    base: str
    state: str


@dataclass(frozen=True)
class RunRef:
    run_id: str
    url: str


@dataclass(frozen=True)
class RunResult:
    run_id: str
    status: str
    conclusion: str | None
    url: str


@dataclass(frozen=True)
class CloudPlan:
    environment: str
    summary: str
    changes: int


@dataclass(frozen=True)
class VersionCheck:
    tool: str
    expected: str
    found: str | None
    ok: bool


@dataclass(frozen=True)
class RouteSettings:
    name: str
    adapter: str
    model: str
    vendor: str
    base_url: str | None
    key_env: str | None
    timeout_s: int


@dataclass(frozen=True)
class LLMReply:
    text: str
    route: str
    model: str
    degraded: bool
    usage: Mapping[str, int]


class ForgeAdapter(ABC):
    def __init__(self, settings: Mapping[str, Any]):
        self.settings = settings

    @abstractmethod
    def create_issue(self, title: str, body: str, labels: Sequence[str]) -> IssueRef: pass
    @abstractmethod
    def list_issues(self, state: str = "open", labels: Sequence[str] = ()) -> list[IssueRef]: pass
    @abstractmethod
    def read_board(self, board: str) -> list[BoardItem]: pass
    @abstractmethod
    def open_pr(self, head: str, base: str, title: str, body: str) -> PullRequestRef: pass
    @abstractmethod
    def merge_pr(self, number: int, method: str = "squash") -> None: pass
    @abstractmethod
    def export_status(self) -> dict[str, Any]: pass


class CIAdapter(ABC):
    def __init__(self, settings: Mapping[str, Any]):
        self.settings = settings

    @abstractmethod
    def start_run(self, workflow: str, ref: str, inputs: Mapping[str, str]) -> RunRef: pass
    @abstractmethod
    def get_run(self, run_id: str) -> RunResult: pass
    @abstractmethod
    def register_runner(self, labels: Sequence[str]) -> str | None: pass
    @abstractmethod
    def install_hooks(self, repo_root: Path) -> list[Path]: pass

    @classmethod
    def runner_status(cls) -> tuple[bool | None, str, str]:
        """(ok, what was found, how to fix) for a runner on this machine; ok None when none is set up here."""
        return None, "no runner check for this CI", ""


class CloudAdapter(ABC):
    """Cloud adapter.

    apply() and destroy() raise FreezeInvalid with a fix text when
    approved is False (C-03).
    """
    def __init__(self, settings: Mapping[str, Any]):
        self.settings = settings

    @abstractmethod
    def plan(self, environment: str) -> CloudPlan: pass
    @abstractmethod
    def apply(self, environment: str, approved: bool) -> dict[str, Any]: pass
    @abstractmethod
    def destroy(self, environment: str, approved: bool) -> None: pass
    @abstractmethod
    def outputs(self, environment: str) -> dict[str, Any]: pass


class LLMAdapter(ABC):
    def __init__(self, settings: Mapping[str, Any]):
        self.settings = settings

    @abstractmethod
    def reply(self, prompt: str, route: RouteSettings) -> LLMReply: pass

    def check(self, route: RouteSettings) -> tuple[bool, str, str]:
        """(ok, what was found, how to fix) for the route now, without spending tokens (`vash doctor`)."""
        return True, "not checked by this adapter", ""


class StackPack(ABC):
    """Stack pack (C-03)."""
    def __init__(self, settings: Mapping[str, Any]):
        self.settings = settings

    @abstractmethod
    def manifest(self) -> dict[str, Any]: pass
    @abstractmethod
    def check_versions(self) -> list[VersionCheck]: pass
    @abstractmethod
    def outputs_layout(self) -> list[str]: pass


class GPUAdapter(ABC):
    """A free GPU that runs batch jobs (no server is exposed): a model over a list of prompts, answers saved."""

    def __init__(self, settings: Mapping[str, Any]):
        self.settings = settings

    @abstractmethod
    def quota(self) -> dict[str, Any]:
        """{used_hours, total_hours, resets} of this week's free GPU time."""

    @abstractmethod
    def submit(self, name: str, model: str, prompts: list[str]) -> str:
        """Start a job that runs the model over the prompts; returns its reference."""

    @abstractmethod
    def status(self, ref: str) -> str:
        """The job's state as the provider reports it (queued, running, complete, error ...)."""

    @abstractmethod
    def fetch(self, ref: str, dest: Path) -> Path:
        """Download the answers (results.jsonl) into dest; returns the file."""


class WebAccessAdapter(ABC):
    """A public address for a page that runs only on the VM's own interface: the VM connects out to the provider
    (no port is opened), and the provider lets in only the owner's e-mail addresses."""

    def __init__(self, settings: Mapping[str, Any]):
        self.settings = settings

    @abstractmethod
    def publish(self, hostname: str, service: str, emails: list[str]) -> dict[str, Any]:
        """Make or update the address `hostname` for the `service` on the VM (e.g. http://127.0.0.1:8080), open to
        `emails` only. Idempotent. Returns {connector_token, url, created: [what was made]}."""

    @abstractmethod
    def unpublish(self, hostname: str) -> list[str]:
        """Remove what publish made for `hostname`; returns what was removed."""


CATEGORY_INTERFACES = {
    "forge": ForgeAdapter,
    "ci": CIAdapter,
    "cloud": CloudAdapter,
    "llm": LLMAdapter,
    "gpu": GPUAdapter,
    "web": WebAccessAdapter,
}
