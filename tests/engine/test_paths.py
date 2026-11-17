from pathlib import Path

from vash.core import paths


def _fake_install(tmp_path: Path) -> Path:
    core = tmp_path / "site" / "vash" / "core"
    core.mkdir(parents=True)
    return core / "paths.py"


def test_vash_home_wins(tmp_path, monkeypatch):
    monkeypatch.setenv("VASH_HOME", str(tmp_path))
    assert paths.vash_root() == tmp_path.resolve()


def test_installed_data_used_without_vash_home(tmp_path, monkeypatch):
    monkeypatch.delenv("VASH_HOME", raising=False)
    fake = _fake_install(tmp_path)
    data = tmp_path / "site" / "vash" / "_data"
    data.mkdir()
    monkeypatch.setattr(paths, "__file__", str(fake))
    assert paths.vash_root() == data


def test_project_pyproject_is_not_taken_for_vash(tmp_path, monkeypatch):
    monkeypatch.delenv("VASH_HOME", raising=False)
    fake = _fake_install(tmp_path)
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'other'\n")
    monkeypatch.setattr(paths, "__file__", str(fake))
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    assert paths.vash_root() == elsewhere
    (tmp_path / "method").mkdir()
    assert paths.vash_root() == tmp_path.resolve()


def test_vash_commit_from_pips_record_of_a_git_install(monkeypatch, tmp_path):
    import importlib.metadata
    from vash.core import paths
    sha = "719ec2cf0b9ea37c8879f301427419f73fbf898f"

    class Dist:
        def read_text(self, name):
            return '{"url": "https://github.com/o/r.git", "vcs_info": {"vcs": "git", "commit_id": "%s"}}' % sha
    monkeypatch.setattr(importlib.metadata, "distribution", lambda name: Dist())
    assert paths.vash_commit() == sha


def test_vash_commit_is_to_verify_when_nothing_tells(monkeypatch, tmp_path):
    import importlib.metadata
    from vash.core import paths

    class Dist:
        def read_text(self, name):
            return None  # a wheel from a release page records no commit
    monkeypatch.setattr(importlib.metadata, "distribution", lambda name: Dist())
    monkeypatch.setenv("VASH_HOME", str(tmp_path))  # not a git checkout
    assert paths.vash_commit() == "to-verify"
