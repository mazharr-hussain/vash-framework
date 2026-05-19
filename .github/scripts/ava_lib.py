#!/usr/bin/env python3
"""
VASH 3.0 — AvA Library v3
4-call design: PE-Jr → Jr → PE-Sr → Sr
Each call uses tiny CLI prompt (~200-500 chars)
Claude reads all files from git itself
State tracks last completed call — resume from failure point
LAW 1: Python stdlib only
LAW 2: Fully automated
LAW 3: Standard patterns
"""

import os
import re
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone


# ─────────────────────────────────────────────
# class Files — all file operations
# ─────────────────────────────────────────────
class Files:
    def __init__(self, repo_root: Path):
        self.root = repo_root

    def read(self, path: str) -> str:
        try:
            return (self.root / path).read_text(encoding="utf-8")
        except Exception:
            return ""

    def write(self, path: str, content: str) -> None:
        full = self.root / path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")

    def exists(self, path: str) -> bool:
        return (self.root / path).exists()

    def size(self, path: str) -> int:
        try:
            return (self.root / path).stat().st_size
        except Exception:
            return 0

    def delete(self, path: str) -> None:
        try:
            (self.root / path).unlink()
        except Exception:
            pass

    def get_activity(self, task_id: str) -> str:
        content = self.read("knowledge/activity_list.md")
        pattern = rf"ID: {re.escape(task_id)}\n(.*?)(?=\n---|\Z)"
        m = re.search(pattern, content, re.DOTALL)
        return m.group(0) if m else ""

    def get_threshold(self, task_id: str) -> int:
        m = re.search(r"THRESHOLD:\s*(\d+)", self.get_activity(task_id))
        return int(m.group(1)) if m else 88

    def get_output_path(self, task_id: str) -> str:
        m = re.search(r"OUTPUT_PATH:\s*(.+)", self.get_activity(task_id))
        return m.group(1).strip() if m else ""

    def update_activity_status(self, task_id: str, status: str) -> None:
        content = self.read("knowledge/activity_list.md")
        tid = re.escape(task_id)
        updated = re.sub(
            rf"(ID: {tid}.*?STATUS:)\s*\w+",
            rf"\1 {status}", content, flags=re.DOTALL
        )
        self.write("knowledge/activity_list.md", updated)

    def save_artifact(self, task_id: str, content: str) -> None:
        tid = task_id.replace(".", "-")
        self.write(f"runtime/artifacts/{tid}_artifact.md", content)
        output_path = self.get_output_path(task_id)
        # Skip if output_path is a directory, invalid, or not a file target
        if (output_path and
                output_path not in ("N/A", "Multiple files") and
                not output_path.endswith("/") and
                not (self.root / output_path).is_dir()):
            self.write(output_path, content)

    def save_ava_log(self, task_id: str, round_num: int, content: str) -> None:
        tid = task_id.replace(".", "-")
        ts = datetime.now(timezone.utc).isoformat()
        log = f"# AvA Log — Activity {task_id} Round {round_num}\nTimestamp: {ts}\n\n{content}"
        self.write(f"runtime/ava_logs/{tid}_round{round_num}.md", log)

    def save_summary(self, task_id: str, content: str) -> None:
        self.write(
            f"runtime/validation/{task_id.replace('.', '-')}_summary.md",
            content
        )


