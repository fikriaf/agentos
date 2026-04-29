---
name: browser-harness
description: Direct browser control via CDP (Chrome DevTools Protocol). Connects to the user's already-running Chrome for automation, scraping, testing, and web interaction.
---

# browser-harness

Direct browser control via CDP. Connects to user's Chrome, not a separate browser instance.

## Install & Setup

```bash
# First time (already done)
cd /opt/browser-harness
uv tool install -e .

# Connect to user's Chrome
browser-harness --setup
```

## Usage

```bash
# Basic interaction - invoke as browser-harness (on $PATH)
browser-harness -c '
new_tab("https://example.com")
wait_for_load()
print(page_info())
'

# Screenshot and verify
browser-harness -c '
capture_screenshot()
'

# Click by coordinates (preferred method)
browser-harness -c '
capture_screenshot()  # find target first
click_at_xy(x, y)     # click at coordinates
capture_screenshot()  # verify it worked
'
```

## Available Skills

- `interaction-skills/connection.md` — startup, tab visibility
- `interaction-skills/tabs.md` — tab management
- `interaction-skills/uploads.md` — file uploads
- `interaction-skills/dialogs.md` — alert/confirm dialogs
- `interaction-skills/downloads.md` — download handling
- `agent-workspace/domain-skills/` — site-specific skills (TikTok, Polymarket, etc.)

## Key Concepts

1. **Coordinate clicks** — Use `capture_screenshot()` → find target → `click_at_xy(x, y)` → verify. Don't use selectors first.
2. **First navigation is `new_tab(url)`** — Not `goto_url()` (clobbers user's active tab)
3. **Use screenshots** — Fastest way to verify state, find targets, detect errors
4. **Contribute back** — If you learn non-obvious site patterns, PR to `agent-workspace/domain-skills/<site>/`

## Remote Browsers (Browser Use Cloud)

```bash
# Start remote browser (for headless servers or parallel agents)
browser-harness -c '
start_remote_daemon("work", proxyCountryCode="de")
'

# Then use with BU_NAME
BU_NAME=work browser-harness -c '
new_tab("https://example.com")
'
```

## Maintenance

- `browser-harness --doctor` — version, daemon state, update check
- `browser-harness --setup` — re-run browser attach flow
- `browser-harness --update -y` — update to latest when available

## Architecture

```
Chrome / Browser Use cloud -> CDP WS -> browser_harness.daemon -> /tmp/bu-<NAME>.sock -> browser_harness.run
```

Protocol: one JSON line each way. Requests: `{method, params, session_id}` for CDP or `{meta: ...}` for daemon.