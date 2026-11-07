# Companion improvements and priorities

Other projects' feature lists are inspiration, not proof their hardware, security or software was validated here. USB remains the only transport.

## Shipped in v1.19.0 (history; current version in `tools/project_version.py`)

| Change | Note |
| --- | --- |
| Connection checklist, observation test | No model requests |
| Local numeric history, quota charts, reset-aware estimates | Optional |
| Claude session hooks | Explicit, observational; other AIs keep recorded token activity |
| Family-wide transparent cropping (six poses per built-in companion; measured on NOVA and ORBIT) | RGB565+A8 payload 4,396,320 -> 3,349,656 bytes (-1,046,664, 23.8%), no nontransparent pixels dropped; `CompanionRenderer` keeps canvas origins |
| First brightness load | Recovered value applied once; explicit user change preserved |
| Slow local reader (> 15 s) | Reported; USB and quota polling continue; app recommends host restart; no replacement threads |
| Free PSRAM | Added to the bounded device info reply |
| Windows Job Objects | Quota workers and read-only Codex app-server in kill-on-close jobs before the primary thread resumes; unconfirmed startup cleanup blocks retry; descendants stay contained |

> [!NOTE]
> Cropping shrinks flash data only: not the framebuffer, no proven runtime RAM gain, no PSRAM decode. Native tests cover both board interfaces and pose origins; real P4 and physical S3 are separate checks.

## Next reliability work

1. Physical gestures: drag out/back in, failed touch read, providers reordered while held.
2. Long P4 soak: resets, reconnects, heap/PSRAM trends, touch, backlight.
3. Packaged Job Object path on a fresh Windows install (source tests cover exited parents, abrupt owner death, nested jobs, denied assignment, unrelated processes; non-Windows keeps scoped process enumeration). Jobs control lifetime, not filesystem/network permissions.
4. Enforceable deadlines for local readers if bounded I/O is not enough.

## Optional, needs separate evaluation

- More companion packs with validated sizes, origins and bounded allocation; measure compression/PSRAM caching before choosing a decoder or storage format.
- Reset notifications from cached observations.
- Provider incident indicators separating quota from outages.
- Safe update checker, then verified downloads (firmware updates stay a user action).

## Out of scope

- Bluetooth/C6 transport (USB-only product).
- On-screen approval of AI tool commands: a much larger security scope, not enabled by observational reporting, not part of this candidate.
- Graphics acceleration should follow measured bottlenecks, not hardware availability.

Related: [Desktop Buddy](https://github.com/tech-nickk2/claude-desktop-buddy), [CodexBar](https://github.com/steipete/CodexBar), [ESP32 LimitBuddy](https://github.com/tobymarks/esp32-ai-monitor).
