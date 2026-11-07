# Desktop performance check (historical)

> [!NOTE]
> **Historical.** These measurements cover the Qt desktop window of v1.17.2-v1.18.1, retired in rc15. `scripts/benchmark_desktop.py` and that GUI are no longer in the repository, so nothing here can be rerun or applies to the terminal or display firmware (device numbers: [P4_HARDWARE_BENCHMARKS.md](P4_HARDWARE_BENCHMARKS.md)). Only the SQLite budget below still describes current numeric token readers.

## Key findings

Controlled offscreen Windows runs (Oct 10-11, 2026), synthetic Copilot/COM9999 fixture, mocked token polling, no accounts, provider calls or USB writes, 20 ms event-loop probe.

| Measurement | v1.17.2 | v1.18.1 |
| --- | --- | --- |
| Warm startup to widgets | 163 ms | 168 ms |
| RSS visible / minimized | 67.9-68.9 / 68.2-69.4 MiB | 69.3-69.9 / 69.3-70.0 MiB |
| Event-loop p95 | about 2 ms | about 2 ms |
| UI token refreshes in 10 s minimized | 4 | 0 |

| Injected 300 ms token-poll delay | Before | After |
| --- | --- | --- |
| Max visible loop delay | 284.3 ms | 2.5 ms |
| p95 / RSS / CPU | 2.04 ms / 69.5 MiB / 0.52% | 2.05 ms / 69.1 MiB / 0.52% |

- The reliable gain: hidden windows stopped redundant token/database polling while the independent host kept monitoring. CPU stayed below 1% of a core, too low to quantify a reduction. Memory rose 1-2 MiB; startup is not shown to be faster (first-run cold-cache times differed).
- Responsiveness: USB scans and host/status/token/log reads ran off the Qt thread, one pending status read and USB scan at most, stale results discarded. Flasher limits: 10 minutes total, 2 minutes silent output; a timeout reported a possibly incomplete write and stopped the exact child tree.
- Packaged v1.18.1 samples: about 102 MiB visible, 107 MiB hidden (0.16% of one core), no GUI TCP listener, hosts stayed connected through minimize/restore/Quit. Short samples, not a leak test.
- Token history keeps full bounded snapshots; evicted IDs get fixed-size tombstones so old records cannot look new (hash collisions may hide a first observation). Activity indicators, not billing.

## Numeric-query execution budget (current)

Codex and ZCode reads use SQLite's progress handler with a **100 ms** execution budget, like the OpenCode adapter; a row limit alone did not bound an unindexed sort.

| Case | Result |
| --- | --- |
| 1M-row synthetic recursive projection, old adapter | 433-453 ms |
| Same, bounded adapter | interrupted in 106-111 ms; database bytes unchanged |
| Timeout | source reported unavailable, never partial or fabricated usage |

The budget bounds SQLite execution only, not filesystem access; connection lock waiting keeps its own 150 ms timeout, and progress callbacks are periodic, so 100 ms is not a hard wall-clock limit. Synthetic tests cover interruption, later successful reads and unchanged contents.
