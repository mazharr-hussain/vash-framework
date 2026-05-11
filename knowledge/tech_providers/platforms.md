# knowledge/tech_providers/platforms.md

## Purpose
Reference for platform selection during VASH activities.
Read this file only during Phase 3 technology decision activities.

## VASH Development Platform (fixed — not decided per project)
| Platform | Purpose | Cost | Why |
|----------|---------|------|-----|
| Claude.ai | All AI work — AvA Jr and Sr | Pro subscription | Only AI platform for VASH dev |
| GitHub | Code, artifacts, automation | Free tier | Version control and automation |
| Python | Orchestration scripts | Free | LAW 1 compliant |
| Claude Code | GitHub VM execution | Included in Pro | Runs Claude on GitHub Actions |

## Platform Categories for Software Built BY VASH
These are options — Architecture Agent selects per project ADR.

### Orchestration and Pipeline
| Option | Type | License | Free Tier |
|--------|------|---------|-----------|
| LangGraph | Open source | MIT | Self-host free |
| CrewAI | Open source | MIT | Self-host free |
| Temporal | Open source | MIT | Self-host free |

### Human-in-Loop Communication
| Option | Type | License | Free Tier |
|--------|------|---------|-----------|
| Telegram Bot | API | Free | Unlimited |
| Slack | SaaS | Proprietary | Limited free |
| GitHub Issues | SaaS | Proprietary | Free |

### State and Memory
| Option | Type | License | Free Tier |
|--------|------|---------|-----------|
| Redis (Upstash) | Managed | Open source | 10K cmd/day |
| PostgreSQL | Open source | MIT | Self-host free |
| SQLite | Open source | Public domain | Always free |

### Storage
| Option | Type | License | Free Tier |
|--------|------|---------|-----------|
| GitHub | SaaS | Proprietary | Free tier |
| Supabase | Open source | Apache 2.0 | 500MB free |
| MinIO | Open source | AGPL | Self-host free |

## LAW 1 Compliance
All platforms must have open source alternative.
Free tier required until VASH generates revenue.
No proprietary lock-in in core logic.
