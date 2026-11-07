# Security

Firmware needs no provider credentials. The Python companion reads local credentials at runtime and sends quota/activity over USB. For Claude quota it reads the local Claude Code login (`.credentials.json` in the Claude config folder) only inside the quota worker; the token is never logged or stored by LimitBuddy. Token activity uses read-only queries of numeric counters and identifiers.

> [!WARNING]
> Do not commit `tools/aim_host.json`, environment files, CLI auth, keys, databases or logs. The example key stays empty, and `.env.example` is documentation only (never auto-loaded). Keep logs private even when sanitized.

Tests use synthetic credentials and responses. Do not mix debug serial logging with a production companion on one port. Provider responses and USB messages are untrusted: keep size limits, type validation and bounded buffers.

## Host protections

| Area | Protection |
| --- | --- |
| Network | No listening service; outbound HTTPS and local USB serial only. The optional official CLI runs over local stdin/stdout. |
| Quota requests | Three fixed HTTPS endpoints (Codex, Z.AI, Claude), verified certificates, 20-second timeout. All redirects are rejected so auth headers cannot follow to another origin or HTTP. |
| Codex discovery | Ignores relative PATH entries, the current directory and the project tree; PowerShell uses its absolute system path. Install and sign-in need explicit user choice and trust the official client. |
| USB and logs | Ports limited to COM or /dev/ serial paths (traversal and URLs rejected). Panel errors are generic; control characters and oversized log entries are removed. Config reads capped at 64 KiB. |
| CI | Pinned commit identities, read-only CI permissions, dependency auditing, Dependabot updates. Source setup upgrades pip only inside the project's virtual environment. |

These do not protect against malware running as your Windows user, a modified local executable or a compromised provider account. The optional Z.AI key is stored as plaintext in local configuration: keep it in a private folder, never upload it, and use a revocable separate key. A checksum detects corruption but cannot authenticate a package if ZIP and checksum come from an untrusted source; download from this repository's Releases. Windows executables are currently unsigned ([Windows trust](docs/WINDOWS_TRUST.md)).

[Review evidence and limits](docs/SECURITY_REVIEW.md) · [GitHub permissions, external contributions and release safeguards](docs/GITHUB_SECURITY.md)

## Reporting

If private reporting is enabled on the GitHub repository, use **Security > Report a vulnerability**; otherwise contact the owner privately through a channel on their GitHub profile. No exploit details, credentials or account data in public issues. This package lists no maintainer email or response deadline.

Include version, impact and a minimal synthetic reproduction. Revoke exposed keys with their provider first; deleting a file does not remove it from Git history. Fixes target the current release; older forks may need backports.
