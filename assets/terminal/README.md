# Terminal artwork

`nova.json` holds four 40 x 26 RGB rasters (work, attention, error, done) generated from the original NOVA vectors in `assets/nova/`. They keep that artwork's MIT license and attribution (`assets/nova/SOURCES.md`); no third-party provider marks are included.

Regenerate: `.venv\Scripts\python.exe scripts/generate_terminal_assets.py`. PySide6 (Qt) is needed for generation only; the terminal draws the pixels as colored half-block cells with Python's standard library and Rich (inside Textual).
