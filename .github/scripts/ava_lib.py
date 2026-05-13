#!/usr/bin/env python3
"""
VASH 3.0 — AvA Library
All AvA logic organised in classes.
LAW 1: Python stdlib only — no pip installs
LAW 2: Fully automated
LAW 3: Standard patterns, modular design
"""

import os
import re
import json
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime, timezone


# ─────────────────────────────────────────────
# class Files
# All file read/write operations
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

    def pre_create(self, *paths: str) -> None:
        """Pre-create directories for all paths."""
        for path in paths:
            full = self.root / path
            full.parent.mkdir(parents=True, exist_ok=True)
            if not full.exists():
                full.touch()

    def hash(self, path: str) -> str:
        content = self.read(path)
        return hashlib.md5(content.encode()).hexdigest() if content else ""

    def get_activity(self, task_id: str) -> str:
        content = self.read("knowledge/activity_list.md")
        pattern = rf"ID: {re.escape(task_id)}\n(.*?)(?=\n---|\Z)"
        m = re.search(pattern, content, re.DOTALL)
        return m.group(0) if m else ""

    def get_threshold(self, task_id: str) -> int:
        activity = self.get_activity(task_id)
        m = re.search(r"THRESHOLD:\s*(\d+)", activity)
        return int(m.group(1)) if m else 88

    def get_output_path(self, task_id: str) -> str:
        activity = self.get_activity(task_id)
        m = re.search(r"OUTPUT_PATH:\s*(.+)", activity)
        return m.group(1).strip() if m else ""

    def update_activity_status(self, task_id: str, status: str) -> None:
        content = self.read("knowledge/activity_list.md")
        tid = re.escape(task_id)
        updated = re.sub(
            rf"(ID: {tid}.*?STATUS:)\s*\w+",
            rf"\1 {status}",
            content,
            flags=re.DOTALL
        )
        self.write("knowledge/activity_list.md", updated)

    def save_artifact(self, task_id: str, content: str) -> None:
        tid = task_id.replace(".", "-")
        self.write(f"runtime/artifacts/{tid}_artifact.md", content)
        output_path = self.get_output_path(task_id)
        if output_path and output_path not in ("N/A", "Multiple files"):
            self.write(output_path, content)

    def save_ava_log(self, task_id: str, round_num: int, content: str) -> None:
        tid = task_id.replace(".", "-")
        ts = datetime.now(timezone.utc).isoformat()
        log = f"# AvA Log — Activity {task_id} Round {round_num}\nTimestamp: {ts}\n\n{content}"
        self.write(f"runtime/ava_logs/{tid}_round{round_num}.md", log)

    def save_summary(self, task_id: str, content: str) -> None:
        tid = task_id.replace(".", "-")
        self.write(f"runtime/validation/{tid}_summary.md", content)


