# LimitBuddy v2 foundation validation

Direction: **Physical AI Agent Companion & Monitor**. Quota/activity, live agent interaction, companion rendering, transport and hardware capability stay separate domains; the USB/AIM1 snapshot is not a permission or live-agent container. Plan: [COMPANION_V2](../plans/COMPANION_V2.md). Current state: [V2_STATUS](V2_STATUS.md).

> [!NOTE]
> Dated log condensed into tables. "Native" = synthetic/native tests, not physical evidence. Counts are Python regression totals then. Device = identified P4 (JC4880P443C_I_W_Y) on COM6; flashes were app-only (NVS, bootloader, partition table untouched) with full previous-app backup, digest check and restored host. Dates are 2026-10-13/14 unless noted.

## Not yet validated

- Physical S3 (panel, touch, flashing); SD detection/activation.
- Physical touch gestures and fault injection; 24 h loop-task soak; any long soak.
- Physical enrollment (code comparison, hold, reboot, unplug), real permission approval/denial, unplug-during-hold, interactive Claude hook, provider approval (user postponed).
- Genuine Codex lifecycle hook delivery at these checkpoints (later rc4 evidence: [V2_STATUS](V2_STATUS.md)); real USB serial timing/backpressure/unplug for live metadata.
- Runtime C6 beyond the historical schema 1 run; HCI/GATT/pairing/Claude Desktop (Bluetooth excluded).
- Fresh-PC/clean-profile install; Windows publisher signing; published release or push.
- Production PPA, scanout FPS, cached-path peak memory/latency, p95 and all-pose asset timings, runtime memory with the agent/notification screens, CI result for the integrated candidate.

## Diagnostics and graphics (v1.19.0)

| Item | Validated | Result |
| --- | --- | --- |
| `get_hardware` | Bounded read-only USB command: flash/PSRAM size, image and app partition size, internal/external heap total/free/min/largest, chip revision, CPU/flash frequency, SDK, display buffers | Free app space = `partitionBytes - applicationBytes`; allocator capacity separate from physical PSRAM (S3 XIP) |
| Capability | Compiled ESP-Hosted/PPA vs runtime detection | C6 `not-probed`, version unknown, production PPA inactive, SD pending; no coprocessor init/update |
| Host flow | One validated snapshot after capability handshake; no second COM connection; needs `hardwareDiagnostics: true`; invalid/unsolicited/mismatched-boot replies rejected; lost connection clears sample | Pass |
| Collectors | `scripts/collect_device_baseline.py --board guition-p4 --port COM_NUMBER --output work/hardware.json`, `collect_graphics_baseline.py ... --seconds 10 --output work/graphics.json` | Stop the attached host first; auto port rejected; whitelisted fields |
| Graphics envs | `esp32p4-graphics`, `esp32s3-waveshare-43-graphics`, `esp32p4-ppa-benchmark` | Compiled; production timing off; `get_graphics`/`get_ppa_benchmark` start nothing and never renew the lease; flush chunks are not FPS; PPA timeout keeps DMA resources until reboot; S3 timing/orientation pending |

`startupMemory` (four one-time readings; last includes all initial screens and possibly concurrent USB task allocations):

| Checkpoint | Internal free | Internal largest | PSRAM free | PSRAM largest |
| --- | ---: | ---: | ---: | ---: |
| Before display | 434,584 | 344,052 | 33,551,856 | 33,030,132 |
| After display | 433,440 | 344,052 | 32,014,208 | 31,981,556 |
| After LVGL/HAL | 428,764 | 344,052 | 29,710,160 | 29,360,116 |
| After screens/companion | 186,932 | 102,388 | 29,710,160 | 29,360,116 |

## Foundation (v1.18.5 analysis, v1.19.0)

