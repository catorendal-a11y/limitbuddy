# Release the LimitBuddy terminal

The distributed product is Python source plus verified board firmware. No NOVA application EXE, Qt runtime, PyInstaller or Inno installer is built.
Windows releases include the official hash-verified Python embeddable runtime and hash-locked
Python dependency wheels, with retained original license files, under `runtime/`. The consumer
installs offline by double-clicking `Install-LimitBuddy.cmd`; source-only setup still uses pip.
See [Windows trust](WINDOWS_TRUST.md) for what users are told about signing and SmartScreen.

## Local build on Windows

1. Synchronize `FW_VERSION` in `src/config.h`, `HOST_VERSION` in `tools/project_version.py` and the top
   `docs/RELEASE_NOTES.md` heading (`# LimitBuddy vVERSION`). The builder rejects a `HOST_VERSION`/`FW_VERSION`
   mismatch; the release workflow also checks the release-notes heading and that the git tag equals the version.
2. Build both boards sequentially and collect each image pair before switching boards (their pinned platforms
   use different Arduino SDK versions). The collector writes `work/prebuilt/<board-id>/application.bin` and `factory.bin`:

```powershell
.\.venv\Scripts\python.exe -m platformio run -e esp32p4-release
.\.venv\Scripts\python.exe scripts/collect_firmware.py --environment esp32p4-release --output work/prebuilt
.\.venv\Scripts\python.exe -m platformio run -e esp32s3-waveshare-43-release
.\.venv\Scripts\python.exe scripts/collect_firmware.py --environment esp32s3-waveshare-43-release --output work/prebuilt
```

3. Build the package:

```powershell
.\.venv\Scripts\python.exe scripts/build_terminal_release.py --firmware-dir work/prebuilt --windows-runtime
```

Use a fresh output directory for each attempt (the default is `work/terminal-release`; the builder refuses an existing package folder or ZIP).
The builder must run from the project's own Git root. It exports only tracked reviewed source,
rejects private/generated files and linked paths, verifies both application/factory pairs and that the
application image contains the version string, adds the NOVA and ORBIT companion packs, keeps
source/license notices, writes an internal `SHA256SUMS.txt` and produces
`nova-vVERSION-windows-x64-terminal.zip`. Without `--windows-runtime` it builds a
`terminal-source` archive instead.

## Test the package

On a disposable Windows directory, extract the exact ZIP and test it:

```powershell
.\.venv\Scripts\python.exe scripts/test_terminal_package.py --package PATH_TO_CLEAN_PACKAGE
```

This runs the real CMD installer without external Python or package downloads, then bare `limitbuddy` and `nova`
from another folder, verifies no Qt/PyInstaller runtime and no unexpected executable, and tests idempotent
registration/unregistration (private settings are preserved). It does not read credentials, link provider hooks
or flash hardware. The resulting test directory contains generated private setup data; do not republish it.
Publish the original clean ZIP only.

## Publish

Pushing a `v*` tag starts the GitHub release workflow (`.github/workflows/release.yml`):

1. `prepare` skips the build when a release for the tag already exists.
2. `firmware` builds both firmware targets, requires the tag to match the firmware, host and release-note versions,
   runs the native UI tests (on the P4 job) and collects the images.
3. `windows` runs the Python regressions, builds the Windows x64 terminal ZIP, runs the package test above and
   writes `SHA256SUMS.txt` and the current release notes.
4. `publish` is the only job with write permission. It verifies the ZIP against its checksum, attests the ZIP and
   checksum file and creates a draft release without checking out or executing repository code.

Review the downloaded draft and publish it explicitly. Maintainers must not replace immutable published assets.
Retirement of old EXE releases is a separate explicit owner action; retain source tags/history and local
verification evidence. For the permission model see [GitHub security](GITHUB_SECURITY.md).
