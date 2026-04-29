---
name: openclaw-telegram-bot-debug
description: Bring up OpenClaw Telegram channel and debug "bot online but not replying" by separating channel transport issues from LLM/auth issues.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [openclaw, telegram, troubleshooting, gateway, llm-auth]
---

# OpenClaw Telegram Bot Debug Playbook

## When to use
- User says Telegram bot is online but not replying.
- OpenClaw gateway is running, but Telegram behavior is inconsistent.

## 1) Configure token from file (safe path)

```bash
openclaw config set channels.telegram.enabled true --strict-json
openclaw config set channels.telegram.tokenFile '"/root/.config/faftech/openclaw_telegram_bot_token"' --strict-json
systemctl --user restart openclaw-gateway.service
```

## 2) Verify channel health (probe)

```bash
openclaw channels status --probe
openclaw status --deep
```

If probe says Telegram is enabled/configured/running, transport is likely alive.

## 3) Confirm transport separately from agent generation

Use direct message send test:

```bash
openclaw message send --channel telegram --target <chat_id> --message "tes" --json
```

Interpretation:
- If this works, Telegram outbound transport is OK.
- If user still sees no AI replies, problem is likely in model/auth path.

## 4) Inspect Telegram channel logs

```bash
openclaw channels logs --channel telegram --lines 200
```

Key pattern:
- `getUpdates ... 409 Conflict ... terminated by other getUpdates request`
  - Means there is another poller/session using the same token.

## 5) Inspect gateway logs for model/auth failures

```bash
openclaw logs --limit 300 --plain
```

Key pattern:
- `No API key found for provider "openai"`
- fallback/auth 401 errors

Meaning:
- Telegram channel may be healthy, but OpenClaw cannot generate model responses.

## 6) Operational fixes

- Resolve poller conflicts by ensuring only one active OpenClaw instance/channel consumer for that bot token.
- Configure valid LLM provider auth/profile for the active agent.
- Restart gateway and re-run probe.

## 7) Security hardening after bring-up

Temporary open policy is okay only for quick testing; then tighten:

```bash
openclaw config set channels.telegram.dmPolicy '"pairing"' --strict-json
openclaw config set channels.telegram.groupPolicy '"allowlist"' --strict-json
systemctl --user restart openclaw-gateway.service
openclaw security audit
```

## 8) Token rotation checklist (safe)

When changing Telegram bot token:
1. Overwrite token file and keep permission `600`.
2. Restart gateway service.
3. Verify bot identity changed via channel probe/logs (bot username should match new token owner).
4. If channel unexpectedly flips to webhook-mode errors after rotation, reset Telegram channel config to polling defaults and restart.

## 9) GitHub Copilot provider caveat (v2026.4.15)

If user asks to switch model to `github-copilot/*`:
- `openclaw models set github-copilot/...` may succeed, but generation can still fail during runtime token exchange.
- Use the **official auth command** from docs: `openclaw models auth login-github-copilot` (interactive TTY required).
- Non-interactive env token injection can appear configured in status, yet still fail with `Copilot token exchange failed: HTTP 404`.
- Treat `openclaw infer model run ...` as source of truth, not only auth status.

Docs-backed nuance that matters in practice:
- OpenClaw resolves env tokens in this order: `COPILOT_GITHUB_TOKEN` > `GH_TOKEN` > `GITHUB_TOKEN`.
- A regular GitHub token/PAT may be visible to OpenClaw but still fail Copilot exchange (404).
- Device-login flow stores a Copilot-compatible profile and is the most reliable path on this version.

Quick diagnostics:

```bash
# token prefix sanity (masked): many failing cases show gho_/ghp_ tokens
python - <<'PY'
from pathlib import Path
for p in ['/root/.hermes/.env','/root/.config/faftech/openclaw-model.env']:
    t=None
    for line in Path(p).read_text().splitlines():
        if line.startswith('COPILOT_GITHUB_TOKEN='):
            t=line.split('=',1)[1].strip().strip('"').strip("'")
            break
    print(p, 'prefix='+ (t[:4] if t else 'missing'), 'len=' + (str(len(t)) if t else '0'))
PY

openclaw infer model auth status --json
openclaw infer model run --local --model github-copilot/gpt-5.3-codex --prompt "Reply exactly: OK" --json
```

