# Companion runtime format and cache checkpoint

The P4 experiment uses **raw LZ4 blocks** (experimental version-1 runtime cache) decoded into the existing **RGB565+A8** layout. Built-ins remain the production fallback. P4 renders them from compressed frames through a startup-allocated PSRAM cache; S3 keeps raw built-ins. External packs use the version-2 format in [COMPANION_ANIMATIONS.md](COMPANION_ANIMATIONS.md). Not a physical S3 validation; USB/AIM1 is unchanged.

## Codec comparison (physical P4)

All 12 committed poses (NOVA and ORBIT) on the identified JC4880P443C_I_W_Y at 360 MHz; 5 decodes per pose/codec, SHA-256 verified on every output, timing excludes hashing. Standalone: no display, USB or SD load.

| Codec | Payload, 12 poses | Median of pose medians | Slowest pose median | Extra decoder state |
| --- | ---: | ---: | ---: | ---: |
| Raw copy | 3,349,656 B | 11,350.5 us | 13,637 us | 0 |
| Byte RLE | 1,925,271 B | 11,703.5 us | 13,523 us | 0 |
| **LZ4** | **519,579 B** | 12,033.5 us | 13,740 us | 0 |
| Zlib/Deflate | 249,490 B | 12,792 us | 14,269 us | 10,992 B |

Medians, not p95/max. State excludes task stack, allocator overhead and the decoded buffer; working-UI peak memory still needs integration measurement. Data: [p4-assets-2026-10-13.json](../.ecc/benchmarks/p4-assets-2026-10-13.json).

- **Decision:** LZ4 saves 2,830,077 bytes (84.5%) vs raw at near-raw decode time and no persistent inflater state, leaving internal RAM for live-agent UI and USB permissions. RLE compresses far less at similar latency. Deflate stays a later option if smaller transfers outweigh its state.
- No S3 timing or throughput is inferred from P4.
- Delivery is one versioned manifest per companion (<= 8 frames, strict bounds). The 12-frame aggregate is not a runtime manifest; real pack tooling must verify its full delivered size (the prototype with metadata stayed below the conservative 1.8 MB limit).

## PSRAM cache experiment

`PsramCache`: two 64-byte-aligned slots, pinned LVGL LZ4 decoder, mbedTLS SHA-256 over encoded and decoded bytes. The test loaded six NOVA frames while pinning the active one.

| Result | Value |
| --- | --- |
| Reserved pool | 630,528 B (2 x 315,264) |
| Six verified loads | 117,783 us total, ~19,630.5 us per load (both hashes included) |
| Bad encoded hash; truncated LZ4 with valid hash of truncated input | both rejected |
| Pinned active image after failures | still hash-correct |

- Allocation happens at init, never lazily in `load` or render. Pool and frame descriptors must outlive bindings; detach all bindings before destroying an owner.
- Production P4 allocates the pool once at startup. All built-in poses stay available compressed: six per companion, 30 on P4 (five companions), 18 on S3 (three); see `src/companion_features.h`.
- One raw work pose per companion stays in flash as fallback if allocation, validation or decoding fails. Thumbnails and provider logos are unchanged.

## Rendering and ownership

- `CompanionRenderer` takes a generic descriptor/origin view and restores the desired source if another owner changed the LVGL image.
- `ImageBinding` owns two stable descriptors and explicit frame pins; rejects another image/cache target or a pin shared between bindings; swapping drops the old LVGL cache entry before retiring storage; detach restores the fallback and origin. Source pixels cannot alias the decode destination; unknown poses and oversized encoded frames are rejected.
- Only the synchronous single software draw unit is supported; other LVGL draw models fail closed until a completion fence exists. UI-task ownership is mandatory; no transport callback touches LVGL; no permission/live state enters `aim::Snapshot`.
- Native LVGL tests cover swaps, conflicting owners, cleanup, fallback origins, position updates, external source changes, invalid indices, pixel-identical built-in decoding, no per-tick decode, pin retirement and raw fallback on failed integrity. The cache backend was tested on real P4 memory.

## Reproduce

```text
node scripts/export_companion_frames.cjs --output work/asset-benchmark-input
python scripts/export_asset_benchmark.py --frames work/asset-benchmark-input --robot nova --output work/asset-target-fixtures/asset_fixtures.h --cc gcc
python -m platformio run -e esp32p4-asset-benchmark
python scripts/collect_asset_baseline.py --port COM_NUMBER --robot nova --output work/asset-target-nova.json
```

Repeat with `--robot orbit` (the only other choice), rebuilding before collecting.

> [!WARNING]
> The asset-benchmark environment is excluded from release selection. Flash only the identified P4 after stopping its host, verify the production partition table, keep a local app backup and restore the normal app afterwards. Never flash these fixtures as an installer image or overwrite C6/NVS.

Remaining gates: physical S3 validation; microSD deferred until measured pack sizes need it; permissions keep their own fail-closed USB/local-IPC gates. No Bluetooth transport.

## Rebuild compressed built-ins

After regenerating SVG art: `python scripts/generate_companion_lz4.py --cc gcc`. It reads committed raw pixels, uses the pinned LVGL LZ4 encoder, verifies a byte-identical round trip and emits encoded/decoded SHA-256 digests. Production verifies both digests before binding a frame; the two-slot cache may reuse a verified resident frame; a failed frame is not retried every UI tick. Hardware diagnostics report allocation, decoded-frame count, failures and max decode-plus-bind time.

## Normal P4 firmware measurement (2026-10-13)

Identified P4 backed up, app-only flashed, digest verified, watchdog restarted; USB/live metadata handshake and bounded hardware report passed.

| Metric | Result |
| --- | ---: |
| Previous / new app image | 4,611,328 / 2,347,328 B |
| App saving | 2,264,000 B (49.1%) |
| Free app partition | 4,206,272 B |
| Companion cache allocation | 630,528 B |
| PSRAM free after companion init / largest block | 29,079,616 / 28,835,828 B |
| Internal heap free after companion init | 172,612 B |
| First-frame verified decode + LVGL bind | 20,513 us |
| Companion init complete (boot uptime) | 1,411 ms |

Cache active, zero failures. One startup frame only: not p95, all-pose timing, touch responsiveness or soak. Both SHA-256 checks are in the frame time. Raw reserve poses explain why firmware savings are below the standalone payload savings. Evidence: [p4-production-companion-2026-10-13.json](../.ecc/benchmarks/p4-production-companion-2026-10-13.json).
