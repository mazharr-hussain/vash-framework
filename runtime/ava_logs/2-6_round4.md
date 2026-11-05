# AvA Log — Activity 2.6 Round 4 (MODIFY 1, session round 1)
Timestamp: 2026-11-05T11:56:53Z

SCORE: 86
THRESHOLD: 90
VERDICT: MODIFY

Scope: only the MODIFY 1 change (owner request "Can you include Ollama, OpenRouter,
https://github.com/Alishahryar1/free-claude-code"), reviewed from the uncommitted diff, and its consistency
with the round 3 approved state.

Score breakdown: Completeness 38/40 (all three named with role, interface, licence / use and privacy in
Section 9.2a; FCC rules in 9.6; `models.harness` and catalog `use` field added; OD-7; LAW 3 record in 14.2;
ADR D7, ai_models.md, platforms.md, activity list 3.3 / 7.7, decision and summary files updated; residual:
ADR D10 not aligned with OD-7). Law compliance 26/30 (R2, R4 and R12 respected in the text; the AGPL
position is sound and left to the owner; deduction: facts presented as "found" are wrong or out of date,
which breaks the "verify, never overstate" discipline of LAW 3 and puts wrong facts into the ADR the owner
accepts; LAW 1 open-source preference vs the proprietary Claude Code harness under FCC only partly
handled). Quality 12/20 (three factual errors, one stale table row, one ambiguous privacy rule, one
overstated "one job per tool" claim). No code 10/10 (tables and prose only).

Web check (5 Nov 2026, WebFetch of the GitHub page, its releases page and the PyPI page):
- free-claude-code: AGPL-3.0-only — CONFIRMED. 66.6k stars — CONFIRMED. NVIDIA NIM default — CONFIRMED.
  About 60 providers — CONFIRMED (page says 61). Harnesses Claude Code, Codex, OpenCode, Cline, Aider and
  others — CONFIRMED (12 listed). "Not affiliated with or endorsed by Anthropic" — CONFIRMED. A failed
  request may consume usage on more than one provider — CONFIRMED. Some plans limited to personal,
  interactive use — CONFIRMED. Optional bearer token for the proxy — CONFIRMED (optional, Admin UI).
  "1.3B+ free tokens per month" — the claim is on the page (correctly marked as to verify).
  "No releases published" — FALSE: the releases page shows tagged releases (v6.18.11 on 5 Nov, v6.18.10
  4 Nov, ... at least 11 pages). Python as language — only indicated by a badge, not stated.
- freellmpool: on PyPI, MIT — CONFIRMED. OpenAI-compatible proxy, library, CLI and MCP server — CONFIRMED.
  Failover and local daily usage counters — CONFIRMED. "Versions 0.3–0.9" — OUT OF DATE: 20 versions, latest
  0.13.0 (30 Aug 2026); 0.3.0–0.9.3 all dated 3 Jun 2026. "16 providers" — FALSE: 22 provider groups
  (178 enabled chat routes). "GitHub Models" among its providers — NOT LISTED on the page. Source
  repository is named on PyPI (github.com/0xzr/freellmpool). Development status "4 - Beta". Local
  Ollama / LM Studio / llama.cpp can be imported but imported models are EXCLUDED from automatic routing;
  "Ollama Cloud" is a keyed external provider — directly relevant to the "local Ollama fallback" item.

CHECKLIST:
knowledge/laws.md read: PASS
Activity ID / MODIFY 1 task understood (prompt section "MODIFY 1 — owner request" saved): PASS
Output path confirmed (vash_framework/architecture/2-6_application_framework.md = runtime/artifacts/2-6_artifact.md, diff empty): PASS
Prompt saved to runtime/prompts/2-6_prompt.md before the change: PASS
Request fully met (Ollama, OpenRouter, free-claude-code each named with role, interface, licence / use, privacy — Section 9.2a): PASS
No actual software code: PASS
Language clear, structured, complete: PASS
No summaries — full content: PASS
AvA log round recorded (this file round 4): PASS
Threshold known (90): PASS
Facts about free-claude-code correct and not overstated: FAIL (OBJ-031)
Facts about freellmpool correct and not overstated: FAIL (OBJ-032)
Nothing stated as found / verified that is not: FAIL (OBJ-031, OBJ-032)
AGPL-3.0-only position sound for a public MIT repository (run unmodified as a separate service, never fork or link; decision left to owner in OD-7 and 4.1): PASS
R2 privacy (client data only to local Ollama; Ollama cloud models treated as external): PASS with a wording gap in 9.6 item 3 (OBJ-034)
R4 different vendor (9.6 item 4, AvA log records both routes): PASS
R12 no custom routing (9.6 item 6): PASS
OD-1 ending at 7.7 consistent with OD-7 (earlier end): FAIL, minor (OBJ-035)
LAW 1 open-source preference vs proprietary harness (9.6 item 7): PASS with a gap (OBJ-037)
One job per tool: PASS with an overstated claim (OBJ-036)
Decision file and summary updated (OD-1 to OD-7), decision still PENDING: PASS
Table formatting (column counts of every table in artifact, ADR, ai_models.md, platforms.md): PASS
Nothing client-specific added to the public repository: PASS

LAWS:
LAW1 VANILLA: PASS — every new component is $0 (Ollama MIT, OpenRouter free models, FCC AGPL run-only, freellmpool MIT); the proprietary harness is kept only as a $0 option, not a dependency.
LAW2 AGENT: PASS — no new manual step; FCC routing and the cost meter are automated; human only answers OD-7.
LAW3 SKILLS: FAIL (partial) — the search is documented in 14.2 and the deep check is assigned to 3.3, but several "found" facts are wrong or out of date (OBJ-031, OBJ-032); the record must state only what was actually confirmed.

GATE1: PASS (byte-identical copy, table column counts consistent, no code fences added)
SENIOR_ROUTE: Claude Opus 5.5 (claude-opus-5-5)   JUNIOR_ROUTE: same vendor (transitional exception OD-1, recorded; independence limited to isolated contexts — R4 not met until 7.7 exits, or until OD-7 is accepted and applied)
CANARY: NONE

OBJECTIONS:
OBJ-031 (blocking): "no releases published; pin a commit" is false. Locations: artifact Section 9.6 item 1 ("pinned to a commit (it publishes no releases)"), Section 14.2 row "Harness bridge" ("no releases published"), knowledge/tech_providers/ai_models.md Harness Bridge table ("stability (no releases published; pin a commit)"), runtime/prompts/2-6_prompt.md MODIFY 1 facts ("no releases published"). The releases page shows tagged releases up to v6.18.11 (5 Nov 2026), several per week.
OBJ-032 (blocking): freellmpool facts are wrong / out of date and stated as "Found on 5 Nov 2026". Locations: artifact Section 9.2 and 14.2 ("versions 0.3–0.9", "16 providers", "GitHub Models"), ADR-001 D7 (only "on PyPI, MIT" — correct), ai_models.md "Update 5 Nov 2026" paragraph ("versions 0.3-0.9", "16 providers"). PyPI shows 0.13.0 (30 Aug 2026), 22 provider groups, no GitHub Models, Beta status, and source repository github.com/0xzr/freellmpool already named. Section 9.2 lists "local Ollama fallback" as to verify, but the PyPI page says imported local models are excluded from automatic routing — a known risk, not an open unknown.
OBJ-033 (non-blocking): knowledge/tech_providers/ai_models.md keeps the old freellmpool row "NOT verified in session 2.6: existence, maintenance, licence, ..." directly above the new "Update" paragraph that says existence and licence were found. The two statements contradict.
OBJ-034 (non-blocking): artifact Section 9.6 item 3 "Client data goes only through FCC's Ollama provider" — FCC offers both local Ollama and Ollama cloud models (prompt facts: "Ollama local and cloud"); 9.2a correctly says cloud models are external, 9.6 item 3 does not say "local". Same for 9.2a FCC row "client data only to its Ollama provider".
OBJ-035 (non-blocking): OD-7 / Section 9.5 say FCC "can end the exception earlier", but ADR-001 D10 and LAW 1 transitional text still say "until activity 7.7 exits" without "or earlier if OD-7 is accepted"; activity 7.7 says exit ends OD-1. The owner accepts an ADR whose D7 and D10 do not state how they interact.
OBJ-036 (non-blocking): Section 9.6 item 6 "Neither duplicates the other's routing" is overstated: freellmpool and FCC both route to the same free providers (NIM, OpenRouter, Groq, Gemini, Cerebras, Cloudflare) with separate keys, separate failover and separate quota counters. The split by job (engine calls vs harness sessions) is sound, but the shared provider quotas and the cost meter must combine both counters; this is not stated.
OBJ-037 (non-blocking): Section 9.6 item 7 / OD-7 — running the proprietary Claude Code harness against non-Anthropic backends is subject to that harness's own licence / terms; not listed among the 3.3 checks (only provider terms are). LAW 1 open-source preference suggests the open harness (OpenCode / Aider / Cline) as the default for OD-7.
OBJ-038 (non-blocking): Section 9.6 item 2 "with its bearer token set" — correct as a VASH rule, but should say the token is optional in FCC and therefore a required setting checked by Stage 0 / 7.7 (otherwise a default install is unprotected).

CORRECTIONS:
OBJ-031: Replace with "publishes tagged releases (v6.18.x, frequent); pin a release tag and its commit SHA" in 9.6 item 1, 14.2, ai_models.md and the prompt facts; keep "stability / release cadence" as a 3.3 check.
OBJ-032: In 9.2, 14.2 and ai_models.md write: "PyPI: latest 0.13.0 (30 Aug 2026), MIT, Beta; OpenAI-compatible proxy, library, CLI and MCP server; 22 provider groups (including Groq, Cerebras, NVIDIA NIM, Gemini, OpenRouter, Cloudflare, Mistral, Cohere); failover; local daily counters; source github.com/0xzr/freellmpool. Local Ollama models can be imported but are excluded from automatic routing — the local fallback must be configured outside the pool's auto-routing (3.3)." Remove "GitHub Models" from its provider list. Mark the figures "as read on PyPI 5 Nov 2026".
OBJ-033: Change the freellmpool row's "To verify" column to "Maintenance, provider data-use terms, local Ollama fallback (see update)", or remove the old wording.
OBJ-034: Write "FCC's local Ollama provider (never Ollama cloud models)" in 9.6 item 3 and the 9.2a FCC row.
OBJ-035: Add to ADR D10 "(or earlier, for the routes FCC covers, if OD-7 is accepted)" and the same qualifier to the 7.7 exit sentence, or state in OD-7 that D10 is unchanged and FCC only removes the same-vendor limitation, not the Claude tooling exception.
OBJ-036: Reword item 6: "freellmpool serves engine calls, FCC serves harness sessions; both may reach the same providers, so the cost meter adds both tools' usage per provider and the free quotas are shared; no custom routing is added (R12)."
OBJ-037: Add "terms of the harness itself (Claude Code with non-Anthropic backends)" to the 3.3 checks in ai_models.md and OD-7; state the open harness as the preferred OD-7 default.
OBJ-038: Write "with its bearer token set (optional in FCC, so required by VASH and checked in 7.7)".