# ─────────────────────────────────────────────
# class State — tracks which call completed
# ─────────────────────────────────────────────
class State:
    # Call numbers
    CALL_NONE   = 0
    CALL_PE_JR  = 1  # Prompt Engineer generates Junior prompt
    CALL_JR     = 2  # Junior generates artifact
    CALL_PE_SR  = 3  # Prompt Engineer generates Senior prompt
    CALL_SR     = 4  # Senior reviews artifact

    def __init__(self, files: Files):
        self.files = files

    def _path(self, task_id: str) -> str:
        return f"runtime/ava_logs/{task_id.replace('.', '-')}_state.json"

    def load(self, task_id: str) -> dict:
        content = self.files.read(self._path(task_id))
        if content:
            try:
                return json.loads(content)
            except Exception:
                pass
        return {
            "task_id": task_id,
            "last_completed_call": self.CALL_NONE,
            "current_round": 1,
            "locked_sections": [],
            "failed_sections": [],
            "rounds_completed": 0,
            "last_updated": ""
        }

    def save(self, task_id: str, state: dict) -> None:
        state["last_updated"] = datetime.now(timezone.utc).isoformat()
        self.files.write(self._path(task_id), json.dumps(state, indent=2))

    def mark_call_complete(self, task_id: str, call_num: int) -> None:
        state = self.load(task_id)
        state["last_completed_call"] = call_num
        self.save(task_id, state)

    def get_resume_call(self, task_id: str) -> int:
        """Return the next call to run based on last completed."""
        state = self.load(task_id)
        last = state.get("last_completed_call", self.CALL_NONE)
        # If round completed (call 4 done) — next round starts from call 1 (Jr only)
        if last == self.CALL_SR:
            return self.CALL_JR  # round 2+ skips PE-Jr, Jr fixes based on Sr feedback
        return last + 1  # resume from next call

    def get_current_round(self, task_id: str) -> int:
        return self.load(task_id).get("current_round", 1)

    def get_locked_sections(self, task_id: str) -> list:
        return self.load(task_id).get("locked_sections", [])

    def get_failed_sections(self, task_id: str) -> list:
        return self.load(task_id).get("failed_sections", [])

    def update_after_sr(self, task_id: str, score: int,
                        locked: list, failed: list) -> None:
        state = self.load(task_id)
        state["last_completed_call"] = self.CALL_NONE  # reset for next round
        state["rounds_completed"] = state.get("rounds_completed", 0) + 1
        # current_round = next round number (rounds_completed is now incremented)
        state["current_round"] = state["rounds_completed"] + 1
        # Accumulate locked — never remove without human approval
        existing = {s["title"] for s in state["locked_sections"]}
        for s in locked:
            if s["title"] not in existing:
                state["locked_sections"].append(s)
        state["failed_sections"] = failed
        self.save(task_id, state)

    def reset(self, task_id: str) -> None:
        """Full reset — used when artifact is missing on round 2+."""
        tid = task_id.replace(".", "-")
        self.files.delete(self._path(task_id))
        for i in range(1, 10):
            self.files.delete(f"runtime/ava_logs/{tid}_round{i}.md")
        self.files.delete(f"runtime/artifacts/{tid}_artifact.md")
        self.files.delete(f"runtime/prompts/{tid}_jr_prompt.md")
        self.files.delete(f"runtime/prompts/{tid}_sr_prompt.md")


# ─────────────────────────────────────────────
# class Runner — calls Claude Code CLI
# Tiny prompts only — Claude reads files itself
# ─────────────────────────────────────────────
class Runner:

    def run(self, prompt: str) -> str:
        """
        Call Claude Code CLI with a small prompt.
        Claude reads all referenced files itself from the repo.
        Returns stdout output as string.
        """
        try:
            result = subprocess.run(
                ["claude", "-p", prompt],
                capture_output=True,
                text=True,
                timeout=300,
                env={
                    **os.environ,
                    "CLAUDE_CODE_OAUTH_TOKEN": os.environ.get(
                        "CLAUDE_CODE_OAUTH_TOKEN", ""
                    )
                }
            )
            output = result.stdout.strip()
            if not output and result.stderr:
                return f"ERROR: {result.stderr[:300]}"
            return output
        except subprocess.TimeoutExpired:
            return "ERROR: timeout"
        except FileNotFoundError:
            return "ERROR: claude CLI not found"
        except Exception as e:
            return f"ERROR: {e}"

    def failed(self, output: str) -> bool:
        return (
            not output or
            output.startswith("ERROR") or
            "hit your limit" in output.lower() or
            "rate limit" in output.lower()
        )

    def is_limit(self, output: str) -> bool:
        return "hit your limit" in output.lower()