# ─────────────────────────────────────────────
# class State
# Manages ava state per activity
# ─────────────────────────────────────────────
class State:
    def __init__(self, files: Files):
        self.files = files

    def _path(self, task_id: str) -> str:
        tid = task_id.replace(".", "-")
        return f"runtime/ava_logs/{tid}_state.json"

    def load(self, task_id: str) -> dict:
        content = self.files.read(self._path(task_id))
        if content:
            try:
                return json.loads(content)
            except Exception:
                pass
        return {
            "task_id": task_id,
            "current_round": 0,
            "artifact_hash": "",
            "locked_sections": [],
            "failed_sections": [],
            "overall_score": 0,
            "rounds_completed": 0,
            "last_updated": ""
        }

    def save(self, task_id: str, state: dict) -> None:
        state["last_updated"] = datetime.now(timezone.utc).isoformat()
        self.files.write(self._path(task_id), json.dumps(state, indent=2))

    def reset(self, task_id: str) -> None:
        """Reset state and clear all AvA logs for this task."""
        tid = task_id.replace(".", "-")
        # Delete state file
        self.files.delete(self._path(task_id))
        # Delete all AvA log rounds
        for i in range(1, 10):
            self.files.delete(f"runtime/ava_logs/{tid}_round{i}.md")
        # Delete artifact
        self.files.delete(f"runtime/artifacts/{tid}_artifact.md")

    def get_scenario(self, task_id: str) -> str:
        """
        Detect which scenario applies:
        A = artifact exists, round 1 (first review)
        B = artifact exists, round 2+ (targeted fix)
        C = no artifact, round 1
        D = no artifact, round 2+ (reset to C)
        """
        tid = task_id.replace(".", "-")
        artifact_path = f"runtime/artifacts/{tid}_artifact.md"
        artifact_exists = (
            self.files.exists(artifact_path) and
            self.files.size(artifact_path) > 100
        )
        state = self.load(task_id)
        rounds_done = state.get("rounds_completed", 0)

        if artifact_exists and rounds_done == 0:
            return "A"
        elif artifact_exists and rounds_done >= 1:
            return "B"
        elif not artifact_exists and rounds_done == 0:
            return "C"
        else:
            return "D"

    def get_locked_sections(self, task_id: str) -> list:
        return self.load(task_id).get("locked_sections", [])

    def get_failed_sections(self, task_id: str) -> list:
        return self.load(task_id).get("failed_sections", [])

    def get_current_round(self, task_id: str) -> int:
        return self.load(task_id).get("rounds_completed", 0)

    def update_after_review(self, task_id: str, score: int,
                            locked: list, failed: list) -> None:
        state = self.load(task_id)
        tid = task_id.replace(".", "-")
        state["overall_score"] = score
        state["rounds_completed"] = state.get("rounds_completed", 0) + 1
        state["current_round"] = state["rounds_completed"]
        state["artifact_hash"] = self.files.hash(
            f"runtime/artifacts/{tid}_artifact.md"
        )
        # Locked sections accumulate — never removed without human approval
        existing_locked_titles = {s["title"] for s in state["locked_sections"]}
        for section in locked:
            if section["title"] not in existing_locked_titles:
                state["locked_sections"].append(section)
        state["failed_sections"] = failed
        self.save(task_id, state)


# ─────────────────────────────────────────────
# class Parser
# Parses Senior output into structured data
# ─────────────────────────────────────────────
class Parser:

    def parse_score(self, text: str) -> int:
        m = re.search(r"SCORE:\s*(\d+)", text)
        return int(m.group(1)) if m else 0

    def parse_verdict(self, text: str) -> str:
        m = re.search(r"VERDICT:\s*(APPROVED|MODIFY|FAIL)", text)
        return m.group(1) if m else "FAIL"

    def parse_sections(self, text: str) -> tuple:
        """
        Parse SECTION REVIEW block.
        Returns (locked_sections, failed_sections) as lists of dicts.
        """
        locked = []
        failed = []
        section_block = re.search(
            r"SECTION REVIEW:(.*?)(?=OBJECTIONS:|CORRECTIONS:|SCORE:|\Z)",
            text, re.DOTALL
        )
        if not section_block:
            return locked, failed

        for line in section_block.group(1).strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            if ": PASS" in line:
                title = line.split(": PASS")[0].strip()
                locked.append({"title": title, "status": "PASS"})
            elif ": FAIL" in line:
                parts = line.split(": FAIL")
                title = parts[0].strip()
                reason = parts[1].strip(" —-") if len(parts) > 1 else ""
                failed.append({"title": title, "status": "FAIL",
                               "reason": reason})
        return locked, failed

    def parse_objections(self, text: str) -> list:
        m = re.search(r"OBJECTIONS:(.*?)(?=CORRECTIONS:|\Z)", text, re.DOTALL)
        if not m:
            return []
        block = m.group(1).strip()
        if block.upper() == "NONE" or not block:
            return []
        return [line.strip() for line in block.split("\n")
                if line.strip() and not line.strip().upper() == "NONE"]

    def parse_corrections(self, text: str) -> list:
        m = re.search(r"CORRECTIONS:(.*?)(?=\Z)", text, re.DOTALL)
        if not m:
            return []
        block = m.group(1).strip()
        if block.upper() == "NONE" or not block:
            return []
        return [line.strip() for line in block.split("\n")
                if line.strip() and not line.strip().upper() == "NONE"]

    def parse_all(self, text: str) -> dict:
        locked, failed = self.parse_sections(text)
        return {
            "score": self.parse_score(text),
            "verdict": self.parse_verdict(text),
            "locked_sections": locked,
            "failed_sections": failed,
            "objections": self.parse_objections(text),
            "corrections": self.parse_corrections(text),
            "raw": text
        }


