# knowledge/tech_providers/ai_models.md
Amended by 2.6 (ADR-001 D7). PROPOSED: in force when ADR-001 is ACCEPTED; until then the earlier text (git history) applies.

## Purpose
Reference for AI model routing. Read during Phase 3 activity 3.3 and when writing a project's
project-stack.json. Every limit here changes often: verify in activity 3.3 before use.

## Routing Rules (from knowledge/laws.md)
| Rule | Meaning |
|------|---------|
| R2 Data privacy | Intake and any client data: local model only |
| R4 Independent critic | Senior / Critic on a different vendor from Junior / Coder |
| R12 Pooling tools | Pooling and failover through a vetted open-source tool; no custom routing |
| LAW 1 | Free tiers only; local model as the final fallback |

## Pooling Tool Candidates (decided in 3.3 by ADR)
| Tool | Status | Notes |
|------|--------|-------|
| freellmpool | Named by Blueprint v8.2 (MIT, OpenAI-compatible endpoint, many free-tier providers) | NOT verified in session 2.6: existence, maintenance, licence, provider list, quota tracking, local fallback |
| LiteLLM | Previous VASH reference (open source) | Fallback candidate if freellmpool fails verification |

## Free-Tier Providers to Evaluate (named by Blueprint v8.2)
| Provider | Type | To verify in 3.3 |
|----------|------|------------------|
| Groq | Hosted inference, free tier | Limits, models, data-use terms |
| Cerebras | Hosted inference, free tier | Limits, models, data-use terms |
| Google Gemini | Hosted, free tier | Limits; whether free-tier prompts are used for training |
| OpenRouter | Router with free models | Limits, data-use terms |
| GitHub Models | Hosted, free tier with GitHub account | Limits |
| Mistral | Hosted, free tier | Limits, data-use terms |
| Cohere | Hosted, trial / free tier | Limits, commercial-use terms |
| Cloudflare Workers AI | Hosted, free daily allowance | Limits |
| Ollama (local, on OCI A1) | Self-hosted, open source | Fits A1 memory with one 7B coder model (v8.2: qwen2.5-coder:7b) |

Data-use terms matter: a free tier that may use prompts for training is allowed only for
public, non-client content (VASH's own design work), never for client data (R2).

## Route Assignment
| Use | Route |
|-----|-------|
| Intake, client data | Local Ollama |
| Junior / Coder | Pool route A |
| Senior / Critic | Pool route B — different vendor from route A |
| Exhausted free tiers | Local Ollama |

## Transitional (OD-1)
Until activity 7.7, VASH's own development keeps the existing Claude tooling for Junior and Senior.
This is recorded as a known limitation (same vendor) in each AvA log.