| Item | Result |
| --- | --- |
| Analysis fixes | Job Object containment (synthetic real-process tests), coalesced desktop reads, stalled-reader messages, initial brightness recovery keeping user overrides. Blocked reader still needs host/app restart. |
| Tests | 306 Python; strict C++ protocol/settings/live-agent + both boards; native LVGL P4/S3; both production builds. Follow-up: 313 Python (incl. real per-user Windows IPC/tray). |
| Builds | P4 app 4,570,004 / 6,553,600 B, static RAM 100,068 / 327,680 B (follow-up: P4 4,570,048; S3 4,619,502 B, static RAM 100,068 / 107,460). Linker RAM is not heap. |
| Flash | Byte-for-byte verified; layout matched; NVS untouched. Plain reset did not start the app, watchdog reset did (P4 flasher now requests it; S3 keeps UART hard reset). Flasher checks board identity after write+reboot; re-enumeration retries bounded, never switch port or repeat writes; unconfirmed boot never advises erasing settings. |
| Telemetry | v1.19.0; flash 16,777,216 B; PSRAM 33,554,432 B; app 4,604,272 B (later 4,604,320), free partition 1,949,328 B (later 1,949,280). PSRAM free/largest 29,710,160 / 29,360,116; internal heap free/largest 228,120 / 102,388 (single point, not minima). Heap can grow when the startup loop task releases its stack. |
| Packaging | Fresh portable Windows package, both images, hash-verified Qt sources; GUI/runtime/flasher checks passed; not a fresh-PC install, not signed. Desktop flasher install on COM6 verified; the EMBER host (COM6 owner) was stopped for the test only. |
| Physical diagnostics | Standalone C6 + isolated PPA on P4: C6 presence, versions, controller RPC measured; PPA/CPU rotation 8/8 byte-identical; 324 Python tests. [P4_HARDWARE_BENCHMARKS](P4_HARDWARE_BENCHMARKS.md) |

## Companion assets and cache

| Stage | Validated | Result |
| --- | --- | --- |
| Assets | Twelve NOVA/ORBIT poses, union-alpha crop per companion, export verified against committed C++ (`node scripts/export_companion_frames.cjs ...`, `python scripts/benchmark_asset_codecs.py ... --cc gcc`; needs Node, Sharp, pinned LVGL, C compiler) | 4,396,320 -> 3,349,656 B (-23.8%); built-ins stay fallback |
| Host-only sizes (12 frames) | Raw 3,349,656; RLE 1,925,271; LZ4 519,579; Deflate 249,490 B | Sizes only, no ESP32 timing; chose no codec |
| Version-1 manifest + two-slot cache (native) | Rejects bad sizes, hashes, traversal, duplicates, invalid UTF-8, case aliases, reserved names; failed decode cannot overwrite a pinned frame | Pass |
| Target checkpoint | 12 poses x 4 codecs, 5 SHA-256-verified decodes each; PSRAM pool + real hash/decode; six NOVA loads, corruption, pin retention; native renderer/LVGL binding both boards | LZ4 selected; 333 Python tests; builds OK; original app restored. [COMPANION_RUNTIME_FORMAT](COMPANION_RUNTIME_FORMAT.md) |
| Production cache (2026-10-13) | Normal P4 renders verified LZ4 via startup PSRAM cache; native pixel comparison with raw art, stable origins, reuse, retirement, integrity fallback; S3 keeps raw images | 355 Python tests; both builds; cache active 630,528 B, 1 verified decode, 0 failures, 20,513 us; app 4,611,328 -> 2,347,328 B; installed flasher images/manifest updated, config digest preserved. `.ecc/benchmarks/p4-production-companion-2026-10-13.json` |

## Transport, live agents, provider events

