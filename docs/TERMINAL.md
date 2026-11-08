# LimitBuddy terminal

NOVA is the PC application: type `limitbuddy` and it runs in the current terminal. The release holds Python source and board firmware, with no NOVA EXE or Qt.

## Install on Windows

1. Download `nova-v1.19.1-rc28-windows-x64-terminal.zip` from [Releases](https://github.com/catorendal-a11y/limitbuddy/releases/tag/v1.19.1-rc28).
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
| `limitbuddy --check-update` | Says whether a newer published release exists |
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
- **Device / Doctor** shows one OK / FIX list: settings, host, USB, firmware version, Start at sign-in, the `limitbuddy` command, provider hooks and quota, and the Claude login expiry. It is read-only and prints no keys or tokens.
- When the display firmware differs from the host, **Device** and **Overview** say so; update it with **Firmware > Application update**.
- **Device / Firmware > Application update** writes only the application partition after exact board identification and confirmation. **First installation** resets display settings. Source-only downloads contain no firmware: use the release ZIP or build per [DEVELOPMENT.md](DEVELOPMENT.md). Physical permissions stay disabled; S3 is experimental.

## Start at Windows sign-in

Off by default. **Settings > Edit settings** adds one `LimitBuddy` value to the current user's Run key (listed under Windows Settings > Apps > Startup), pointing at this folder's windowless Python and `tools\aim_control.py --start-host`. No administrator rights, scheduled task or service.

- Turning it off removes the value, but only if it starts this installation.
- If another program already uses the name `LimitBuddy`, Save stops with a message and changes nothing.
- A host that cannot start at sign-in (for example an unplugged display) just waits for USB.

## Update in place

**Settings > Check for update** looks for a newer published release on GitHub. **Install update** (type `UPDATE`) downloads it, checks it against the release's `SHA256SUMS.txt`, extracts it beside this folder as `<folder>.next`, stops the host and closes NOVA. A small PowerShell step then moves your private files (`tools\aim_host.json`, `tools\activity`, companion packs, logs, `.env`) into the new version, renames this folder to `<folder>.previous` and puts the new version in its place, then starts the host again if it was running.

- The folder path stays the same, so provider hooks (and their Codex trust), the Start at sign-in entry and the `limitbuddy` command keep working.
- Only this repository's releases and GitHub's asset hosts are contacted; downloads carry no credentials.
- If anything fails, the old folder is put back and keeps working. The result is in `%TEMP%\limitbuddy-update.log` and on **Device / Doctor**.
- Update the display afterwards with **Device > Firmware > Application update**.
- Available in the Windows package; a Git checkout updates with Git.

## Upgrade and migrate (older versions)

Versions before in-place update move by hand once. Use a stable folder such as `%LOCALAPPDATA%\Programs\NOVA Terminal\app`, so later updates keep the same path.

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