# ─────────────────────────────────────────────
# class Parser — parses Senior output
# ─────────────────────────────────────────────
class Parser:

    def parse_score(self, text: str) -> int:
        m = re.search(r"SCORE:\s*(\d+)", text)
        return int(m.group(1)) if m else 0

    def parse_verdict(self, text: str) -> str:
        m = re.search(r"VERDICT:\s*(APPROVED|MODIFY|FAIL)", text)
        return m.group(1) if m else "FAIL"

    def parse_sections(self, text: str) -> tuple:
        locked, failed = [], []
        block = re.search(
            r"SECTION REVIEW:(.*?)(?=OBJECTIONS:|CORRECTIONS:|SCORE:|\Z)",
            text, re.DOTALL
        )
        if not block:
            return locked, failed
        for line in block.group(1).strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            if ": PASS" in line:
                locked.append({"title": line.split(": PASS")[0].strip(), "status": "PASS"})
            elif ": FAIL" in line:
                parts = line.split(": FAIL")
                reason = parts[1].strip(" —-") if len(parts) > 1 else ""
                failed.append({"title": parts[0].strip(), "status": "FAIL", "reason": reason})
        return locked, failed

    def parse_objections(self, text: str) -> list:
        m = re.search(r"OBJECTIONS:(.*?)(?=CORRECTIONS:|\Z)", text, re.DOTALL)
        if not m:
            return []
        block = m.group(1).strip()
        if not block or block.upper() == "NONE":
            return []
        return [l.strip() for l in block.split("\n") if l.strip() and l.strip().upper() != "NONE"]

    def parse_corrections(self, text: str) -> list:
        m = re.search(r"CORRECTIONS:(.*?)$", text, re.DOTALL)
        if not m:
            return []
        block = m.group(1).strip()
        if not block or block.upper() == "NONE":
            return []
        return [l.strip() for l in block.split("\n") if l.strip() and l.strip().upper() != "NONE"]

    def parse_all(self, text: str) -> dict:
        locked, failed = self.parse_sections(text)
        return {
            "score": self.parse_score(text),
            "verdict": self.parse_verdict(text),
            "locked_sections": locked,
            "failed_sections": failed,
            "objections": self.parse_objections(text),
            "corrections": self.parse_corrections(text),
        }


