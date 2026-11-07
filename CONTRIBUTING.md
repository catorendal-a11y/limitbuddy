# Contributing

Use English for code comments, UI, docs, issues and pull requests. Keep changes focused and describe concrete behavior.

## Development

1. `setup.ps1 -BuildTools` on Windows, or `sh setup.sh` elsewhere, then `python -m pip install 'platformio>=6.1,<7'` in the local .venv.
2. Build: `python -m platformio run -e esp32p4-release` (first build downloads pinned ArduinoJson/LVGL).
3. Test: `python -m unittest discover -s tests -p "test_*.py"`.
4. Test: `python scripts/run_tests.py`; for UI changes add `--ui` (needs GCC, CMake, Ninja).

- Inspect UI screenshots for clipping, contrast and touch targets, and say whether you validated with mocks or physical hardware.
- Stop the companion before flashing; pick an explicit port when several boards are present.
- Keep LVGL/backlight mutations on the UI task. Preserve bounded parsing, frame correlation, partial writes, rollover-safe timing and compatibility. Test state transitions; no flash writes per render loop.

## Privacy and assets

> [!WARNING]
> Never include local configuration, auth files, keys, databases, conversations or runtime logs. Use synthetic provider responses and SQLite fixtures, and review screenshots and errors for private data.

Keep third-party headers and licenses intact; provider marks and fonts are not relicensed by MIT. Regenerate committed NOVA arrays only when assets change.

## Pull requests

Describe the problem, resulting behavior, tests and hardware limits; add screenshots for visual changes. Discuss broad protocol or hardware changes in an issue first. Vulnerabilities: see [SECURITY.md](SECURITY.md).
