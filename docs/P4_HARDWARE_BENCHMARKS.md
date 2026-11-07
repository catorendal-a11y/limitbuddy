# P4 hardware measurements for v2

Measured on the owner's **JC4880P443C_I_W_Y**, 2026-10-13. Artifact: [p4-hardware-2026-10-13.json](../.ecc/benchmarks/p4-hardware-2026-10-13.json) (no USB logs, MAC addresses, provider data or app backups).

Procedure: current pinned P4 platform/SDK; firmware and ROM identity verified; production partition table checked; existing app backed up locally; only the app partition written and verified; original app restored and USB startup verified; host restarted on COM6. No C6 firmware or NVS written.

## PPA vs CPU rotation (isolated)

Identical pseudorandom 800x480 RGB565 input rotated into a 480x800 buffer, separate 64-byte-aligned PSRAM buffers. Display driver initialized but not fed these buffers. PPA time includes its completion callback. Outputs compared byte-for-byte.

| Measurement | Result |
| --- | ---: |
| CPU rotation median (8 samples) | 23,963 us |
| PPA rotation median (8 samples) | 14,744 us |
| Pixel comparisons | 8 / 8 exact |
| Speed ratio | 1.625x |
| Retained resources after cleanup | none |

> [!NOTE]
> **Decision:** keep CPU rotation in production. This result does not show partial-region performance, display DMA/cache ownership, tearing, end-to-end frame rate or long-term reliability; those gates must pass first. No buffer-size or asset-format decision follows from it.

## Graphics counters (diagnostic build)

Boot screen observed 10,203 ms, no host or provider request.

| Counter | Value |
| --- | ---: |
| Flush chunks / pixels | 13 / 1,294,650 |
| CPU rotation total / mean per chunk | 78,829 us / 6,063.77 us |
| Driver submission total / mean per chunk | 61,490 us / 4,730 us |

Chunk counters, **not display FPS**, total LVGL render time or DMA completion.

| Allocation | Bytes |
| --- | ---: |
| Two LVGL draw buffers | 1,536,000 |
| Rotation scratch | 768,000 |
| Two display framebuffers | 1,536,000 |
| Physical PSRAM / flash | 33,554,432 / 16,777,216 |

Startup/allocator readings are separate from physical capacity. Internal/PSRAM bandwidth and alternative buffer sizes need controlled comparisons.

```text
python scripts/collect_graphics_baseline.py --board guition-p4 --port COM_NUMBER --seconds 10 --ppa --output work/graphics.json
```

Reads an installed diagnostic build without enabling acceleration.

## Standalone C6 (historical, schema 1)

Before the USB-only decision removed controller enabling, the probe reached `completed` within its deadline.

| Result | Value |
| --- | --- |
| Detected coprocessor | ESP32-C6 |
| ESP-Hosted host / coprocessor version | 2.12.13 / 2.12.22 |
| Controller init/enable RPC | confirmed |

The differing versions worked for the tested RPC calls. This is not HCI, encrypted GATT, pairing, reconnect or Claude Desktop validation. Production leaves the coprocessor uninitialized and reports `not-probed`. See [C6 bring-up](C6_BRINGUP.md).

## Collector fixes and validation

- Opening USB can restart the board and the benchmark runs before the protocol task, so the hardware collector waits on one connection for up to three 3 s identity attempts. A wrong identity is never retried; a changed boot ID between identity and telemetry rejects the measurement. The flashing harness allows USB re-enumeration after a watchdog reset.
- C6 collector: 2,048-byte line buffer, 15 s deadline, duplicate JSON fields rejected, only validated fields exported. `probe` never retries radio init; failures/timeouts are never guessed as capability.
- Synthetic tests cover limits, fragmented replies, boot noise, partial writes, invalid types, unverified identities, pixel mismatches and missing fields. All 324 Python regressions passed.

**Next gates (as of 2026-10-13):** target asset decode timing/peak memory, PSRAM cache/LVGL lifetime binding, permission UI. SD and physical S3 untested. Bluetooth is no longer a goal.
