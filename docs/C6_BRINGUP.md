# Standalone P4/C6 bring-up

> [!NOTE]
> **USB-only decision (2026-10-13):** Bluetooth is permanently excluded. The standalone probe is identity/version only (schema 2) and never initializes or enables a Bluetooth controller. Schema 1 measurements are historical (the collector still reads them). Normal firmware does not initialize the radio. See [USB-only v2 transport](USB_LIVE_TRANSPORT.md).

Board: JC4880P443C_I_W_Y. Vendor spec: 32 MB PSRAM, 16 MB flash, ST7701S panel; `_Y` is the enclosed variant. Specs are not runtime detection.

## Isolated test firmware

```text
python -m platformio run -e esp32p4-c6-probe
```

| Property | Detail |
| --- | --- |
| Scope | Developer-only; replaces the monitor entry point; source filter is `src/diagnostics/c6_probe_main.cpp` only |
| Absent | display/UI, AIM1 host, Claude integration, GATT server, Wi-Fi association/scanning; excluded from release board/image selection; production never initializes the coprocessor |
| SDIO profile (compile-time check) | clock 18, command 19, data 14/15/16/17, reset 54, ESP32-C6 target; a different SDK pin config fails the build. Do not reuse for another board revision without wiring evidence |
| Worker steps | NVS init (no erase), SDK event loop, ESP-Hosted start, connect, check target via `esp_hosted_get_cp_info`, read slave firmware version |
| Never | Bluetooth init/enable, C6 firmware update, credential input, bonding, automatic retry, access-point connection |

Send the ASCII line `probe` plus newline over the probe firmware's USB serial port. The reply has host/slave version, RPC state, numeric error and deadline state.

- `configuredSlaveTarget` is separate from `detectedChip` (filled only after the runtime Hosted identity check).
- `controllerEnableConfirmed` is always `false` in schema 2. In schema 1 it meant the controller RPC acknowledgement, not measured HCI/GATT.
- Unfinished work is marked timed out after 10 s with no retry. A blocking SDK call may keep running (task and driver resources are not force-freed); late completion stays timed out; a completed result stays successful when read later.
- This is an isolated SDK test, not a bounded-driver guarantee; record any driver panic or incompatible slave firmware on real hardware.

## Validation

| Area | Status |
| --- | --- |
| Deadline boundaries, completed results, clock rollover | Native tests |
| Pinned SDK APIs/pins | Compile-time |
| Actual C6 presence, compatible slave firmware, controller operation | Not proven by tests; see schema 1 run |
| Schema 1 run on JC4880P443C_I_W_Y, 2026-10-13 | Completed: target ESP32-C6, host 2.12.13, coprocessor 2.12.22, controller init/enable acknowledged via RPC in deadline; no C6 firmware updated; original P4 app restored, USB startup verified |
| HCI, GATT, secure pairing, Claude Desktop | Untested (not goals) |

Measured results: [P4_HARDWARE_BENCHMARKS.md](P4_HARDWARE_BENCHMARKS.md).

> [!WARNING]
> Flash only the explicitly identified P4 port, after stopping its host, and restore the production image afterwards. Never flash an unrelated serial device or update the C6 just to probe it.

Read an already installed probe with the bounded collector:

```text
python scripts/collect_c6_baseline.py --port COM_NUMBER --output work/c6.json
```

It waits at most 15 s, discards oversized boot-noise lines, rejects malformed or duplicate fields, saves a whitelisted result, and sends only read-only `probe` queries (no init, no flashing). A saved failure is not a successful radio test.

References: [vendor spec](https://www.guition.com/icms/upload/fb081940d6fc11f09850077a33e1404f/FTPData/UEditor/file/2026121/1768961095795/JC4880P443C_I_W%20Specifications-EN-V1.0.pdf), [tested pin profile](https://github.com/ultramcu/guition-jc4880p4-bsp/blob/main/src/board_p4_pins.h), [coprocessor version example](https://github.com/espressif/esp-hosted-mcu/tree/main/examples/system/get_cp_fw_version). The BSP is hardware evidence only, not a dependency or a replacement for the working display driver.