# ─────────────────────────────────────────────
# class Runner
# Calls Claude Code CLI
# ─────────────────────────────────────────────
class Runner:

    def run_claude(self, prompt: str) -> str:
        """Call Claude Code CLI with prompt via stdin. Returns output or error string."""
        import tempfile
        try:
            # Write prompt to temp file — avoids arg length limits and pipe issues
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt',
                                             delete=False, encoding='utf-8') as f:
                f.write(prompt)
                prompt_file = f.name

            # Pass prompt via stdin — more reliable than arg on Linux headless VM
            with open(prompt_file, 'r') as stdin_f:
                result = subprocess.run(
                    ["claude", "-p", "-"],
                    stdin=stdin_f,
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

            # Cleanup temp file
            try:
                os.unlink(prompt_file)
            except Exception:
                pass

            output = result.stdout.strip()
            if not output and result.stderr:
                return f"ERROR: {result.stderr[:300]}"
            return output
        except subprocess.TimeoutExpired:
            return "ERROR: Claude Code timed out after 300 seconds"
        except FileNotFoundError:
            return "ERROR: Claude Code CLI not found"
        except Exception as e:
            return f"ERROR: {str(e)}"

    def is_error(self, output: str) -> bool:
        return not output or output.startswith("ERROR")

    def clean_output(self, output: str) -> str:
        """Remove process notes and commentary from Junior output."""
        lines = output.split("\n")
        skip_phrases = [
            "write permission", "not pre-authorized",
            "process note", "note to orchestrator",
            "i'll now", "i will now", "let me", "i need to"
        ]
        clean = [
            l for l in lines
            if not any(p in l.lower() for p in skip_phrases)
        ]
        return "\n".join(clean).strip()


# ─────────────────────────────────────────────
# class Prompts
# Builds prompts for Junior and Senior
# ─────────────────────────────────────────────
class Prompts:
    def __init__(self, files: Files):
        self.files = files

    def _base_context(self, task_id: str) -> dict:
        return {
            "activity": self.files.get_activity(task_id),
            "laws": self.files.read("knowledge/laws.md"),
            "checklist": self.files.read("knowledge/checklists/artifact.md"),
            "threshold": self.files.get_threshold(task_id),
            "output_path": self.files.get_output_path(task_id),
            "tid": task_id.replace(".", "-")
        }

    def build_junior(self, task_id: str, scenario: str,
                     locked_sections: list = None,
                     failed_sections: list = None) -> str:
        ctx = self._base_context(task_id)
        tid = ctx["tid"]

        if scenario in ("C", "D"):
            # Minimal prompt — Claude reads files by path itself
            return "\n".join([
                "You are the VASH 3.0 Junior Creator.",
                f"TASK: Produce the complete artifact for activity {task_id}.",
                f"Read these files for context:",
                f"- knowledge/activity_list.md (find activity {task_id})",
                f"- knowledge/laws.md",
                f"- knowledge/checklists/artifact.md",
                f"OUTPUT PATH: {ctx['output_path']}",
                f"THRESHOLD: {ctx['threshold']}/100",
                "RULES:",
                "- Design and planning only. NO code.",
                "- Full content. Never summarise.",
                "- Apply all three laws.",
                "- Output ONLY artifact content. No preamble, no wrappers, no approval requests.",
                "- Start with the artifact title line (e.g. # Title).",
                "Output the complete artifact now:"
            ])

        elif scenario == "B":
            # Minimal prompt — reference files by path, pass only corrections
            locked_titles = "\n".join(
                f"- {s['title']}" for s in (locked_sections or [])
            )
            failed_list = "\n".join(
                f"- {s['title']}: {s.get('reason','')}"
                for s in (failed_sections or [])
            )
            corrections = "\n".join(
                f"- {s['title']}: {s.get('correction', s.get('reason',''))}"
                for s in (failed_sections or [])
            )
            return "\n".join([
                "You are the VASH 3.0 Junior Creator — fix mode.",
                f"TASK: Fix failed sections in artifact for activity {task_id}.",
                f"Read current artifact from: runtime/artifacts/{tid}_artifact.md",
                f"Read laws from: knowledge/laws.md",
                "LOCKED SECTIONS (copy verbatim from artifact — do NOT change):",
                locked_titles if locked_titles else "None",
                "FAILED SECTIONS (fix only these):",
                failed_list if failed_list else "None",
                "CORRECTIONS REQUIRED:",
                corrections if corrections else "None",
                "RULES:",
                "- Output ONLY the complete rewritten artifact content.",
                "- No approval requests, no process notes, no wrappers.",
                "- Start with artifact title line (e.g. # Title).",
                "- Locked sections: copy character-for-character from the artifact file.",
                "- Failed sections: apply the corrections above.",
                "Output the complete rewritten artifact now:"
            ])

        return ""

    def build_senior(self, task_id: str,
                     locked_sections: list = None) -> str:
        ctx = self._base_context(task_id)
        tid = ctx["tid"]
        locked_titles = "\n".join(
            f"- {s['title']} (PASS round {s.get('locked_round', '?')})"
            for s in (locked_sections or [])
        )

        # Minimal prompt — Claude reads files by path
        return "\n".join([
            "You are the VASH 3.0 Senior Validator.",
            f"TASK: Review artifact for activity {task_id}.",
            f"Read artifact from: runtime/artifacts/{tid}_artifact.md",
            f"Read activity from: knowledge/activity_list.md (find {task_id})",
            f"Read laws from: knowledge/laws.md",
            f"Read checklist from: knowledge/checklists/artifact.md",
            f"THRESHOLD: {ctx['threshold']}/100",
            "LOCKED SECTIONS (mark PASS automatically — do not re-evaluate):",
            locked_titles if locked_titles else "None — round 1",
            "OUTPUT FORMAT (use exactly):",
            "SCORE: [0-100]",
            "VERDICT: APPROVED / MODIFY / FAIL",
            "SECTION REVIEW:",
            "## Section Title: PASS",
            "## Section Title: FAIL — [reason]",
            "OBJECTIONS:",
            "OBJ-001: [## Section] [issue] (or NONE)",
            "CORRECTIONS:",
            "OBJ-001: [exact fix] (or NONE)",
            "Begin review now:"
        ])


# ─────────────────────────────────────────────
# class Reporter
# Builds owner-facing summaries
# ─────────────────────────────────────────────
class Reporter:
    def __init__(self, files: Files):
        self.files = files

    def write_summary(self, task_id: str, score: int,
                      verdict: str, failed_sections: list,
                      objections: list, corrections: list) -> None:
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

        if failed_sections:
            lines.append("**Sections Needing Improvement:**")
            for s in failed_sections:
                lines.append(f"- {s['title']}: {s.get('reason','')}")
            lines.append("")

        if objections:
            lines.append("**Specific Issues:**")
            for obj in objections:
                lines.append(f"- {obj}")
            lines.append("")

        if corrections:
            lines.append("**Required Corrections:**")
            for cor in corrections:
                lines.append(f"- {cor}")
            lines.append("")

        lines.append("**Your Decision:**")
        if verdict == "APPROVED":
            lines.append(f"- APPROVED {task_id}")
        elif verdict == "MODIFY":
            lines.append(f"- MODIFY {task_id} [corrections already identified above]")
            lines.append(f"- REJECTED {task_id} [reason — if full rebuild needed]")
        else:
            lines.append(f"- REJECTED {task_id} [reason]")

        lines.append("")
        lines.append(f"*Validated: {ts}*")

        self.files.save_summary(task_id, "\n".join(lines))


# ─────────────────────────────────────────────
# class Orchestrator
# Main flow controller
# ─────────────────────────────────────────────
class Orchestrator:
    def __init__(self, repo_root: Path):
        self.files = Files(repo_root)
        self.state = State(self.files)
        self.parser = Parser()
        self.runner = Runner()
        self.prompts = Prompts(self.files)
        self.reporter = Reporter(self.files)

    def log(self, msg: str) -> None:
        print(f"[VASH AvA] {msg}", flush=True)

    def run(self, task_id: str) -> str:
        if not task_id:
            self.log("ERROR: No TASK_ID provided")
            return "FAIL"

        tid = task_id.replace(".", "-")
        scenario = self.state.get_scenario(task_id)
        self.log(f"Activity: {task_id} | Scenario: {scenario}")

        # Pre-create all output paths
        self.files.pre_create(
            f"runtime/artifacts/{tid}_artifact.md",
            f"runtime/prompts/{tid}_prompt.md",
            f"runtime/validation/{tid}_summary.md"
        )

        if scenario == "D":
            self.log("Scenario D: No artifact, round 2+ — resetting to round 1")
            self.state.reset(task_id)
            scenario = "C"

        if scenario == "A":
            return self._run_scenario_a(task_id)
        elif scenario == "B":
            return self._run_scenario_b(task_id)
        else:  # C
            return self._run_scenario_c(task_id)

    def _run_scenario_a(self, task_id: str) -> str:
        """Artifact exists, round 1 — Senior validation only."""
        tid = task_id.replace(".", "-")
        self.log("Scenario A: Existing artifact — Senior validation only")

        round_num = 1
        senior_prompt = self.prompts.build_senior(task_id)
        self.files.write(
            f"runtime/prompts/{tid}_prompt.md",
            f"# Senior Prompt — Round {round_num}\n{senior_prompt}"
        )

        self.log("Senior reviewing existing artifact...")
        senior_output = self.runner.run_claude(senior_prompt)

        if self.runner.is_error(senior_output):
            self.log(f"Senior failed: {senior_output}")
            self._write_error_summary(task_id, senior_output)
            return "FAIL"

        result = self.parser.parse_all(senior_output)
        score = result["score"]
        verdict = result["verdict"]
        locked = result["locked_sections"]
        failed = result["failed_sections"]
        threshold = self.files.get_threshold(task_id)

        if score >= threshold:
            verdict = "APPROVED"

        # Mark locked sections with round number
        for s in locked:
            s["locked_round"] = round_num

        self.files.save_ava_log(task_id, round_num, senior_output)
        self.state.update_after_review(task_id, score, locked, failed)
        self.reporter.write_summary(
            task_id, score, verdict, failed,
            result["objections"], result["corrections"]
        )

        if verdict == "APPROVED":
            self.files.update_activity_status(task_id, "PASS")
        self.log(f"Scenario A complete: {verdict} ({score}/100)")
        return verdict

    def _run_scenario_b(self, task_id: str) -> str:
        """Artifact exists, round 2+ — Junior fixes failed sections only."""
        tid = task_id.replace(".", "-")
        locked = self.state.get_locked_sections(task_id)
        failed = self.state.get_failed_sections(task_id)
        round_num = self.state.get_current_round(task_id) + 1
        threshold = self.files.get_threshold(task_id)

        self.log(f"Scenario B: Round {round_num} — fixing {len(failed)} failed sections")
        self.log(f"Locked sections: {len(locked)} — will not be re-evaluated")

        # Junior fixes only failed sections
        junior_prompt = self.prompts.build_junior(
            task_id, "B", locked, failed
        )
        self.files.write(
            f"runtime/prompts/{tid}_prompt.md",
            f"# Junior Prompt — Round {round_num}\n{junior_prompt}"
        )

        self.log("Junior fixing failed sections...")
        junior_output = self.runner.run_claude(junior_prompt)

        if self.runner.is_error(junior_output):
            self.log(f"Junior failed: {junior_output}")
            self._write_error_summary(task_id, junior_output)
            return "FAIL"

        clean = self.runner.clean_output(junior_output)
        self.files.save_artifact(task_id, clean)
        self.log("Artifact updated with fixes")

        # Senior reviews full artifact, carries forward locked sections
        senior_prompt = self.prompts.build_senior(task_id, locked)
        senior_output = self.runner.run_claude(senior_prompt)

        if self.runner.is_error(senior_output):
            self.log(f"Senior failed: {senior_output}")
            self._write_error_summary(task_id, senior_output)
            return "FAIL"

        result = self.parser.parse_all(senior_output)
        score = result["score"]
        verdict = result["verdict"]
        new_locked = result["locked_sections"]
        new_failed = result["failed_sections"]

        if score >= threshold:
            verdict = "APPROVED"

        for s in new_locked:
            s["locked_round"] = round_num

        self.files.save_ava_log(task_id, round_num, senior_output)
        self.state.update_after_review(task_id, score, new_locked, new_failed)
        self.reporter.write_summary(
            task_id, score, verdict, new_failed,
            result["objections"], result["corrections"]
        )

        if verdict == "APPROVED":
            self.files.update_activity_status(task_id, "PASS")
        self.log(f"Scenario B complete: {verdict} ({score}/100)")
        return verdict

    def _run_scenario_c(self, task_id: str) -> str:
        """No artifact — full Junior generation then Senior review."""
        tid = task_id.replace(".", "-")
        threshold = self.files.get_threshold(task_id)
        self.log("Scenario C: No artifact — full generation")

        # Junior generates full artifact
        junior_prompt = self.prompts.build_junior(task_id, "C")
        self.files.write(
            f"runtime/prompts/{tid}_prompt.md",
            f"# Junior Prompt — Round 1\n{junior_prompt}"
        )

        self.log("Junior generating artifact...")
        junior_output = self.runner.run_claude(junior_prompt)

        if self.runner.is_error(junior_output):
            self.log(f"Junior failed: {junior_output}")
            self._write_error_summary(task_id, junior_output)
            return "FAIL"

        clean = self.runner.clean_output(junior_output)
        self.files.save_artifact(task_id, clean)
        self.log(f"Artifact saved: runtime/artifacts/{tid}_artifact.md")

        # Senior reviews full artifact
        senior_prompt = self.prompts.build_senior(task_id)
        self.log("Senior reviewing artifact...")
        senior_output = self.runner.run_claude(senior_prompt)

        if self.runner.is_error(senior_output):
            self.log(f"Senior failed: {senior_output}")
            self._write_error_summary(task_id, senior_output)
            return "FAIL"

        result = self.parser.parse_all(senior_output)
        score = result["score"]
        verdict = result["verdict"]
        locked = result["locked_sections"]
        failed = result["failed_sections"]

        if score >= threshold:
            verdict = "APPROVED"

        for s in locked:
            s["locked_round"] = 1

        self.files.save_ava_log(task_id, 1, senior_output)
        self.state.update_after_review(task_id, score, locked, failed)
        self.reporter.write_summary(
            task_id, score, verdict, failed,
            result["objections"], result["corrections"]
        )

        if verdict == "APPROVED":
            self.files.update_activity_status(task_id, "PASS")
        self.log(f"Scenario C complete: {verdict} ({score}/100)")
        return verdict

    def _write_error_summary(self, task_id: str, error: str) -> None:
        tid = task_id.replace(".", "-")
        summary = (
            f"# YOUR REVIEW — Activity {task_id}\n\n"
            f"**Verdict:** FAIL\n\n"
            f"**Error:** Claude Code could not complete the task.\n\n"
            f"**Details:** {error[:300]}\n\n"
            f"- REJECTED {task_id} — check GitHub Actions logs\n"
        )
        self.files.save_summary(task_id, summary)
