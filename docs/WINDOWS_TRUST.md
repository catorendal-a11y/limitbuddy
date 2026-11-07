# Windows installation and terminal trust

1. Download `nova-v1.19.1-rc27-windows-x64-terminal.zip` and `SHA256SUMS.txt` from this repository's Releases.
2. Compare the ZIP's SHA-256 with the checksum.
3. Extract the complete archive into a permanent writable folder.
4. Double-click **Install-LimitBuddy.cmd** (verifies the bundled runtime, registers `limitbuddy` for the current user), open a new terminal, run `limitbuddy`.

The release holds NOVA Python source, the official CPython 3.13.16 embeddable runtime (upstream `python.exe` / `pythonw.exe` under `runtime/`), hash-locked wheels and both boards' firmware. It has no compiled NOVA EXE, Qt frontend, PyInstaller package or Inno installer. Keep the extracted folder; the command points to it. No separate Python, pip, Node.js, PlatformIO or administrator access is needed, and install works offline.

## SmartScreen

> [!WARNING]
> The command scripts and bundled interpreter are **not Authenticode-signed** by this project's publisher. Windows or organization policy can still warn or block them. A checksum, version metadata or GitHub provenance does not establish a trusted Windows publisher.

- The project never disables SmartScreen, Defender, Smart App Control or execution protections, and never auto-unblocks downloads.
- Download only from the linked repository and compare SHA-256. Checksums detect corruption; they cannot authenticate a compromised release.
- If you do not trust the download or your organization blocks it, cancel and ask your administrator; do not weaken policy.
- A future verified publisher could timestamp-sign artifacts or use an MSIX Store package; outside the Store, reputation may still be needed. See [SmartScreen reputation](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation) and [code-signing options](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options).
- Microsoft Security Intelligence can review a specific file for false detections. A submission is not a certificate or guarantee; record the file SHA-256 and the final determination, and never call a pending submission approved.

## What is tested

| Check | Scope |
| --- | --- |
| Release build | Both firmware targets and the exact Windows x64 terminal ZIP |
| Package verification | Pinned CPython archive and wheel hashes, runtime manifest, retained licenses, no NOVA EXE/Qt, clean extraction |
| Install | Real CMD installer and bare `limitbuddy` with external Python and package downloads unavailable |
| Unit tests | Native and Python tests with synthetic settings; no flashing, no provider sign-in |
| Publishing | Isolated publisher only verifies and attests the ZIP/checksum before a draft; it runs no repository code |

Real P4 flashing is checked separately with the board connected. The S3 stays experimental until tested on physical hardware; physical approvals, unplug/suspend behavior and long-duration stability are separate gates. Checks cannot guarantee every PC, cable, board variant, policy or provider version; unsupported integrations stay visibly unavailable rather than report fabricated quotas.

## Uninstall

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Install-LimitBuddy.ps1 -Uninstall
```

Run from the extracted folder. It removes only that installation's `limitbuddy` command and PATH entry; application files, private `tools/aim_host.json`, logs and activity records stay. Stop the host and unlink observational integrations before deleting the folder. Erase private data yourself and never upload it to GitHub.
