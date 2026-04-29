---
name: supabase-self-hosted-docker-ubuntu
description: Deploy Supabase self-hosted on Ubuntu with Docker, handle Compose package quirks, initialize secure .env, bring up stack, and verify DB connectivity for app use.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [supabase, docker, ubuntu, compose, postgres, self-hosted]
---

# Supabase Self-Hosted on Ubuntu (Docker)

## When to use
Use when user asks to install/run Supabase via Docker on Ubuntu server and needs DB connection for a website/backend.

## Why this skill exists
Ubuntu package names for Docker Compose differ across releases. `docker-compose-plugin` may be unavailable even though Compose v2 is available as `docker-compose-v2`.

## Procedure

1. **Prerequisites check**
   - `docker --version`
   - `docker compose version` (or fallback `docker-compose version`)
   - `ss -lntp` to check port conflicts (8000, 8443, 5432, 6543)

2. **Install required packages**
   - Install git
   - Install Compose v2 on Ubuntu if missing:
     - `apt-get install -y docker-compose-v2`
   - Optional legacy CLI (not required):
     - `apt-get install -y docker-compose`

3. **Get Supabase self-hosted repo**
   - `git clone https://github.com/supabase/supabase.git /opt/supabase`
   - Use background execution if clone can exceed foreground timeout.

4. **Initialize Docker config**
   - `cd /opt/supabase/docker`
   - `cp -n .env.example .env`
   - Generate secrets safely:
     - `sh ./utils/generate-keys.sh --update-env`

5. **Set deployment-specific env values**
   Update `.env` minimally:
   - `SUPABASE_PUBLIC_URL=http://<host>:8000`
   - `API_EXTERNAL_URL=http://<host>:8000`
   - `SITE_URL=https://<host>` (or appropriate app URL)
   - `POOLER_TENANT_ID=<tenant-id>` (required for pooler username format)

6. **Start stack**
   - `docker compose up -d`
   - First run pulls many large images; can take several minutes.

7. **Verify health**
   - `docker compose ps`
   - Ensure core services are `running/healthy`:
     - `supabase-db`, `supabase-auth`, `supabase-rest`, `supabase-storage`, `supabase-meta`, `supabase-kong`, `supabase-pooler`, `supabase-studio`, `realtime`, `analytics`
   - Verify host listening ports:
     - `8000`, `8443`, `5432`, `6543`

## App DB connection outputs
From `.env`:
- `POSTGRES_PASSWORD`
- `POSTGRES_PORT` (usually 5432)
- `POOLER_PROXY_PORT_TRANSACTION` (usually 6543)
- `POOLER_TENANT_ID`

Typical connection strings:

### Session mode (recommended default)
`postgresql://postgres:<POSTGRES_PASSWORD>@<host>:5432/postgres`

### Transaction mode (pooler)
`postgresql://postgres.<POOLER_TENANT_ID>:<POSTGRES_PASSWORD>@<host>:6543/postgres`

## Vercel integration (when backend is deployed on Vercel)
If the app runs on Vercel (e.g. Next.js API routes), update project env vars right after Supabase is live:

- `NEXT_PUBLIC_SUPABASE_URL` = `http://<host>:8000` (or HTTPS URL if TLS fronted)
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` = `ANON_KEY` from `/opt/supabase/docker/.env`
- `SUPABASE_SERVICE_ROLE_KEY` = `SERVICE_ROLE_KEY` from `/opt/supabase/docker/.env`

Recommended commands (non-interactive):
- `npx --yes vercel link --yes --project <project> --cwd <repo> --scope <team> --token <token>`
- `npx --yes vercel env add <NAME> production --value '<value>' --yes --force ...`
- `npx --yes vercel env add <NAME> preview '' --value '<value>' --yes --force ...`
- `npx --yes vercel deploy --prod --yes ...`

Vercel DNS commands (team-scoped):
- List records: `npx --yes vercel dns ls <domain> --scope <team> --token <token>`
- Add A record: `npx --yes vercel dns add <domain> <name> A <ip> --scope <team> --token <token>`
  - Example: `vercel dns add faftech.net database A 103.208.206.199 ...`
- Common pitfall: `vercel dns add` argument order is `<domain> <name> <type> <value>` (not `<fqdn> <value> <type>`).
- Common pitfall: forgetting `--scope <team>` can produce permission errors even with valid token.

Why `preview ''` matters:
- Vercel CLI may prompt for git branch when setting Preview env. Passing empty positional git-branch (`''`) avoids interactive prompt and applies to all preview branches.

## Common pitfalls
- `docker-compose-plugin` not found on Ubuntu Jammy: install `docker-compose-v2`.
- First `docker compose up -d` may appear stalled; it is usually pulling/extracting large layers.
- `vercel env pull` can show sensitive values redacted/empty; verify presence with `vercel env ls <environment>` instead of assuming missing values.
- Do not expose raw secrets in chat logs; read from `.env` only when needed.
- If user wants production hardening, additional TLS/reverse proxy and firewall setup is required.
- **Critical for Vercel/external backends:** ensure `SUPABASE_PUBLIC_URL` hostname resolves to a **publicly reachable IP**, not private overlay IPs (e.g. `100.x.x.x` Tailscale/CGNAT). If DNS points to private IP, Vercel will timeout and API routes may return app-level `NOT_FOUND` fallbacks.
- After DNS changes, verify from outside the host (not only localhost/server shell):
  - `dig +short <host>` from public resolver (`@8.8.8.8`)
  - `curl` from external context to `http://<host>:8000/rest/v1/` (expect 401 without key, not timeout)
  - Only then redeploy app on Vercel.
