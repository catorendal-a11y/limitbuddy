# Security review — 2026-10-09

Scope: the PC companion, official-client setup, USB input, local configuration, provider HTTP requests, build dependencies and GitHub workflows. This is a source and dependency review with synthetic regression tests, not a full penetration test of the owner's PC or a guarantee against compromise.

| Finding | Impact and resolution |
| --- | --- |
| Provider requests followed default HTTP redirects | A redirect from the authenticated endpoint could forward Authorization. All redirects are now rejected, including HTTPS-to-HTTP and same-origin redirects. Only allowlisted quota URLs can be opened (`PROVIDER_ENDPOINTS` in `tools/host_security.py`; three as of v1.19.1-rc25, see the addendum below). Tests exercise the real opener using a synthetic HTTPS handler and verify that no second request occurs. |
| Implicit current-directory executable discovery | A planted Codex executable could be selected from a working/project folder. Discovery now scans only absolute PATH directories, rejects the current directory and the monitor tree, and uses an absolute system PowerShell path. The official CLI remains a trusted local dependency. |
| Serial paths and terminal text were insufficiently constrained | Serial settings now reject network URLs and /dev/ traversal. Panel rejection details are not copied into host exceptions. Displayed log lines remove terminal controls and have a length bound. Configuration reads are limited to 64 KiB. |
| Mutable workflow references and old package installer | Actions are pinned to verified upstream commits, dependency audit is added to CI and Dependabot proposes reviewed updates. The isolated build environment and source setup use pip 26.2.1; the older builder pip had known advisories. |

At the time of this review, 101 synthetic Python tests passed locally after these fixes; CI reports the current count. Resolved runtime/release requirements and the actual isolated Windows build environment were checked with pip-audit. No known dependency advisories remained after updating pip. Static analysis warnings about subprocess use were reviewed: provider replies and telemetry are not executed, subprocess arguments are structured, and the optional installer runs only after user selection. No remote command execution path was found in the reviewed monitor code.

On the owner's machine, Defender real-time, behavior and downloaded-file protection were enabled; all three firewall profiles were enabled. The two running monitor processes had zero listening network sockets. These are point-in-time observations, not a scan of every other installed application. Provider login and cloud API requests were not exercised with real credentials in the security tests. Hardware USB attacks and exploitation of dependencies or the official CLI are outside the verified test scope.

The optional Z.AI key remains plaintext in local configuration. A process with the same Windows account can read it, and can equally read the Claude Code login file described below; the monitor cannot isolate credentials from already installed malware. The public Git history and release archive exclude local keys, authentication files, databases and logs. The extracted program and its command scripts are not Authenticode-signed (see [Windows trust](WINDOWS_TRUST.md)). See [Security](../SECURITY.md) for the remaining trust assumptions and private reporting procedure.

## Addendum: Claude plan quota endpoint (v1.19.1-rc25)

The host now also calls the undocumented `GET https://api.anthropic.com/api/oauth/usage` to read the Claude plan windows (see `fetch_claude` in `tools/aim_host.py`). The three allowlisted outbound quota endpoints are therefore the Codex and Z.AI URLs plus this one.

- **When it runs.** Only for the selected Claude provider, when the documented statusline bridge supplies no fresh quota and the credentials file exists. See [Providers](PROVIDERS.md#claude-code).
- **Same transport rules.** The URL is in `PROVIDER_ENDPOINTS`; requests use verified TLS, a 20-second timeout and the redirect-rejecting opener, so the Authorization header cannot follow a redirect.
- **Credential source.** The bearer token is the local Claude Code OAuth access token from `.credentials.json` in the Claude configuration directory (`~/.claude`, or `CLAUDE_CONFIG_DIR` when set). It is read only inside the quota worker subprocess, never in the main host process.
- **No persistence or exposure.** The token is not written to settings, status or logs, is not copied into replies or panel data, and is never passed as a command-line argument. The worker's stdin carries only a `key` field, which is empty for Claude.
- **Rate.** A successful reply is reused for five minutes (`CLAUDE_MIN_FETCH_SECONDS`), so the endpoint is queried at most about every 5 minutes. The endpoint is undocumented and may change or rate-limit; failures surface as a quota notice.
- **Residual risk.** Any process under the same Windows account can read `.credentials.json` directly; this feature adds no new access, but it does make the monitor a consumer of that token. The Claude entry never starts a model turn.
- **Test scope.** `tests/test_aim_host.py` covers the request headers, percentage mapping, missing-token handling and the five-minute reuse with synthetic tokens and replies. Automated tests never call the real endpoint; it was checked once on the owner's ESP32-P4 with the owner's own login, without printing the token or the reply.

Implementation references: [Python HTTP redirect handling](https://docs.python.org/3/library/urllib.request.html#urllib.request.HTTPRedirectHandler), [Python executable search behavior](https://docs.python.org/3/library/shutil.html#shutil.which).
