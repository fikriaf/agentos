---
name: kali-tools-on-ubuntu-safe-path
description: Safely handle requests to install all Kali tools on Ubuntu/Debian hosts; detect incompatibility, avoid breaking base system, rollback repo changes, and pivot to container/chroot/VM strategy.
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [kali, ubuntu, apt, dependency-conflict, rollback, container]
---

# Kali Tools on Ubuntu: Safe Path

## When to use
Use when user asks to install "all Kali tools" (e.g., `kali-linux-everything`) on a non-Kali host, especially Ubuntu LTS.

## Why this exists
Directly mixing Kali rolling repo into Ubuntu often fails or risks system breakage due to core dependency mismatches (e.g., `libc6`, `base-files`, t64 transitions). Must verify compatibility first and preserve host stability.

## Procedure
1. **Baseline discovery**
   - Check distro and privileges:
     - `cat /etc/os-release`
     - `whoami && id -u`
   - Confirm apt availability: `command -v apt && apt --version`
   - Check resources up front if full install is requested:
     - `df -h /`
     - `free -h`

2. **Attempt with safe pinning (diagnostic only)**
   - Install prerequisites: `apt-get update && apt-get install -y curl gnupg ca-certificates`
   - Add Kali key and source list.
   - Add low-priority apt pin for `kali-rolling` (e.g., priority 50).
   - `apt-get update`

3. **Preflight simulation before full install**
   - Run simulated install:
     - `apt-get -s -t kali-rolling install kali-linux-everything`
   - Inspect for blockers like:
     - `libc6 (>= 2.38)` on Ubuntu 22.04 (`2.35`)
     - `libc6 breaks base-files (< 13.3~)`
     - many “not installable / not going to be installed” dependencies

4. **If core dependency conflict appears, STOP full install**
   - Do **not** force with aggressive apt flags.
   - Explain incompatibility clearly.

5. **Rollback immediately to safe host state**
   - Remove Kali repo/pin files.
   - `apt-get update`
   - Verify candidate versions are back to native distro (e.g., `apt-cache policy libc6`).

6. **Pivot to isolated Kali environment (recommended path)**
   - Install and start Docker on host (or use VM/chroot):
     - `apt-get update && apt-get install -y docker.io`
     - `systemctl start docker && systemctl is-active docker`
   - Create Kali container:
     - `docker pull kalilinux/kali-rolling:latest`
     - `docker run -d --name kali-everything --restart unless-stopped kalilinux/kali-rolling:latest sleep infinity`
   - Start full install inside container in background:
     - `docker exec kali-everything bash -lc 'export DEBIAN_FRONTEND=noninteractive; apt-get update && apt-get install -y kali-linux-everything'`
   - Monitor progress (long-running):
     - `docker top kali-everything`
     - `docker exec kali-everything bash -lc 'du -sh /var/cache/apt/archives'`
     - `docker exec kali-everything bash -lc 'df -h /'`

7. **Report status and constraints clearly**
   - State whether process is running/completed/failed.
   - Include current disk headroom and note this install can consume tens of GB.
   - If still running, provide exact command/process handle for follow-up checks.

## Verification checklist
- `apt-get update` runs clean after rollback.
- `apt-cache policy libc6` candidate points to Ubuntu repos only.
- No partial Kali meta-packages installed (`dpkg -l | grep '^ii\s+kali-'`).
- User receives explicit next-step options.

## Pitfalls
- Writing directly to `/etc/apt/*` may require terminal/root flow; file tools can be blocked for sensitive paths.
- `kali-linux-everything` is huge; even in isolated env, expect very large disk/time requirements.
- Don’t leave Kali repo configured on Ubuntu if install is abandoned/fails.
- In minimal Kali containers, common diagnostics (`ps`, `pgrep`) may be absent; prefer `docker top <container>` for process visibility.
- For long installs, use background execution + periodic polling to avoid command timeouts and keep user updated.
- During package trigger phase, host/container disk usage may temporarily spike; monitor free space and proactively warn users before low-space conditions.

## After-install validation (required)
1. Confirm meta-packages are fully installed (not just unpacked):
   - `dpkg -s kali-linux-everything | grep '^Status'` must be `install ok installed`
   - Optionally check `kali-linux-default` and `kali-tools-top10`
2. Verify host safety state:
   - Ensure Ubuntu host still uses native repos and healthy `apt-get update`
3. Run a smoke test on key tools (not every package):
   - Presence + quick version/help checks for representative tools (`sqlmap`, `nikto`, `hashcat`, `john`, `aircrack-ng`, `tshark`, `nuclei`, etc.)
4. Report explicitly that smoke test != exhaustive validation of all Kali tools.

## Known container-specific caveats
- Some tools may fail in Docker despite successful installation:
  - `nmap` can return `Operation not permitted` due to container capability restrictions.
  - `msfconsole` can fail from Ruby/Bootsnap path traversal issues (e.g., symlink loops) in certain images.
  - `amass` may warn/fail if `libpostal` parser/language-classifier data is incomplete.
  - `zap-baseline.py` wrapper may be missing in Kali package even when `zaproxy` is installed.
- Treat these as runtime-environment issues first; validate command availability separately from full functional execution.

## Runtime remediation playbook (post-install)
Apply these only after reproducing errors.

1. **Fix `nmap: Operation not permitted` in container**
   - Root cause: file capabilities on `/usr/lib/nmap/nmap` can be incompatible with container constraints.
   - Remediation:
     - `setcap -r /usr/lib/nmap/nmap`
   - Verify:
     - `nmap --version` returns rc=0.

2. **Fix `msfconsole` ELOOP / bootsnap path scan failure**
   - Root cause: Ruby bootsnap load-path cache traverses symlink loops under `llvm` dev paths.
   - Remediation (stable workaround): disable bootsnap load path cache in Metasploit boot config.
     - Edit `/usr/share/metasploit-framework/config/boot.rb`
     - Set `load_path_cache: false`
   - Verify:
     - `msfconsole --version` returns rc=0.

3. **Fix `amass` libpostal model errors**
   - Symptoms include:
     - `Could not find parser model file`
     - `Error loading address parser module`
   - Remediation:
     - `libpostal_data download parser /usr/share/libpostal`
     - `libpostal_data download language_classifier /usr/share/libpostal`
   - Verify:
     - `amass -version` returns clean output and rc=0.

4. **Provide `zap-baseline.py` compatibility when missing**
   - If `zaproxy` exists but `zap-baseline.py` is missing, add a local wrapper (e.g., `/usr/local/bin/zap-baseline.py`) that invokes:
     - `zaproxy -cmd -quickurl <target> -quickout /tmp/zap_quick_report.html`
   - Verify:
     - `zap-baseline.py -t https://example.com` returns rc=0 and writes report.

## Final targeted verification commands
Run after remediation:
- `nmap --version`
- `msfconsole --version`
- `amass -version`
- `zap-baseline.py -t https://example.com`
