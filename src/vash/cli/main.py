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
    p_doctor = subparsers.add_parser("doctor", help="Check that everything VASH needs here works; says how to fix it")
    p_doctor.add_argument("--repo", type=Path, default=Path.cwd())
    p_gw = subparsers.add_parser("gateway", help="The model gateway on this machine")
    gw_sub = p_gw.add_subparsers(dest="action", required=True)
    p_gwc = gw_sub.add_parser("config", help="Write the gateway's settings: a model per kind of work, with fallbacks")
    p_gwa = gw_sub.add_parser("add", help="Add any model the gateway supports to a kind of work (provider/model)")
    p_gwa.add_argument("kind", help="coding, test, docs, prompt or review")
    p_gwa.add_argument("model", help="provider/model as the gateway names it, e.g. together_ai/meta-llama/...")
    p_gwa.add_argument("--maker", required=True, help="Who made the model (rule R4 compares makers), e.g. meta")
    p_gwa.add_argument("--key-env", default="", help="Environment variable of the provider's key, if new")
    p_gwa.add_argument("--paid", action="store_true", help="The provider is not in the free list: accept its cost")
    p_gwa.add_argument("--first", action="store_true", help="Put it ahead of the catalog's models of that kind")
    p_gwa.add_argument("--extra", default="/etc/vash/gateway-models.json")
    p_gwc.add_argument("--out", default="/etc/vash/gateway.yaml")
    p_gwc.add_argument("--env", default="/etc/vash/gateway.env", help="File with the provider keys (KEY=value)")
    p_gwc.add_argument("--vm-model", default="", help="The model on this machine, the last fallback")
    p_gwc.add_argument("--extra", default="/etc/vash/gateway-models.json", help="The owner's added models")
    subparsers.add_parser("mcp", help="Serve VASH's tools to a chat harness over MCP (stdio)")
    p_gpu = subparsers.add_parser("gpu", help="Batch jobs on free GPUs, within their free quota")
    gpu_sub = p_gpu.add_subparsers(dest="action", required=True)
    p_gq = gpu_sub.add_parser("quota", help="This week's free GPU hours")
    p_gq.add_argument("--provider")
    p_gr = gpu_sub.add_parser("run", help="Run a model over a file of prompts on a free GPU")
    p_gr.add_argument("name", help="A short name for the job")
    p_gr.add_argument("--model", required=True, help="Model to run, e.g. qwen2.5-coder:32b")
    p_gr.add_argument("--prompts", type=Path, required=True, help="One prompt per line, or JSON lines with 'prompt'")
    p_gr.add_argument("--no-client-data", action="store_true", help="Confirm the prompts hold no client data")
    p_gr.add_argument("--provider")
    p_gs = gpu_sub.add_parser("status", help="State of the GPU jobs")
    p_gs.add_argument("name", nargs="?")
    p_gres = gpu_sub.add_parser("result", help="Download a job's answers")
    p_gres.add_argument("name")
    p_gres.add_argument("--dest", type=Path, default=Path.home() / ".vash" / "gpu" / "results")
    p_status = subparsers.add_parser("status", help="Show freeze and audit status")
    p_status.add_argument("--repo", type=Path, default=Path.cwd())
    for kind in ("skill", "agent"):
        p_kind = subparsers.add_parser(kind, help=f"Create or check {kind}s (portable, Agent Skills standard)")
        kind_sub = p_kind.add_subparsers(dest="action", required=True)
        p_new = kind_sub.add_parser("new", help=f"Create a {kind} from the template")
        p_new.add_argument("name")
        p_new.add_argument("--description", required=True, help="What it does and when to use it")
        p_new.add_argument("--searched", default="to-record", help="LAW 3: what was searched first")
        p_new.add_argument("--catalog", action="store_true", help="Create it in the VASH catalog, not the project")
        p_new.add_argument("--repo", type=Path, default=Path.cwd())
        p_val = kind_sub.add_parser("validate", help="Validate every skill and agent")
        p_val.add_argument("--repo", type=Path, default=Path.cwd())
        if kind == "skill":
            p_sug = kind_sub.add_parser("suggest", help="Rule R15: propose skills for repeated work")
            p_sug.add_argument("--repo", type=Path, default=Path.cwd())
            p_sug.add_argument("--min", type=int, default=3, help="Repetitions that make a skill")
            p_sug.add_argument("--similarity", type=float, default=0.8)
            p_sug.add_argument("--open-issues", action="store_true", help="Open one issue per proposal")
            p_sug.add_argument("--label", action="append", help="Label for the opened issues")
    p_onboard = subparsers.add_parser("onboard", help="Create a cloud runner VM with VASH installed")
    p_onboard.add_argument("cloud", help="Cloud adapter id from the catalog")
    p_onboard.add_argument("--down", action="store_true", help="Remove what onboarding created")
    p_onboard.add_argument("--status", action="store_true",
                           help="Show the setup running in the cloud's job service: its state, last log lines, the VM")
    p_onboard.add_argument("--resume", action="store_true",
                           help="Run the setup again (no capacity: next availability domain, then a smaller VM)")
    p_onboard.add_argument("--update", action="store_true",
                           help="Install this VASH on the VM again over SSH, then run the health check and a first task")
    p_onboard.add_argument("--keys", action="store_true",
                           help="Give the model provider keys once: kept in the vault, installed in the VM's gateway")
    p_onboard.add_argument("--chat", action="store_true",
                           help="Open the chat on the VM: a harness that talks to VASH and uses its models")
    p_onboard.add_argument("--in-shell", action="store_true",
                           help="Run terraform in this shell step by step instead of in the cloud's job service")
    p_onboard.add_argument("--yes", action="store_true", help="Do not ask before creating or removing")
    p_onboard.add_argument("--runner-repo", help="owner/name: register a self-hosted CI runner for it")
    p_onboard.add_argument("--admin-cidr", help="CIDR allowed to SSH (default: this shell's IP/32)")
    p_onboard.add_argument("--compartment", help="Compartment name; when missing: default vash after a yes, else typed; created only after a yes")
    p_onboard.add_argument("--cleanup-only", action="store_true", help="Only list and delete existing objects; no VM setup")
    p_onboard.add_argument("--no-inventory", action="store_true", help="Skip the list of existing compartments, VCNs and subnets")
    p_onboard.add_argument("--name-prefix", help="Prefix of new object names, e.g. north; when missing: default vash after a yes, else typed")
    p_onboard.add_argument("--vm-ip", help="Install on this existing VM instead of creating one")
    p_onboard.add_argument("--ssh-user", help="SSH user of the existing VM (default ubuntu)")
    p_onboard.add_argument("--ssh-key", help="Private key for the existing VM (default ~/.ssh/id_rsa)")
    p_onboard.add_argument("--notify-email", help="E-mail told when the VM is made, VASH is ready, or setup fails; '' for none")
    p_onboard.add_argument("--guardrails-only", action="store_true",
                           help="Only apply the free-tier guardrails (quota policy that allows Always Free amounts only, and a budget e-mail)")
    p_onboard.add_argument("--no-vault", action="store_true", help="Skip choosing the vault and key for VASH's secrets")
    p_onboard.add_argument("--database", action="store_true",
                           help="Also create an Always Free Autonomous Database <prefix>-db (password kept in the vault)")
    p_onboard.add_argument("--database-only", action="store_true",
                           help="Only the compartment, the vault and the database: no VM is made or changed")
    p_onboard.add_argument("--network-compartment", default=None,
                           help="Compartment for a new network (default 'network', asked; an existing one is reused)")
    p_onboard.add_argument("--subnet-id", help="Existing public subnet to use; no network is created")
    p_onboard.add_argument("--ocpus", type=int, default=2)
    p_onboard.add_argument("--memory", type=int, default=12, help="GB of memory")
    p_onboard.add_argument("--os-version", default="24.04")
    p_onboard.add_argument("--model", default="qwen2.5-coder:7b", help="Model to pull on the VM")
    p_onboard.add_argument("--shape", choices=("auto", "a1", "micro"), default="auto",
                           help="VM shape: auto (the asked Arm A1 size, else a basic 1-core 6 GB A1, else the AMD "
                                "Micro, each after a yes), a1 (Arm only) or micro (AMD E2.1.Micro, 1 GB, no model on the VM)")
    p_onboard.add_argument("--workdir", help="Where the terraform state is kept")

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
        elif args.command == "gateway":
            from vash.adapters.llm import gateway_add, gateway_command
            if args.action == "add":
                return gateway_add(args.kind, args.model, args.maker, args.key_env, args.paid, args.first,
                                   args.extra)
            return gateway_command(args.out, args.env, args.vm_model, args.extra)
        elif args.command == "mcp":
            from vash.mcp.server import run as serve
            return serve()
        elif args.command == "gpu":
            from vash.tools import gpu
            if args.action == "quota":
                return gpu.quota(args.provider)
            if args.action == "run":
                return gpu.run(args.name, args.model, args.prompts, args.no_client_data, args.provider)
            if args.action == "status":
                return gpu.status(args.name)
            return gpu.result(args.name, args.dest)
        elif args.command == "doctor":
            from vash.tools.doctor import run as doctor
            return doctor(args.repo)
        elif args.command in ("skill", "agent"):
            from vash.cli import skill as skill_cli
            if args.action == "new":
                return skill_cli.new_skill(args) if args.command == "skill" else skill_cli.new_agent(args)
            if args.action == "validate":
                return skill_cli.validate(args)
            return skill_cli.suggest(args)
        elif args.command == "onboard":
            from vash.cli.onboard import run
            return run(args)
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
