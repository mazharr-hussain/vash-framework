# knowledge/tech_providers/ai_models.md

## Purpose
Reference for AI model selection during VASH activities.
Read this file only during Phase 3 technology decision activities.

## VASH Development Models (Claude only)
| Role | Model | Purpose |
|------|-------|---------|
| Junior (generator) | Claude Haiku | High volume artifact generation — lower cost |
| Senior (reviewer) | Claude Sonnet | Critical review and judgment — best quality |
| Orchestrator | Claude Haiku | Routing and pipeline management |

## Models for Software Built BY VASH (decided per project)
These are options — Architecture Agent selects per project ADR.

| Provider | Model | Best For | Cost |
|----------|-------|----------|------|
| Anthropic | Claude Sonnet 4.6 | Complex reasoning, review | $3-15/1M tokens |
| Anthropic | Claude Haiku | Fast generation, routing | $0.25-1.25/1M tokens |
| Google | Gemini 1.5 Pro | Large context reading | $1.25-3.50/1M tokens |
| Google | Gemini Flash | Cheap large context | $0.30/1M tokens |
| DeepSeek | DeepSeek V3 | Structured generation | $0.14/1M tokens |
| OpenAI | GPT-4o | Cross-perspective review | $5-15/1M tokens |
| OpenAI | GPT-4o Mini | Simple classification | $0.15-0.60/1M tokens |

## Selection Principle
Cheapest model that delivers quality for the specific task.
Never underspend on critical decisions.
Never overspend on structured generation.

## LAW 1 Compliance
All models accessed via API only — no proprietary SDKs.
Model routing via LiteLLM (open source) for software built by VASH.
