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

## Links
- [LICENSE](LICENSE)
- [GOVERNANCE](GOVERNANCE.md)
- [SECURITY](SECURITY.md)
- [CONTRIBUTING](CONTRIBUTING.md)
- [CODE_OF_CONDUCT](CODE_OF_CONDUCT.md)
- [CHANGELOG](CHANGELOG.md)