| Checkpoint | Validated | Result / limits |
| --- | --- | --- |
| USB-only direction | Bluetooth permanently excluded; separate live domain; C6 probe identity/version only (schema 2) | [USB_LIVE_TRANSPORT](USB_LIVE_TRANSPORT.md) |
| Read-only USB live | Dispatch beside AIM1 quota frame, metadata bounds, full replacement, stale sequence/boot/epoch rejection, expiry, rollover | 340 Python tests, strict USB live, both builds (one initializer incompatibility fixed). Shared serial owner; not enabled by polling; no UI consumer/adapter/trust/permission sender; not flashed |
| Provider lifecycle | Codex/Claude observers normalize documented events, retaining no prompts/commands/results; Codex setup keeps hooks/config and requires the client's trust review; live timeouts back off apart from quota | Synthetic only (content exclusion, expiry, subagent identity, generation revocation, bounded selection, setup/removal, real Windows neutral wrapper, quota/live separation). 354 Python tests incl. offscreen Qt; a transient Windows lock hit one archive test, a project-local temp rerun correctly failed trust tests, final isolated-temp run passed without weakening discovery policy. [LIVE_PROVIDER_EVENTS](LIVE_PROVIDER_EVENTS.md) |
| Device agent view | Fixed AGENTS button; UI-owned screen, 4 of up to 8 entries per page; unknown phases not inferred; epoch change or shrinking batch resets paging | 354 Python tests; native LVGL (pagination, fixed coordinates, themes, expiry, drag-out cancel, NEXT PAGE held while batch shrinks, rollover); synthetic screenshots. [LIVE_AGENT_VIEW](LIVE_AGENT_VIEW.md) |
| P4 app update (agent view) | Explicit flash: app at 0x10000 only, no NVS/partition/bootloader/C6 write | Digest, startup identity, live capability, open/empty/close exchange, telemetry passed. No real agent status, touch or permission |
| Correct deployment | EMBER was the wrong install; the LimitBuddy shortcut targets AppData/Local/Programs/AI Monitor. Fresh package smoke-tested and installed there, private config byte-identical, old runtimes backed up, EMBER stopped, Codex hooks prepared (user confirmed trust review) | Corrected provider-status rows (not agents) flashed. No genuine recent hook delivery observed |
| Phase 2 domain split | Session counts moved out of `aim::Snapshot` into `agent::Snapshot` (own freshness, revision, publication); `session_activity` wire command compatible; expiry clears agent state | 354 Python tests, strict native, both LVGL variants, both builds. Not flashed or repackaged |
| Agent lifecycle and timers | Generic `agent::State`, bounded elapsed/source-age, capability 2, legacy compatible. Claude: tool failures, auto-mode denials, teammate idle, task create/complete; child events don't replace parent; tasks not counted successful from vetoable hooks. Frozen timers, rollback rejection, source expiry, concurrent-hook file locking; NOVA reacts to recent explicit states | 362 Python tests; strict native; LVGL P4/S3; builds. P4 flashed (capability 2, empty handshake, zero-failure cache). All executables rebuilt, install replaced with backup, config digest unchanged. No real Codex hook event |
| Notification center | UI-owned; live transitions, quota warnings, host connection; max 32 entries / 24 h / current boot; fixed EVENTS/unread button, 4 rows; no command/permission authority, hints, transcripts, disk persistence | 363 Python tests; native bounds, duplicates, expiry/rollover, LVGL navigation/themes. P4 flashed. Codex read-only inventory: ten enabled/trusted hooks, wrapper no-op 250 ms; running client predates the hooks (stale config possible, unproven). Open: PC event journal, history UX, permission helper, packs |
| Navigation/readability | One MENU on home; large menu targets for secondary navigation; Usage always two full-size cards; Settings two large dropdowns; larger text; four palettes include menu screen | Native LVGL P4/S3 and builds; P4 flashed. App 2,350,992 B (was 2,352,880); internal free heap 240,724 (was 203,872); largest 116,724 (was 90,100); cache 630,528 B, 0 failures. Installed images refreshed |
| Home refresh correction | Fixed 164x48 REFRESH beside MENU; NEXT fixed, only when needed | Native P4/S3 (gating, caption bounds); app 2,352,336 B flashed. No real refresh request |

## Permissions, authentication, enrollment