# ─────────────────────────────────────────────
# class Reporter — owner-facing summaries
# ─────────────────────────────────────────────
class Reporter:
    def __init__(self, files: Files):
        self.files = files

    def write_summary(self, task_id: str, score: int, verdict: str,
                      failed: list, objections: list, corrections: list) -> None:
        tid = task_id.replace(".", "-")
        threshold = self.files.get_threshold(task_id)
        ts = datetime.now(timezone.utc).isoformat()
        lines = [
            f"# YOUR REVIEW — Activity {task_id}",
            "",
            f"**Score:** {score}/100 (threshold: {threshold})",
            f"**Verdict:** {verdict}",
            f"**Artifact:** runtime/artifacts/{tid}_artifact.md",
            ""
        ]
        if failed:
            lines.append("**Sections Needing Improvement:**")
            for s in failed:
                lines.append(f"- {s['title']}: {s.get('reason', '')}")
            lines.append("")
        if objections:
            lines.append("**Specific Issues:**")
            for o in objections:
                lines.append(f"- {o}")
            lines.append("")
        if corrections:
            lines.append("**Required Corrections:**")
            for c in corrections:
                lines.append(f"- {c}")
            lines.append("")
        lines.append("**Your Decision:**")
        if verdict == "APPROVED":
            lines.append(f"- APPROVED {task_id}")
        elif verdict == "MODIFY":
            lines.append(f"- MODIFY {task_id}")
            lines.append(f"- REJECTED {task_id} [reason — if full rebuild needed]")
        else:
            lines.append(f"- REJECTED {task_id} [reason]")
        lines += ["", f"*Validated: {ts}*"]
        self.files.save_summary(task_id, "\n".join(lines))

    def write_error(self, task_id: str, call_num: int, error: str) -> None:
        call_names = {1: "PE-Jr", 2: "Junior", 3: "PE-Sr", 4: "Senior"}
        name = call_names.get(call_num, f"Call {call_num}")
        summary = (
            f"# YOUR REVIEW — Activity {task_id}\n\n"
            f"**Verdict:** FAIL\n\n"
            f"**Failed at:** {name} (call {call_num}/4)\n\n"
            f"**Error:** {error[:300]}\n\n"
            f"Next run will resume from call {call_num}.\n\n"
            f"- REJECTED {task_id} [reason]\n"
        )
        self.files.save_summary(task_id, summary)

    def write_limit(self, task_id: str, call_num: int, reset_time: str) -> None:
        call_names = {1: "PE-Jr", 2: "Junior", 3: "PE-Sr", 4: "Senior"}
        name = call_names.get(call_num, f"Call {call_num}")
        summary = (
            f"# YOUR REVIEW — Activity {task_id}\n\n"
            f"**Verdict:** RETRY\n\n"
            f"**Status:** Claude usage limit reached during {name} (call {call_num}/4)\n\n"
            f"**Reset time:** {reset_time}\n\n"
            f"Next run will resume from call {call_num} after reset.\n\n"
            f"No action needed — pipeline will continue automatically after reset.\n"
        )
        self.files.save_summary(task_id, summary)


