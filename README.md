# VASH - Virtual AI Software House

VASH is a technology-independent framework designed to run an AI-driven software house. It uses a strict Agent vs Agent (AvA) protocol, deterministic gates, and $0-cost technology adapters.

**Status:** 🚧 Under Construction. Nothing is installable yet.

## How changes reach `main`

`main` is protected by a ruleset: every change goes through a pull request, nothing is force-pushed or
deleted, and these checks must pass before the merge button turns active.

| Check | Workflow | What it does |
|---|---|---|
| `test` | `ci.yml` | the test suite, including an end-to-end run of the engine |
| `gate1` | `ci.yml` | Gate 1, VASH's own deterministic checks |
| `stage0` | `ci.yml` | the project and catalog checks (`vash check`) |
| `terraform` | `ci.yml` | `init`, `validate` and offline plan tests of the OCI Terraform |
| `Checks without AI` | `pr-review.yml` | ruff, bandit, pip-audit, detect-secrets, actionlint |
| `New dependencies (GitHub dependency review)` | `pr-review.yml` | new dependencies with known vulnerabilities |
| CodeQL | repository setting | GitHub's code scanning |

An AI review (`pr-review.yml`) then posts one advisory comment when the `GEMINI_API_KEY` secret is set.

## Versions: live, test and dev

| Track | What it is | How to install |
|---|---|---|
| Live | the newest full GitHub release, e.g. `v3.1.0` | the bootstrap command as it is (the default, or `--channel live`) |
| Test | the newest release of any kind, including pre-releases such as `v3.2.0-rc.1` | add `--channel test` |
| Dev | whatever is on `main` now | add `--channel dev` |
| A named release | any release, e.g. to go back | add `--version v3.0.0` |

How a version is published (`.github/workflows/release.yml` checks the tag, tests, builds and publishes it):

- **Test:** set the next version in `pyproject.toml` (for example `3.2.0`), merge to `main`, then on github.com go to
  Releases, "Draft a new release", create the tag `v3.2.0-rc.1` on `main`, tick "Set as a pre-release" and publish.
  Each fix after that is `v3.2.0-rc.2`, `-rc.3` and so on. A `-rc` tag is always published as a pre-release, so the
  live track never picks it.
- **Live:** when the test version is good, publish the tag `v3.2.0` (same version, no `-rc`) as a normal release.
  It becomes the default install.
- **Dev:** nothing to publish; every merge to `main` is the dev version.

The VM that onboarding builds gets the same VASH as the shell that built it, and its tools are pinned too (Ollama,
the GitHub Actions runner with its checksum).

## Links
- [LICENSE](LICENSE)
- [GOVERNANCE](GOVERNANCE.md)
- [SECURITY](SECURITY.md)
- [CONTRIBUTING](CONTRIBUTING.md)
- [CODE_OF_CONDUCT](CODE_OF_CONDUCT.md)
- [CHANGELOG](CHANGELOG.md)
