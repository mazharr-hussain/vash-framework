"""VASH command line interface (C-15)."""
import sys
import argparse
from pathlib import Path
from typing import Sequence
from vash import __version__
from vash.core.exceptions import VashError, NotAvailableYet

def main(argv: Sequence[str] | None = None) -> int:
    """Run the VASH CLI."""
    parser = argparse.ArgumentParser(prog="vash", description="VASH Engine")
    parser.add_argument("--version", action="store_true", help="Show version")
    subparsers = parser.add_subparsers(dest="command")

    p_init = subparsers.add_parser("init", help="Create a project from the scaffold")
    p_init.add_argument("target", nargs="?", default=".")
    p_init.add_argument("--repo", type=Path, default=Path.cwd())
    p_check = subparsers.add_parser("check", help="Run Stage 0 checks")
    p_check.add_argument("--repo", type=Path, default=Path.cwd())
    p_load = subparsers.add_parser("load", help="Rebuild .claude/ and CLAUDE.md")
    p_load.add_argument("--repo", type=Path, default=Path.cwd())
    p_ava = subparsers.add_parser("ava", help="Run an AvA activity")
    p_ava.add_argument("task_id")
    p_ava.add_argument("--repo", type=Path, default=Path.cwd())
    p_cost = subparsers.add_parser("cost", help="Show cost meter status")
    p_cost.add_argument("--repo", type=Path, default=Path.cwd())
    p_status = subparsers.add_parser("status", help="Show freeze and audit status")
    p_status.add_argument("--repo", type=Path, default=Path.cwd())

    args = parser.parse_args(argv)

    if args.version:
        print(f"vash {__version__}")
        return 0

    if not args.command:
        parser.print_help()
        return 2

    try:
        if args.command == "init":
            from vash.cli.init import run
            return run(args.target, args.repo)
        elif args.command == "check":
            from vash.cli.check import run
            return run(args.repo)
        elif args.command == "load":
            from vash.cli.load import run
            return run(args.repo)
        elif args.command == "ava":
            from vash.cli.ava import run
            return run(args.repo, args.task_id)
        elif args.command == "cost":
            from vash.cli.cost import run
            return run(args.repo)
        elif args.command == "status":
            from vash.cli.status import run
            return run(args.repo)
    except NotAvailableYet as e:
        print(f"Error: {e}")
        return 0
    except VashError as e:
        print(f"Error: {e}")
        return e.exit_code

    return 2

def cli() -> None:
    """Entry point for the vash command."""
    sys.exit(main())