If run test fails with exchange 404:
1. run interactive login on host TTY:
   `openclaw models auth login-github-copilot --yes`
2. retest infer run
3. if still failing, switch to another provider with known-good key/profile.

## 10) Systemd user service auto-start (for VPS reboot survival)

OpenClaw gateway should run as a **user systemd service** (not root), so it survives reboots independently.

### Key constraints discovered empirically
- Running as `root` but serving a non-root user session → `DBUS_SESSION_BUS_ADDRESS` missing on reboot.
- Service `ExecStart` and all `Environment=` paths must point to the **actual user home**, not `/root`.
- `loginctl enable-linger <user>` is **required** — without it, user systemd services die after user logout.
- Use `XDG_RUNTIME_DIR=/run/user/<uid>` when invoking `systemctl --user` remotely.

### Setup (tested on Ubuntu, user=fikri, uid=1000)

```bash
# 1. Ensure linger is enabled (survives user logout/reboot)
loginctl enable-linger fikri

# 2. Copy and fix service file to user's systemd dir
mkdir -p /home/fikri/.config/systemd/user
cp /root/.config/systemd/user/openclaw-gateway.service /home/fikri/.config/systemd/user/

# 3. Fix all /root paths → /home/fikri paths in ExecStart + Environment vars
#    Also fix EnvironmentFile path (must be under user's home)
#    Key vars: HOME=/home/fikri, TMPDIR=/tmp/openclaw, PATH=... all under /home/fikri

# 4. Symlink for WantedBy=default.target
mkdir -p /home/fikri/.config/systemd/user/default.target.wants
ln -sf /home/fikri/.config/systemd/user/openclaw-gateway.service \
       /home/fikri/.config/systemd/user/default.target.wants/

# 5. Daemon-reload + enable
sudo -u fikri bash -c 'XDG_RUNTIME_DIR=/run/user/1000 systemctl --user daemon-reload'
sudo -u fikri bash -c 'XDG_RUNTIME_DIR=/run/user/1000 systemctl --user enable openclaw-gateway.service'

# 6. Verify
sudo -u fikri bash -c 'XDG_RUNTIME_DIR=/run/user/1000 systemctl --user is-enabled openclaw-gateway.service'
# Expected: enabled

# 7. Status check
sudo -u fikri bash -c 'XDG_RUNTIME_DIR=/run/user/1000 systemctl --user status openclaw-gateway.service'
```

### Critical path fixes (most common failure mode)

Wrong (will break on reboot):
```
ExecStart=/root/.hermes/node/bin/node .../openclaw/dist/index.js gateway
Environment=HOME=/root
EnvironmentFile=-/root/.config/faftech/openclaw-model.env
```

Correct (survives reboot):
```
ExecStart=/home/fikri/.hermes/node/bin/node .../openclaw/dist/index.js gateway
Environment=HOME=/home/fikri
EnvironmentFile=-/home/fikri/.config/faftech/openclaw-model.env
```

### Verifying auto-start works

```bash
# Simulate reboot conditions (no active user session):
sudo -u fikri bash -c 'XDG_RUNTIME_DIR=/run/user/1000 systemctl --user is-active openclaw-gateway.service'
# Should return: active

# Or check the actual log after a real reboot:
cat /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log | grep 'gateway.*ready'
```

## Practical lessons
- `channels status --probe` can show channel healthy while replies still fail due to missing LLM auth.
- Always separate **transport** validation (`message send`) from **generation** validation (`agent` run + logs).
- Token rotation can leave stale channel state if config/mode is not rechecked after restart.
- For this workflow, logs are the decisive source of truth.
- Systemd user service paths must match the target user home — `/root` paths in a non-root user service will silently fail on reboot.