# ─────────────────────────────────────────────
# class Orchestrator — main flow controller
# ─────────────────────────────────────────────
class Orchestrator:
    def __init__(self, repo_root: Path):
        self.files = Files(repo_root)
        self.state = State(self.files)
        self.parser = Parser()
        self.runner = Runner()
        self.reporter = Reporter(self.files)

    def log(self, msg: str) -> None:
        print(f"[VASH AvA] {msg}", flush=True)

    def run(self, task_id: str) -> str:
        if not task_id:
            self.log("ERROR: No TASK_ID")
            return "FAIL"

        resume_call = self.state.get_resume_call(task_id)
        round_num = self.state.get_current_round(task_id)
        tid = task_id.replace(".", "-")
        threshold = self.files.get_threshold(task_id)

        self.log(f"Activity: {task_id} | Round: {round_num} | Resume from call: {resume_call}")

        # CALL 1: Prompt Engineer generates Junior prompt
        if resume_call <= State.CALL_PE_JR:
            self.log("Call 1/4: Prompt Engineer generating Junior prompt...")
            result = self._call_pe_jr(task_id, round_num)
            if result != "OK":
                return result
            self.state.mark_call_complete(task_id, State.CALL_PE_JR)

        # CALL 2: Junior generates artifact
        if resume_call <= State.CALL_JR:
            self.log("Call 2/4: Junior generating artifact...")
            result = self._call_jr(task_id, round_num)
            if result != "OK":
                return result
            self.state.mark_call_complete(task_id, State.CALL_JR)

        # CALL 3: Prompt Engineer generates Senior prompt
        if resume_call <= State.CALL_PE_SR:
            self.log("Call 3/4: Prompt Engineer generating Senior prompt...")
            result = self._call_pe_sr(task_id, round_num)
            if result != "OK":
                return result
            self.state.mark_call_complete(task_id, State.CALL_PE_SR)

        # CALL 4: Senior reviews artifact
        if resume_call <= State.CALL_SR:
            self.log("Call 4/4: Senior reviewing artifact...")
            result = self._call_sr(task_id, round_num, threshold)
            if result != "OK":
                return result

        # All 4 calls complete — read result
        sr_output = self.files.read(f"runtime/ava_logs/{tid}_round{round_num}.md")
        parsed = self.parser.parse_all(sr_output)
        score = parsed["score"]
        verdict = parsed["verdict"]
        locked = parsed["locked_sections"]
        failed = parsed["failed_sections"]

        if score >= threshold:
            verdict = "APPROVED"

        for s in locked:
            s["locked_round"] = round_num

        self.state.update_after_sr(task_id, score, locked, failed)
        self.reporter.write_summary(
            task_id, score, verdict, failed,
            parsed["objections"], parsed["corrections"]
        )
        if verdict == "APPROVED":
            self.files.update_activity_status(task_id, "PASS")

        self.log(f"Round {round_num} complete: {verdict} ({score}/100)")
        return verdict

    # ── Individual call methods ──────────────────

    def _call_pe_jr(self, task_id: str, round_num: int) -> str:
        """CALL 1: PE generates Junior prompt and saves to git."""
        tid = task_id.replace(".", "-")
        locked = self.state.get_locked_sections(task_id)
        failed = self.state.get_failed_sections(task_id)

        locked_note = ""
        if locked:
            titles = ", ".join(s["title"] for s in locked)
            locked_note = f"Locked sections (Junior must preserve): {titles}"

        failed_note = ""
        if failed:
            items = "; ".join(f"{s['title']}: {s.get('reason','')}" for s in failed)
            failed_note = f"Failed sections from last round (Junior must fix): {items}"

        prompt = "\n".join([
            "You are VASH 3.0 Prompt Engineer.",
            f"Generate an optimal Junior Creator prompt for activity {task_id} round {round_num}.",
            "",
            "Read these files to understand the task:",
            "- knowledge/activity_list.md",
            "- knowledge/laws.md",
            "- knowledge/checklists/artifact.md",
            "",
            "The prompt you generate must:",
            "- Tell Junior exactly what artifact to produce",
            "- Tell Junior which files to read (not their content)",
            "- Say: output artifact text to stdout only, no file writes",
            "- Be clear and specific, under 1000 chars",
            locked_note,
            failed_note,
            "",
            "Output ONLY the prompt text to stdout.",
            "Do NOT write files. Do NOT ask for approval.",
        ])

        output = self.runner.run(prompt)

        if self.runner.is_limit(output):
            reset = re.search(r"resets (.+)", output)
            self.reporter.write_limit(task_id, State.CALL_PE_JR,
                                      reset.group(1) if reset else "unknown")
            return "RETRY"
        if self.runner.failed(output):
            self.reporter.write_error(task_id, State.CALL_PE_JR, output)
            return "FAIL"

        # Verify PE saved the prompt file
        if not self.files.exists(f"runtime/prompts/{tid}_jr_prompt.md"):
            # PE may have output the prompt instead of saving it
            # Save it ourselves from the output
            self.files.write(f"runtime/prompts/{tid}_jr_prompt.md", output)

        self.log(f"Junior prompt saved: runtime/prompts/{tid}_jr_prompt.md")
        return "OK"

    def _call_jr(self, task_id: str, round_num: int) -> str:
        """CALL 2: Junior reads prompt from git and generates artifact."""
        tid = task_id.replace(".", "-")
        prompt = "\n".join([
            "You are VASH 3.0 Junior Creator.",
            f"Read your task from: runtime/prompts/{tid}_jr_prompt.md",
            "",
            "Execute the task exactly as specified.",
            "Output ONLY the artifact text content to stdout.",
            "Do NOT write any files. Do NOT ask for approval.",
            "Do NOT include preamble, process notes, or wrappers.",
            "Start directly with the artifact content (e.g. # Title).",
        ])

        output = self.runner.run(prompt)

        if self.runner.is_limit(output):
            reset = re.search(r"resets (.+)", output)
            self.reporter.write_limit(task_id, State.CALL_JR,
                                      reset.group(1) if reset else "unknown")
            return "RETRY"
        if self.runner.failed(output):
            self.reporter.write_error(task_id, State.CALL_JR, output)
            return "FAIL"

        # Clean and save artifact
        clean = self._clean(output)
        self.files.save_artifact(task_id, clean)
        self.log(f"Artifact saved: {len(clean)} chars")
        return "OK"

    def _call_pe_sr(self, task_id: str, round_num: int) -> str:
        """CALL 3: PE generates Senior review prompt and saves to git."""
        tid = task_id.replace(".", "-")
        locked = self.state.get_locked_sections(task_id)
        locked_note = ""
        if locked:
            titles = "\n".join(f"- {s['title']}" for s in locked)
            locked_note = f"These sections are locked (carry forward as PASS):\n{titles}"

        prompt = "\n".join([
            "You are VASH 3.0 Prompt Engineer.",
            f"Generate an optimal Senior Validator prompt for activity {task_id} round {round_num}.",
            "",
            "Read these files to understand the task:",
            "- knowledge/activity_list.md",
            "- knowledge/laws.md",
            "- knowledge/checklists/artifact.md",
            f"- runtime/prompts/{tid}_jr_prompt.md",
            f"- runtime/artifacts/{tid}_artifact.md",
            "",
            "The prompt you generate must tell Senior to:",
            "- Read and review the artifact",
            "- Read the Junior prompt to understand intent",
            "- Score 0-100 against checklist and laws",
            "- Output in exact format: SCORE/VERDICT/SECTION REVIEW/OBJECTIONS/CORRECTIONS",
            "- Output to stdout only, no file writes",
            locked_note,
            "",
            "Output ONLY the prompt text to stdout.",
            "Do NOT write files. Do NOT ask for approval.",
        ])

        output = self.runner.run(prompt)

        if self.runner.is_limit(output):
            reset = re.search(r"resets (.+)", output)
            self.reporter.write_limit(task_id, State.CALL_PE_SR,
                                      reset.group(1) if reset else "unknown")
            return "RETRY"
        if self.runner.failed(output):
            self.reporter.write_error(task_id, State.CALL_PE_SR, output)
            return "FAIL"

        if not self.files.exists(f"runtime/prompts/{tid}_sr_prompt.md"):
            self.files.write(f"runtime/prompts/{tid}_sr_prompt.md", output)

        self.log(f"Senior prompt saved: runtime/prompts/{tid}_sr_prompt.md")
        return "OK"

    def _call_sr(self, task_id: str, round_num: int, threshold: int) -> str:
        """CALL 4: Senior reads prompt from git and reviews artifact."""
        tid = task_id.replace(".", "-")
        prompt = "\n".join([
            "You are VASH 3.0 Senior Validator.",
            f"Read your review task from: runtime/prompts/{tid}_sr_prompt.md",
            "",
            "Execute the review exactly as specified.",
            "Output ONLY the review in the specified format to stdout.",
            "Do NOT write any files. Do NOT ask for approval.",
        ])

        output = self.runner.run(prompt)

        if self.runner.is_limit(output):
            reset = re.search(r"resets (.+)", output)
            self.reporter.write_limit(task_id, State.CALL_SR,
                                      reset.group(1) if reset else "unknown")
            return "RETRY"
        if self.runner.failed(output):
            self.reporter.write_error(task_id, State.CALL_SR, output)
            return "FAIL"

        self.files.save_ava_log(task_id, round_num, output)
        self.state.mark_call_complete(task_id, State.CALL_SR)
        self.log(f"Senior review saved: round {round_num}")
        return "OK"

    def _clean(self, output: str) -> str:
        """Remove process commentary from Junior output."""
        skip = [
            "write permission", "not pre-authorized", "process note",
            "note to orchestrator", "i'll now", "i will now"
        ]
        lines = output.split("\n")
        clean = [l for l in lines if not any(p in l.lower() for p in skip)]
        return "\n".join(clean).strip()