- If frontend shows empty data after env update, check whether DB was actually migrated/seeded. Validate row counts directly in `supabase-db` (`psql`) before blaming app code.
- In some Next.js backends, API handlers catch all exceptions and return `notFoundResponse(...)` (404). This can mask real connectivity errors (`ECONNREFUSED`, `ENOTFOUND`) as fake "data not found". Always verify upstream connectivity separately.
- For Vercel debugging, bypass cache when testing API routes (`?t=<timestamp>` + `cache: no-store`) and inspect `x-vercel-cache` (`MISS/HIT/PRERENDER`) to avoid misreading stale responses.
- If service is reachable on `127.0.0.1`, LAN IP, or Tailscale IP but refused on public domain/IP, root cause is edge exposure (router/NAT/ISP/tunnel), not Supabase/container internals.
- If user refuses port forwarding, prepare alternatives explicitly:
  - Cloudflare Tunnel (requires Cloudflare token/zone control), or
  - Tailscale Funnel (must be enabled in tailnet admin first; otherwise `Funnel is not enabled on your tailnet`).

## Cloudflare Tunnel + external DNS provider (critical gotcha)
When authoritative DNS is **not** on Cloudflare (for example NS is on Vercel), tunnel routing needs **Partial/CNAME setup** behavior.

### Symptoms of wrong setup
- `cloudflared` service shows healthy connections, but public URL still timeout.
- DNS CNAME points directly to `<tunnel-id>.cfargotunnel.com`.
- `dig` may return only AAAA for `*.cfargotunnel.com`, while external clients time out.

### Correct pattern for partial/CNAME setup
1. Ensure `faftech.net` (or your zone) exists in Cloudflare account as a zone (partial/CNAME or full).
2. Add published route in tunnel for `database.<domain>` -> `http://127.0.0.1:8000`.
3. At external DNS provider (e.g. Vercel DNS), set:
   - `database.<domain> CNAME database.<domain>.cdn.cloudflare.net`
   - **Do not** point external DNS directly to `<tunnel-id>.cfargotunnel.com` for partial setup.

### Required token permissions to fully automate
- `Cloudflare One Connector: cloudflared` → Edit
- `Cloudflare One Connectors` → Edit
- `Argo Tunnel (Legacy)` → Edit (compat)
- `Account Zone Create` (needed if zone not yet created)
- `Zone DNS Edit` (only if automating DNS in Cloudflare zone)

### Fast blocker checks
- `GET /accounts/{account_id}/cfd_tunnel` success + status healthy
- `GET /zones?name=<domain>` returns at least one zone
- If zone list empty and cannot create zone (`com.cloudflare.api.account.zone.create` missing), tunnel cannot serve custom domain end-to-end yet

### Communication rule (user-experience)
If tunnel agent is healthy but zone is missing, state blocker explicitly as the single root cause; do not keep cycling app redeploys.

## Reachability triage matrix (fast)
Use this exact order before changing app code:
1. `curl http://127.0.0.1:8000/rest/v1/` on host (expect 401 without key)
2. `curl http://<LAN_IP>:8000/rest/v1/` from host/LAN
3. `curl http://<Tailscale_IP>:8000/rest/v1/` if tailscale used
4. `dig +short <public-subdomain> @8.8.8.8`
5. External/public check to `http://<public-subdomain>:8000/rest/v1/`

Interpretation:
- Steps 1–3 pass, 5 fails ⇒ external path issue (NAT/firewall/tunnel), not DB/migration.
- Step 4 fails ⇒ DNS issue.
- Step 1 fails ⇒ local container/service issue.

## Quick verification checklist
- `docker compose version` works
- `.env` exists and secrets are generated (not default placeholders)
- `docker compose ps` shows healthy services
- host ports are bound (`ss -lntp`)
- application receives valid DATABASE_URL
