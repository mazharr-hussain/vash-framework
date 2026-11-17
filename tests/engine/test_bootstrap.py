"""bootstrap/oci-cloudshell.sh picks which VASH to install: the newest release, a named version, or main."""
import stat
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "bootstrap" / "oci-cloudshell.sh"


def _exe(path: Path, text: str) -> None:
    path.write_text("#!/bin/bash\n" + text)
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


def run(tmp_path: Path, *args: str, release: str | None = "v3.1.0", env: dict | None = None) -> tuple[str, str, str]:
    """Run the script with stand-ins for curl, pip and vash; return (its output, what pip installed, vash's args)."""
    home, stubs = tmp_path / "home", tmp_path / "stubs"
    venv_bin = home / ".vash" / "venv" / "bin"
    venv_bin.mkdir(parents=True)
    stubs.mkdir()
    _exe(venv_bin / "pip", f'[ "$1" = install ] && echo "${{@: -1}}" > "{tmp_path}/installed"\nexit 0\n')
    _exe(venv_bin / "vash", f'echo "$*" > "{tmp_path}/vash-args"\necho "$VASH_SOURCE" > "{tmp_path}/vash-source"\n')
    answer = f'{{"tag_name": "{release}", "name": "x"}}' if release else ""
    _exe(stubs / "curl", f"echo '{answer}'\n" + ("" if release else "exit 22\n"))
    full_env = {"HOME": str(home), "PATH": f"{stubs}:/usr/bin:/bin", "VASH_TTY": "/dev/null", **(env or {})}
    out = subprocess.run(["bash", str(SCRIPT), *args], env=full_env, stdin=subprocess.DEVNULL, capture_output=True,
                         text=True, check=False)
    assert out.returncode == 0, out.stderr
    read = lambda name: (tmp_path / name).read_text().strip() if (tmp_path / name).exists() else ""  # noqa: E731
    assert read("vash-source") == read("installed")  # the VM is built with the same VASH as this shell
    return out.stdout, read("installed"), read("vash-args")


REPO = "git+https://github.com/mazharr-hussain/vash-framework.git"


def test_default_is_the_newest_release_and_other_options_pass_through(tmp_path):
    out, installed, args = run(tmp_path, "--no-inventory", "--ocpus", "2")
    assert installed == f"{REPO}@v3.1.0" and "Installing VASH v3.1.0" in out
    assert args == "onboard oci --no-inventory --ocpus 2"


def test_a_named_version_and_the_dev_channel(tmp_path):
    _, installed, args = run(tmp_path / "a", "--version", "3.0.0", "--yes")
    assert installed == f"{REPO}@v3.0.0" and args == "onboard oci --yes"
    _, installed, args = run(tmp_path / "b", "--channel=dev")
    assert installed == f"{REPO}@main" and args == "onboard oci"


def test_without_any_release_it_says_so_and_installs_main(tmp_path):
    out, installed, _ = run(tmp_path, release=None)
    assert installed == f"{REPO}@main" and "No VASH release found" in out


def test_vash_source_set_by_hand_wins(tmp_path):
    _, installed, _ = run(tmp_path, env={"VASH_SOURCE": "git+https://example.org/fork.git@abc"})
    assert installed == "git+https://example.org/fork.git@abc"
