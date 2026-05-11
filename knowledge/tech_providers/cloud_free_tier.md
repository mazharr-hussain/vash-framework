# knowledge/tech_providers/cloud_free_tier.md

## Purpose
Reference for cloud free tier options during VASH activities.
Read this file only during Phase 3 infrastructure decision activities.

## LAW 1 Rule
Use free tier always until VASH generates revenue.
Document why paid tier is needed if ever selected.

## Compute Free Tiers
| Provider | Free Compute | Limit | Notes |
|----------|-------------|-------|-------|
| GitHub Actions | 2000 min/month | Linux runners | Best for VASH automation |
| Oracle Cloud | 2 AMD VMs always free | 1GB RAM each | Best always-free compute |
| Google Cloud | f1-micro instance | 1 per region | 30GB disk included |
| AWS | t2.micro | 12 months only | Expires after year 1 |
| Fly.io | 3 shared VMs | 256MB RAM | Good for small apps |
| Render | Web service | Sleeps after 15min | Not for always-on |

## Database Free Tiers
| Provider | Free DB | Limit | Notes |
|----------|---------|-------|-------|
| Supabase | PostgreSQL | 500MB | Best free PostgreSQL |
| PlanetScale | MySQL | 5GB | Serverless MySQL |
| Neon | PostgreSQL | 3GB | Serverless PostgreSQL |
| Turso | SQLite | 9GB | Edge SQLite |
| MongoDB Atlas | MongoDB | 512MB | NoSQL option |

## Storage Free Tiers
| Provider | Free Storage | Limit | Notes |
|----------|-------------|-------|-------|
| GitHub | Unlimited public | LFS limited | Best for artifacts |
| Cloudflare R2 | 10GB/month | 1M requests | S3-compatible |
| Backblaze B2 | 10GB | Free egress to CF | Good with Cloudflare |
| Supabase Storage | 1GB | Included in free | Good for small files |

## Cache Free Tiers
| Provider | Free Cache | Limit | Notes |
|----------|-----------|-------|-------|
| Upstash Redis | 256MB | 10K cmd/day | Best for VASH state |
| Redis Cloud | 30MB | Always free | Very limited |

## Recommended Stack For VASH MVP (all free)
| Layer | Choice | Why |
|-------|--------|-----|
| Compute | GitHub Actions | Already integrated with VASH |
| Database | Supabase PostgreSQL | Best free tier + open source |
| Storage | GitHub + Supabase | Already using GitHub |
| Cache | Upstash Redis | Sufficient for pipeline state |
| CDN | Cloudflare | Free tier very generous |
