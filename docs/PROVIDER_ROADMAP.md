# Provider expansion plan

> [!NOTE]
> Plan, not a claim that bridge-only providers work automatically. Current: v1.19.1-rc28 (baseline v1.12.0). Eight selectable tools, no first-run defaults. Capabilities: [PROVIDERS.md](PROVIDERS.md).

Start a task with `docs/PROVIDERS.md`, this plan and the relevant step. One reviewable PR per step. Python suite for host changes; firmware build plus `scripts/run_tests.py --ui` for firmware/UI.

## Shared constraints

- Reuse the patterns in `tools/provider_catalog.py`, `aim_host.py`, `token_activity.py`, `local_activity.py`, `telemetry_bridge.py`.
- Explicit selection only; missing credentials never enable another tool.
- Capability and availability are reported separately. Context occupancy, billing, request counts and quota percentages are different metrics.
- Documented interfaces or reviewed local formats only: no browser cookies, no decrypting app credentials, no personal quota inferred from an org report.
- **Sole approved exception:** Claude's undocumented `GET https://api.anthropic.com/api/oauth/usage` ([details](PROVIDERS.md#claude-code)); existing Claude Code token, quota worker only, allowlisted in `tools/host_security.py`. Treat as breakable.
- Synthetic, bounded fixtures. No prompts, auth files, transcripts, logs or raw IDs in commits/releases. Persist only whitelisted numbers or opted-in fixed lifecycle states with hashed IDs.
- Test: first-sample baselines, repeated IDs, streaming updates, counter decreases, corrupt records, staleness, reconnects, permission failure, missing source.
- Firmware has eight source bits, eight views, three quota rows per view. A ninth provider needs a versioned protocol-capacity PR; never reuse a bit.
- Keep provider branding, warning meanings, theme/companion settings and the RGB565+A8 asset strategy. v1.12.0 used about 85% of the app partition; re-measure.

## Steps

| # | Step | Status | Needs |
| --- | --- | --- | --- |
| 1 | Harden Codex onboarding | Implemented; follow-up PR open | none |
| 2 | Capability/readiness contract | Planned, before more bridges | none |
| 3 | Claude and Gemini robustness | Planned | 2 |
| 4 | Copilot SDK bridge package | Planned | 2 |
| 5 | OpenCode adapter | Implemented in v1.17.0 | 2 |
| 6 | Cursor and Antigravity feasibility | Research gate | 2 |

Order: 1, 2, then 3 and 4 as separate PRs, then 5/6 decisions. Steps 3-6 share registry/bridge files; rebase and re-test before merging.

| # | Remaining work | Validate | Rollback |
| --- | --- | --- | --- |
| 1 | Test client versions/OSes with consenting testers; uniform update/retry/cancel status; keyring/file auth and API-key-only failure; readiness without account details. Install and sign-in stay user actions. | Synthetic subprocess tests, then opt-in account checks; never install or log in in CI | Disable onboarding action; keep selections, CLI path, fallback |
| 2 | Registry gets activity/quota capabilities and setup requirements; adapters return typed readiness (unsupported, missing source, setup required, stale, temporarily failed). No percentage for unsupported quota; no second architecture. | Host tests; one source up while another is missing; selection change while connected; no implicit defaults. Exit: Status, setup and panel agree | Keep adapter results until consumers migrate |
| 3 | Discovery checks and version-specific fixtures; watch the OAuth endpoint for schema/policy changes (keep fail-closed activity-only fallback); idempotent bridge install/remove, never replacing custom hooks; evaluate Gemini hooks/OpenTelemetry as an opt-in bridge. CLI settings change only via explicit reviewed action. | OAuth reply with missing/invalid windows, 401/429 backoff, token-free log, JSONL rewrite/truncation, repeated IDs, subagent duplication, Unicode paths, permission errors, install/remove round trip | Restore backed-up settings; keep local activity parsing |
| 4 | `integrations/copilot/`: runnable SDK bridge that accumulates per-session tokens and forwards the stdin schema; official quota fields only when available in the same authenticated context; label coverage "SDK sessions". No repo GitHub token or model requests in install/tests. | Event replay, resume/dedup, restarted counters, host outage, rejected credentials, unlimited entitlements, reset dates, packaged smoke test | Disable the helper; ingestion stays |
| 5 | Done: `tools/opencode_activity.py`, bounded read-only numeric adapter for V1/V2 schemas (hashed IDs, imported-session baselines, synthetic tests). Quota unsupported. Possible SDK bridge in `integrations/opencode/` ([PROVIDERS.md](PROVIDERS.md#opencode)). | n/a | Remove connector without reusing its bit |
| 6 | Neither Cursor's team Admin API nor Antigravity's interactive usage command is a supported personal real-time source. Check docs, permissions, scope, semantics; go/no-go note each; one provider per PR, only after a stable permitted source is verified. | Personal vs team scope labeled; unknown permissions fail without fabricated numbers; no unrelated login/cookie access; staleness checked | Keep choice and manual bridge |

Step 3 context: Claude quota logic is `fetch_claude` and `claude_quota` in `tools/aim_host.py`. Gemini has local usage/telemetry but no quota adapter. Step 4: do not advertise editor-wide Copilot monitoring.

## Acceptance for every PR

1. Guide states what is automatic and what is user-mediated.
2. `python -m unittest discover -s tests -p "test_*.py"`; firmware build and `python scripts/run_tests.py --ui` for firmware/UI changes.
3. Other providers still work, no implicit default, no personal data in Git or the release ZIP.
4. A maintainer with the app does the opt-in integration check; synthetic fixtures are not account/physical validation.
5. Update capability table, roadmap status and release notes together.

To change scope, record reason and evidence, update dependencies and criteria, and mark unfinished work planned/blocked, never "supported".

References: [Codex auth](https://learn.chatgpt.com/docs/auth), [Codex env](https://learn.chatgpt.com/docs/config-file/environment-variables), [Claude statusline](https://code.claude.com/docs/en/statusline), [Gemini hooks](https://geminicli.com/docs/hooks/reference/), [Copilot SDK](https://github.com/github/copilot-sdk/blob/main/docs/features/usage-and-billing.md), [OpenCode SDK](https://docs.opencode.ai/docs/sdk/), [Cursor Admin API](https://docs.cursor.com/en/account/teams/admin-api), [Antigravity usage](https://www.antigravity.google/docs/cli/commands/usage/).