| Checkpoint | Validated | Result / limits |
| --- | --- | --- |
| Permission UI | Native LVGL dialog, 22 pointer/visibility scenarios both boards; queue and final commit are distinct one-time stages; accelerated draw units rejected until completion fencing | 333 Python tests. Nothing sent; view not initialized in normal firmware. [PERMISSION_UI](PERMISSION_UI.md) |
| Generic permission + local IPC | Generic interaction types own the UI (no reverse dependency). Separate helper: bounded canonical args, random IDs/nonces, exact allow/deny only; failure keeps normal Claude handling. Named pipes reject remote clients (SID ACL); broker: one pending request, rechecks host/device/session/expiry; disconnect cancels; no hints logged | 382 Python tests; real pipe tests (peer PID, ACL, bounded JSON, re-arm, one synthetic denial, cleanup); helper EXE `--check`, unavailable-host, oversized-request fallback with empty output. No USB trust or approval; no flash. [USB_PERMISSION_HELPER](USB_PERMISSION_HELPER.md) |
| USB authentication | P-256 ECDH/HKDF enrollment, current-user DPAPI; code confirmation + device proof; empty keys fail closed. C++/Python HMAC-SHA256 interop (CNG/OpenSSL); bounds, replay/reflection, expiry, rollover, nonce correlation. Device core accepts request/heartbeat/cancel/close; lifetimes not renewed by heartbeats; decisions consumed once; no adapter -> `interactionProtocol` 0 | 399 Python tests. P4 crypto benchmark: two keygens 11,114 us, two agreements 10,080 us, one HMAC 81 us (no enrolled key/NVS/approval). Remote main e03f7ca read; local base 8be8a93; no checkout/reset/merge/push. [USB_INTERACTION_AUTH](USB_INTERACTION_AUTH.md) |
| Enrollment core | Needs local arming, revision-bound physical confirmation, PC proof, storage success before acknowledgment; opt-in stays off; no production instance | 407 Python tests; eight scenarios (wire-only, malformed points, stale revisions/proofs, disconnect, deadlines, crypto/storage failure). Linux/OpenSSL provided, not executed. P4 app 2,352,336 B |
| Connected enrollment setup | 104-byte trust storage (checksum, readback, scoped erasure, never stores opt-in); keys never cross the UI boundary; comparison screen with two 72 px targets; PC setup pauses/restores only its host, keeps heartbeat, commits once, verifies DPAPI | 422 Python tests; 14 pointer scenarios (hold, tap, drag-out, failed touch read, expiry, changed code, hidden/occluded/clipped, invalid code, programmatic click, failed queue). P4 `fw_3e5c_408b72.bin` flashed: enrollment closed, `enrollmentProtocol` 1, `interactionProtocol` 0, `livePermissions` false. Physical tests postponed |
| Host lifecycle + UI handoff | Explicit `PermissionRuntime`; default startup has no runtime/trust read/listener; needs opt-in plus local validation gate. Replay ledger shared across replacement; unconfirmed shutdown blocks replacement; one authenticated close | Native rejects forged/stale/expired/changed/disconnected/consumed envelopes; LVGL hold/deny reach `PermissionView.commit` on P4/S3 (synthetic). Host on COM6, Codex/ZCode ready; P4 firmware unchanged; 4 changed host modules compared with source before install |
| ESP serial/UI integration | `PermissionSerial`; developer P4 adapter (recursive mutex, atomic cancel, latest-consent versioning, off at boot, non-persistent); view hide/unload/delete revoke before mutex wait; failed publication read revokes | Real HMAC interop (allow/deny, one write, cancel, disconnect/timeout during signing, capacity, partial writes; ambiguous write never re-queued). 454 Python tests; 3 UI targets. Developer 2,453,824 B app / 60,908 B static RAM vs normal 2,419,456 / 52,132. Not flashed. CI for b5aa0bf: six jobs passed. Open: physical enrollment, real hold/deny/unplug, packaged validation |

## History, mirror, integrated candidate

| Checkpoint | Validated | Result / limits |
| --- | --- | --- |
| Device history | Separate compact domain on opt-in SQLite; read off the serial owner; 7 daily + 24 hourly token bins keep gaps; quota trends need matching windows; no invented sessions/time/tasks; 3 s enrollment lease | 430 Python tests; LVGL Today/24h/7d, unavailable/stale, fixed navigation. Atomic synthetic delivery and disabled reset passed without changing counters. App 2,419,040 B (later 2,419,296 B flashed), free partition 4,134,560 B, internal heap 214,752 (largest 81,908), PSRAM 29,079,616 (28,835,828), cache 630,528 B/0 failures; 39 setup/auth tests for lease. Local ZIP + v1.19.0 installer (unsigned, unpublished). History disabled in saved preferences. [DEVICE_HISTORY](DEVICE_HISTORY.md) |
| v1.19.1-rc1 integrated | PC/device opt-in UI and Claude setup/removal (backups, literal args, unrelated hooks kept, default-off); opt-in journal + history protocol 2 (migration, shutdown, consent epochs, concurrency, gaps, atomic USB); animation manifest 2 + allocation-free playback; real read-only USB mirror from actual P4/S3 flushes | 493 Python tests; 4 native LVGL targets; normal P4, P4 developer, S3 builds. P4 app 2,431,504 B, static RAM 52,628 B (developer 61,404; S3 116,692). Fixed a 200 ms per-packet short-read delay in `Panel.wait_for`. Mirror 800x480, 600 chunks, 3.094 s; PSRAM free 29,079,772 B before/after. Installer upgrade and five EXE smoke checks; config byte-identical; installed capture 4.922 s with Codex/ZCode ready. 1,000-event journal: median append 3.997 ms, p95 4.999 ms, max 98.868 ms, summary 2.327 ms, DB 241,664 B (fixture timing). Codex CLI 0.159.3 hooks active, no model turn. Read-only packaging/clean-profile workflow added (no publish rights). [DEVICE_MIRROR](DEVICE_MIRROR.md) |

Still open at rc1: see "Not yet validated". The [Claude live foundation](CLAUDE_LIVE_FOUNDATION.md) has a tested bounded parser and permission state machine, not connected to UI or transport. Follow-ups: [V2_STATUS](V2_STATUS.md).
