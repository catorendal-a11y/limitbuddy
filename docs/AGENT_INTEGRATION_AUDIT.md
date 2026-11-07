# Agent integration audit

> [!NOTE]
> Historical. 2026-10-15, installed app and P4 firmware v1.19.1-rc2 (the **rc2 baseline**; current is v1.19.1-rc25). Rc3 added ZCode hooks, an independent live reader, setup-definition checks, legacy Codex wrapper migration and visible USB delivery health (RELEASE_NOTES.md). Not current behavior.

Quota readiness, token activity, lifecycle events, USB acknowledgment and permission control are independent capabilities. At rc2, live monitoring was not established for all three providers.

| Capability (rc2) | Codex | Claude Code | ZCode |
| --- | --- | --- | --- |
| Selected in installed host | Yes | No | Yes |
| Quota physically verified | Yes | No | Yes |
| Lifecycle adapter in source | Yes | Yes | No (added in rc3) |
| Installed lifecycle opt-in | Enabled | Disabled | Unavailable |
| Eligible live records | 0 | 0 | Unavailable |
| Real client event reaches physical view | Unproven | Unproven | Unsupported |
| Production P4 tool approval | Disabled | Disabled | Disabled |

## Findings

- **Codex:** CLI `0.162.0-alpha.17.2`; read-only `hooks/list` showed all ten events enabled and trusted: inventory and trust, not execution in the active conversation. Hook commands used an older dev Python instead of the packaged `AI-Monitor-Events.exe` (synthetic events handled in 109-187 ms), a portability risk, not a proven cause. No records stored; the app-server started after the hook file, so "process predates hooks" was unsupported. A valid check needs a genuine client action, fixed-schema record, correlated USB ack and the physical view. Never overwrite hook trust or force-restart a client ([contract](https://learn.chatgpt.com/docs/hooks)).
- **Claude:** marker disabled, absent from selected-provider health. The isolated observer produced WORKING, WRITING, COMPLETED and kept no prompt or tool input. Activation stays explicit; tool authorization is a separate disabled domain ([hooks](https://code.claude.com/docs/en/hooks)).
- **ZCode (fixed in rc3):** the [official hooks](https://zcode.z.ai/en/docs/hooks) (SessionStart, UserPromptSubmit, PreToolUse, PermissionRequest, PostToolUse, PostToolUseFailure, Stop) made an adapter feasible. Requirements: explicit user-level or plugin setup, keep unrelated config and hook enablement, no decisions/context, bounded input and storage, do not reuse Claude's settings (legacy settings need explicit import; project hooks ignored), no per-subagent coverage.

## Monitoring gaps at rc2

| Gap | Impact |
| --- | --- |
| `setup_report()` used only a Codex opt-in marker | Loaded hook definition, executable and trust unchecked |
| `reporting` = eligible local metadata exists | Not proof a client emitted it or the display received it |
| Live ack/error not exported to `HostStatus` | Failed live channel hidden behind quota-ready (30 s backoff only) |
| Live sampling shared the numeric reader | Stalled numeric source could delay events |
| Task hook metadata = requested actions | Not completed work, test success or approvals |

## Verification

Five synthetic integration tests (observer, sampler, serial-owner method; temp config; correlated serial fixture). Full run: **505 Python tests** in 42.5 s and all **four native UI CTest targets** passed (`work/verification/deep-agent-python.log`). No installed activity directory, real USB, model turn, credential access, provider activation, hook-trust edit, flash or app replacement.
