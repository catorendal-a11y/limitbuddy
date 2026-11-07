# LimitBuddy terminal

NOVA is the PC application: type `limitbuddy` and it runs in the current terminal. The release holds Python source and board firmware, with no NOVA EXE or Qt.

## Install on Windows

1. Download `nova-v1.19.1-rc27-windows-x64-terminal.zip` from [Releases](https://github.com/catorendal-a11y/limitbuddy/releases/tag/v1.19.1-rc27).
2. Extract it into a permanent writable folder and keep it there.
3. Double-click **Install-LimitBuddy.cmd**: it verifies the bundled runtime and registers only this user's `limitbuddy` command. No administrator access.
4. Open a new terminal in any folder and run `limitbuddy`.

The ZIP holds Python 3.13.16, hash-locked dependencies, NOVA source and both firmware images, so install needs no extra downloads, pip, Python, Node.js or npm. The runtime stays inside the folder, does not replace other Pythons and does not change the execution policy. The interpreter and DLLs under `runtime/` are vendor components with original licenses and a per-file manifest; the installer checks hashes first and fails with a request to re-extract if files changed. Provider requests and optional AI-client setup still need internet.

Setup does not select providers, sign into an AI account, flash hardware or enable physical approvals. A Git checkout or GitHub's source archive has no bundled runtime and needs Python 3.10+ plus internet; advanced users can run `Install-LimitBuddy.ps1` directly.

## Commands and navigation

| Command / key | What it does |
| --- | --- |
| `limitbuddy --version`, `--help` | Command information |
| `limitbuddy --check` | Renders synthetic data; does **not** test USB or providers |
| **1-5** | Pages |
| **Tab / Enter** | Controls |
| **R** | Reload local metadata |
| **?** / **Esc** / **Q** | Help / cancel form / quit |

Source launcher: `AI-Monitor-Terminal.bat` (`AI-Monitor.bat` is an alias).

- In **Settings**, choose and save board, USB port and providers, then **Start host**. Use **Overview** and **Device / Check USB** for live status.
- Quota, observed sessions and USB connection are separate signals. Unknown quota stays unknown; stale agent events show Last, not current work.
- Claude quota comes from your local Claude Code login or the optional statusline bridge; otherwise Claude shows activity only.
- Opening or refreshing the dashboard never starts a model request or a second USB owner.
- Invalid settings stay in the form; secret fields are masked and unchanged keys are preserved.
- **Device / Firmware > Application update** writes only the application partition after exact board identification and confirmation. **First installation** resets display settings. Source-only downloads contain no firmware: use the release ZIP or build per [DEVELOPMENT.md](DEVELOPMENT.md). Physical permissions stay disabled; S3 is experimental.

## Start at Windows sign-in

Off by default. **Settings > Edit settings** adds one `LimitBuddy` value to the current user's Run key (listed under Windows Settings > Apps > Startup), pointing at this folder's windowless Python and `tools\aim_control.py --start-host`. No administrator rights, scheduled task or service.

- Turning it off removes the value, but only if it starts this installation.
- If another program already uses the name `LimitBuddy`, Save stops with a message and changes nothing.
- A host that cannot start at sign-in (for example an unplugged display) just waits for USB.

## Upgrade and migrate

1. Extract the new release to a **new** permanent folder and run its `Install-LimitBuddy.cmd` (retargets `limitbuddy`).
2. Stop the old host (**Settings > Stop host**).
3. Copy `tools\aim_host.json` (settings and keys) and, if history is on, `tools\activity` into the new folder's `tools`.
4. Run `limitbuddy`, check **Settings**, then **Start host**. With **Start at Windows sign-in** on, open **Edit settings** and press **Save** once to rewrite the Startup entry.
5. Update the display: **Device > Firmware > Application update** keeps display settings.
6. Re-link only previously opted-in integrations (provider events, Claude quota bridge) from **Agents**; provider selection alone never installs hooks.
7. Keep the old folder until host, USB and hooks work.

> [!IMPORTANT]
> Migrate an old EXE installation before uninstalling it: its host and hooks use the old runtime paths. P4 firmware v1.12.0 or later keeps its identity with the new host; a new S3 board needs its own first installation.

## Remove the command

From the installed folder:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Install-LimitBuddy.ps1 -Uninstall
```

This removes only the owned shim and PATH entry, plus the Startup entry if it starts this folder. Settings, history and the folder stay, and the host is not stopped. Stop the host and unlink this installation's integrations before deleting the folder. Other users' PATH and unrelated `limitbuddy` commands are untouched.

## Development and Linux/macOS

Windows development: `setup.ps1 -BuildTools` (no graphical runtime). Linux/macOS: `./setup.sh`, then `.venv/bin/python tools/aim_terminal.py`; USB access may need OS-specific setup, and Windows is the tested command-registration platform. Artwork regeneration alone uses `scripts/requirements-artwork.txt`.
