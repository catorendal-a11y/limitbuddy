# Security review - 2026-10-09

Scope: PC companion, official-client setup, USB input, local configuration, provider HTTP requests, build dependencies and GitHub workflows. A source and dependency review with synthetic regression tests; not a penetration test of the owner's PC and no guarantee against compromise.

## Findings

| Finding | Impact and resolution |
| --- | --- |
| Provider requests followed default HTTP redirects | A redirect could forward Authorization. **All redirects are now rejected** (including HTTPS-to-HTTP and same-origin). Only allowlisted quota URLs open (`PROVIDER_ENDPOINTS` in `tools/host_security.py`; three as of v1.19.1-rc26, see addendum). Tests use the real opener with a synthetic HTTPS handler and verify no second request |
| Implicit current-directory executable discovery | A planted Codex executable could be picked from a project folder. Discovery now scans only absolute PATH directories, rejects the current directory and the monitor tree, and uses an absolute system PowerShell path. The official CLI remains a trusted local dependency |
| Unconstrained serial paths and terminal text | Serial settings reject network URLs and /dev/ traversal. Panel rejection details are not copied into host exceptions. Log lines strip terminal controls and are length-bounded. Config reads limited to 64 KiB |
| Mutable workflow references, old installer | Actions pinned to verified commits, dependency audit in CI, Dependabot updates. Build environment and source setup use pip 26.2.1 (older pip had advisories) |

## Verification

- 101 synthetic Python tests passed after the fixes (CI reports the current count). pip-audit on resolved runtime/release requirements and the isolated Windows build environment: no known advisories after the pip update.
- Static-analysis subprocess warnings reviewed: provider replies and telemetry are never executed, arguments are structured, the optional installer runs only after user selection. No remote command execution path found.
- Owner's machine (point in time): Defender real-time, behavior and downloaded-file protection on; all three firewall profiles on; the two monitor processes had zero listening sockets.

**Out of scope:** other installed applications, hardware USB attacks, exploitation of dependencies or the official CLI, real-credential provider login and API calls.

## Residual risks

- The optional Z.AI key is plaintext in local configuration. Any process under the same Windows account can read it, and equally the Claude Code login file below; the monitor cannot isolate credentials from installed malware.
- Git history and release archives exclude local keys, auth files, databases and logs.
- The extracted program and command scripts are not Authenticode-signed ([Windows trust](WINDOWS_TRUST.md)). Trust assumptions and private reporting: [Security](../SECURITY.md).

## Addendum: Claude plan quota endpoint (v1.19.1-rc26)

The host also calls the undocumented `GET https://api.anthropic.com/api/oauth/usage` (`fetch_claude` in `tools/quota_claude.py`). The three allowlisted endpoints are the Codex and Z.AI URLs plus this one.

| Aspect | Rule |
| --- | --- |
| When | Only for the selected Claude provider, when the statusline bridge supplies no fresh quota and the credentials file exists ([Providers](PROVIDERS.md#claude-code)) |
| Transport | URL in `PROVIDER_ENDPOINTS`; verified TLS, 20 s timeout, redirect-rejecting opener |
| Credential | Local Claude Code OAuth access token from `.credentials.json` in `~/.claude` (or `CLAUDE_CONFIG_DIR`); read only inside the quota worker subprocess, never the main host |
| Renewal | Within 10 min of `expiresAt` the worker runs the official Claude Code CLI as `claude auth status` (fixed arguments, absolute path from PATH or `~/.local/bin`, never the project folder; stdin/stdout/stderr discarded; 10 s timeout; no model turn). Claude Code rewrites its own file; LimitBuddy never writes it |
| Exposure | Token never written to settings, status or logs, never copied into replies or panel data, never a command-line argument; worker stdin carries only a `key` field, empty for Claude |
| Rate | Successful reply reused for 5 minutes (`CLAUDE_MIN_FETCH_SECONDS`); undocumented endpoint may change or rate-limit; failures show a quota notice |
| Residual | Same-account processes can already read `.credentials.json`; this adds no access but makes the monitor a token consumer. No model turn is started |
| Tests | `tests/test_aim_host.py`: headers, percentage mapping, missing token, renewal only near expiry, fixed renewal command, 5-minute reuse, with synthetic tokens. Tests never call the real endpoint; it was checked once on the owner's ESP32-P4 with the owner's login, without printing token or reply |

## Addendum: in-place update channel

**Settings > Install update** (`tools/self_update.py`, `tools/apply_update.ps1`) is a separate, credential-free channel.

| Aspect | Rule |
| --- | --- |
| Addresses | Only `UPDATE_RELEASES_URL` (this repository's release list) and assets under `UPDATE_DOWNLOAD_PREFIX`; redirects only to `release-assets.githubusercontent.com` or `objects.githubusercontent.com` over HTTPS (`open_update_request` in `tools/host_security.py`) |
| Integrity | The package must match its line in the same release's `SHA256SUMS.txt`. This detects corruption, not a compromised GitHub account; build provenance attestations remain the stronger manual check (`gh attestation verify`) |
| Bounds | 1 MB release list, 200 MB package, 800 MB extracted, 20 000 entries; only regular files under the package folder; absolute, `..`, backslash, drive and link entries are rejected |
| Swap | Runs after NOVA exits, from a copied script in `%TEMP%`, with explicit `-Root`/`-Staged` arguments; refuses any staged folder other than `<root>.next` with its marker. Private files are moved (keeping their current-user DACLs), never copied or uploaded. Failure restores the old folder |
| Scope | Windows package only; no administrator rights, service or scheduled task |
| Tests | `tests/test_self_update.py`: version order, release selection, address and redirect allowlists, checksum mismatch, unsafe archives, foreign staging folders, and a real PowerShell swap on temporary folders |

References: [HTTPRedirectHandler](https://docs.python.org/3/library/urllib.request.html#urllib.request.HTTPRedirectHandler), [shutil.which](https://docs.python.org/3/library/shutil.html#shutil.which).
