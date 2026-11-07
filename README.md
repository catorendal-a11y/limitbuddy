# LimitBuddy — ESP32 desk display for AI coding usage limits

**LimitBuddy** puts your AI coding quota on a 4.3-inch ESP32 touchscreen beside your keyboard: session and weekly limits, reset countdowns and low-limit alerts for **Claude Code, OpenAI Codex, Gemini CLI, Z.AI / ZCode, OpenCode, GitHub Copilot, Cursor and Antigravity**. An animated companion reacts to recorded token activity on your PC. USB only: no Wi-Fi, no cloud relay, keys stay on the PC.

*Formerly **AI Monitor P4** (`ai-monitor-p4-s3`); old links redirect here.*

> [!NOTE]
> Current candidate: **[v1.19.1-rc25](https://github.com/catorendal-a11y/limitbuddy/releases/tag/v1.19.1-rc25)** (prerelease). It adds a full-color terminal dashboard, direct device navigation, observed agent sessions, local-day history, companion packs, private diagnostics and [real USB device-screen capture](docs/DEVICE_MIRROR.md). Physical permission control stays disabled pending hardware/provider validation.

![LimitBuddy: ESP32-P4 touchscreen with the ORBIT and CLAUDE companions, actual UI previews and the LimitBuddy terminal](docs/media/github-preview.png)

<p align="center">
  <a href="https://github.com/catorendal-a11y/limitbuddy/releases/tag/v1.19.1-rc25"><img alt="Latest published release" src="https://img.shields.io/github/v/release/catorendal-a11y/limitbuddy?include_prereleases=true&amp;style=flat-square&amp;label=version&amp;color=35d07f"></a>
  <a href="https://github.com/catorendal-a11y/limitbuddy/commits/main"><img alt="Last commit" src="https://img.shields.io/github/last-commit/catorendal-a11y/limitbuddy?style=flat-square&amp;color=35d07f"></a>
  <a href="https://github.com/catorendal-a11y/limitbuddy/actions/workflows/ci.yml"><img alt="Build and test status" src="https://img.shields.io/github/actions/workflow/status/catorendal-a11y/limitbuddy/ci.yml?branch=main&amp;style=flat-square&amp;label=build%20%2B%20tests"></a>
  <a href="LICENSE"><img alt="MIT license" src="https://img.shields.io/badge/license-MIT-35d07f?style=flat-square"></a>
  <a href="https://github.com/catorendal-a11y/limitbuddy/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/catorendal-a11y/limitbuddy?style=flat-square&amp;logo=github&amp;color=54c4f2"></a>
</p>
<p align="center">
  <a href="docs/BOARDS.md"><img alt="ESP32-P4 supported" src="https://img.shields.io/badge/ESP32--P4-supported-35d07f?style=flat-square"></a>
  <a href="docs/BOARDS.md"><img alt="Original Waveshare S3 experimental" src="https://img.shields.io/badge/Waveshare%20S3-experimental-ffb96a?style=flat-square"></a>
  <a href="docs/BOARDS.md"><img alt="800 by 480 touch interface" src="https://img.shields.io/badge/display-800%20%C3%97%20480%20touch-54c4f2?style=flat-square"></a>
  <a href="platformio.ini"><img alt="LVGL 9.6.0" src="https://img.shields.io/badge/LVGL-9.6.0-c49aff?style=flat-square"></a>
  <a href="docs/DEVELOPMENT.md"><img alt="Arduino and PlatformIO firmware" src="https://img.shields.io/badge/firmware-Arduino%20%2B%20PlatformIO-00979d?style=flat-square"></a>
</p>
<p align="center">
  <a href="docs/CODEX_SETUP.md"><img alt="Codex local tokens and quota" src="https://img.shields.io/badge/Codex-local%20%2B%20quota-10a37f?style=flat-square"></a>
  <a href="docs/PROVIDERS.md#zcode"><img alt="ZCode local tokens and optional quota key" src="https://img.shields.io/badge/ZCode-local%20%2B%20quota-14b8a6?style=flat-square"></a>
  <a href="docs/PROVIDERS.md#claude-code"><img alt="Claude Code local tokens and quota" src="https://img.shields.io/badge/Claude%20Code-local%20%2B%20quota-d97757?style=flat-square"></a>
  <a href="docs/PROVIDERS.md#gemini-cli"><img alt="Gemini CLI local activity" src="https://img.shields.io/badge/Gemini%20CLI-local%20activity-4285f4?style=flat-square"></a>
  <br>
  <a href="docs/PROVIDERS.md#external-numeric-bridge"><img alt="Copilot requires numeric bridge" src="https://img.shields.io/badge/Copilot-bridge%20required-a371f7?style=flat-square"></a>
  <a href="docs/PROVIDERS.md#external-numeric-bridge"><img alt="Cursor requires numeric bridge" src="https://img.shields.io/badge/Cursor-bridge%20required-b9b9c7?style=flat-square"></a>
  <a href="docs/PROVIDERS.md#external-numeric-bridge"><img alt="Antigravity requires numeric bridge" src="https://img.shields.io/badge/Antigravity-bridge%20required-4e8cff?style=flat-square"></a>
  <a href="docs/PROVIDERS.md#external-numeric-bridge"><img alt="OpenCode automatic local token activity" src="https://img.shields.io/badge/OpenCode-local%20activity-8b9ba8?style=flat-square"></a>
</p>
<p align="center">
  <a href="#make-it-yours"><img alt="Five companions: NOVA, ORBIT, CLAUDE, WRAITH and GLITCH" src="https://img.shields.io/badge/companions-5%20to%20choose%20from-35d07f?style=flat-square"></a>
  <a href="#make-it-yours"><img alt="Four saved color themes" src="https://img.shields.io/badge/themes-4%20saved%20palettes-c49aff?style=flat-square"></a>
  <a href="#make-it-yours"><img alt="Per-provider quota selection saved on display" src="https://img.shields.io/badge/quota%20windows-per%20AI%20%2B%20saved-54c4f2?style=flat-square"></a>
  <a href="docs/QUICK_START.md"><img alt="Larger quota notifications" src="https://img.shields.io/badge/alerts-large%20text%20%2B%20tap%20targets-ffb96a?style=flat-square"></a>
</p>
<p align="center">
  <a href="https://github.com/catorendal-a11y/limitbuddy/releases/tag/v1.19.1-rc25"><img alt="LimitBuddy terminal source" src="https://img.shields.io/badge/LimitBuddy-Python%20terminal-54c4f2?style=flat-square"></a>
  <a href="docs/QUICK_START.md"><img alt="No AI preselected" src="https://img.shields.io/badge/AI%20preselection-none-35d07f?style=flat-square"></a>
  <a href="docs/QUICK_START.md"><img alt="Host stays running when window closes" src="https://img.shields.io/badge/close%20app-host%20stays%20running-35d07f?style=flat-square"></a>
  <a href="docs/DEVELOPMENT.md"><img alt="Python source requires 3.10 or later" src="https://img.shields.io/badge/Python%20source-3.10%2B-3776ab?style=flat-square&amp;logo=python&amp;logoColor=white"></a>
</p>
<p align="center">
  <a href="docs/GITHUB_SECURITY.md"><img alt="USB-only display connection" src="https://img.shields.io/badge/display%20connection-USB%20only-6f8996?style=flat-square"></a>
  <a href="docs/PROVIDERS.md#privacy-and-limits"><img alt="No model prompts generated by the monitor" src="https://img.shields.io/badge/model%20prompts-none-35d07f?style=flat-square"></a>
  <a href="docs/GITHUB_SECURITY.md"><img alt="Cloud credentials stay on the PC" src="https://img.shields.io/badge/cloud%20keys-PC%20only-35d07f?style=flat-square"></a>
</p>


*Quota needs the provider's supported account, key or bridge. Gemini, OpenCode and external numeric bridges report activity only. S3 is experimental.*

[![Support LimitBuddy — give this project a star on GitHub](docs/media/star-project.svg)](https://github.com/catorendal-a11y/limitbuddy)

**[Download LimitBuddy terminal](https://github.com/catorendal-a11y/limitbuddy/releases/tag/v1.19.1-rc25)** · [Quick Start](docs/QUICK_START.md) · [Provider setup](docs/PROVIDERS.md) · [Ask a question](https://github.com/catorendal-a11y/limitbuddy/discussions/categories/q-a)

## How it works

```mermaid
flowchart LR
  A["AI tools<br>local usage records"] --> H["PC host<br>limitbuddy"]
  Q["Provider quota<br>HTTPS from the PC"] --> H
  H -- "USB serial" --> D["ESP32 display<br>P4 or S3"]
  T["limitbuddy terminal"] -. "setup, firmware" .-> H
```

The host reads local token counters and queries quota; the display only receives numbers. No incoming network listener, no model prompts. See [Privacy and security](#privacy-and-security).

## Quick install (Windows x64)

1. Download the [terminal ZIP](https://github.com/catorendal-a11y/limitbuddy/releases/download/v1.19.1-rc25/nova-v1.19.1-rc25-windows-x64-terminal.zip) ([SHA-256](https://github.com/catorendal-a11y/limitbuddy/releases/download/v1.19.1-rc25/SHA256SUMS.txt)) and extract it into a permanent, writable folder (not `Program Files`).
2. Double-click **Install-LimitBuddy.cmd** once. It registers `limitbuddy` for your user; no admin rights, Python or extra downloads.
3. Open a **new** terminal and run `limitbuddy`.
4. **Settings > Edit settings**: choose board (P4 or S3), providers and USB port, then save. No AI is preselected; with several boards connected pick the explicit COM port.
5. New board? **Device > Firmware > First installation**, review board and port, type `FLASH` (resets display settings). Nothing is flashed automatically.
6. **Settings > Start host**. It keeps running after you close the terminal; switch on **Start at Windows sign-in** in Edit settings to survive restarts.
7. Optional: **Agents > Provider events** links Claude Code and/or Codex for the Agents screen and the "needs you" alert. Nothing is linked automatically.

![Actual terminal widgets rendered with synthetic sample data](docs/media/terminal-preview.png)

![The Agents page: one card per session, in the same colour as on the display](docs/media/terminal-agents.png)

Keys: **1-5** pages, **Tab/Enter** controls, **?** help, **Q** quit; use a 120 x 30 window or larger. More: [terminal guide](docs/TERMINAL.md), [PC requirements](docs/PC_REQUIREMENTS.md).

> [!WARNING]
> The ZIP is built by GitHub from this repository but is not publisher-signed. SmartScreen may warn: choose **More info > Run anyway** only for a download from this repository's Releases, and compare `SHA256SUMS.txt`. See [Windows trust](docs/WINDOWS_TRUST.md).

**Troubleshooting**

| Symptom | Fix |
| --- | --- |
| `limitbuddy` not recognized | Open a **new** terminal after the installer. |
| Display says **NO HOST** | **Settings > Start host**; check the port in Edit settings. |
| No USB connection | Use a data cable and the right port; close other serial tools. |
| Agents screen empty | Expected until providers are linked (step 7). |
| Robot does not react | Check observed status and **Settings / Recent host log**; **Device / Check USB**. |
| Anything else | **History > Diagnostic export** (no keys or conversations) for an [issue](https://github.com/catorendal-a11y/limitbuddy/issues). |

Upgrading, removing or Linux/macOS: [terminal guide](docs/TERMINAL.md#upgrade-and-migrate). GitHub's automatic **Source code (zip)** has no prebuilt firmware.

## What you need

| Display board | Status | USB connector |
| --- | --- | --- |
| **GUITION JC4880P433 ESP32-P4** | Supported | Espressif USB data port |
| **Original Waveshare ESP32-S3-Touch-LCD-4.3** | **Experimental; untested on physical S3** | **USB TO UART** (flashing and daily use) |

The S3 is the original CH422G model, **not B or C**. [Board details](docs/BOARDS.md). You also need a **USB data cable**, a **Windows 10/11 x64 PC** and your own AI account or CLI. The ZIP includes a private Python runtime and both boards' firmware; no PlatformIO or Arduino IDE for ordinary use.

## Meet your desk companion

| NOVA | ORBIT with the Ocean theme | CLAUDE with the Amethyst theme |
| --- | --- | --- |
| ![NOVA, a sentinel with slanted light slits, on the Forest theme](docs/ui/nova-working.png) | ![ORBIT, a faceted sensor drone, on the Ocean theme](docs/ui/orbit-ocean.png) | ![CLAUDE, the pixel critter with a dark visor, on the Amethyst theme](docs/ui/claude-amethyst.png) |

| WRAITH (P4 only) | GLITCH (P4 only) | Choosing a companion |
| --- | --- | --- |
| ![WRAITH, a hooded figure with blade eyes and a chest rune](docs/ui/nova-wraith.png) | ![GLITCH, a CRT-headed terminal with block-cursor eyes](docs/ui/nova-glitch.png) | ![Companion and theme settings with five companions on two rows](docs/ui/settings-appearance-glitch.png) |

Sharp and a little menacing on purpose, not mascots. WRAITH and GLITCH are P4-only (the S3 has no flash left and shows NOVA instead). The figure shows a mood-coloured radar ring, a status tag (RUN / WAIT / FAULT / DONE), one chip per live session, a ring for the tightest quota window, and a standby tag when idle. Previews are LVGL renders with synthetic data, not photographs.

## Providers

Token activity and account quota are separate signals: a provider can animate the robot without reporting remaining quota.

| Provider | Token activity | Quota |
| --- | --- | --- |
| **Codex** | Local Codex database | Signed-in official Codex CLI (setup offers install/sign-in). |
| **ZCode** | Local ZCode database | Your optional Z.AI coding-plan key. |
| **Claude Code** | Local CLI usage records | Your Claude Code login (read-only, about every 5 minutes) or the optional statusline bridge. |
| **Gemini CLI** | Recorded local sessions | Activity only. |
| **OpenCode** | Local SQLite usage | Activity only. |
| **GitHub Copilot, Cursor, Antigravity** | External numeric bridge | Activity only; selecting them alone imports nothing. |

An **external bridge** supplies cumulative token counts. See [provider requirements](docs/PROVIDERS.md) and [Codex setup](docs/CODEX_SETUP.md); the monitor never asks for an OpenAI password or key.

> [!NOTE]
> **Claude quota needs no setup if you are signed in to Claude Code on this PC.** Claude Code desktop does not run the statusline command, and recent CLI versions no longer send `rate_limits` there. The host therefore reads your 5-hour and 7-day quota from Anthropic's undocumented `api/oauth/usage` endpoint, using the login in `~/.claude/.credentials.json` (`CLAUDE_CONFIG_DIR` is honoured). The token is read only inside the quota worker, never logged or stored; the endpoint is queried at most every 5 minutes, with backoff on HTTP 429. A fresh statusline reading wins. If the login expired, the Claude card shows "check login" until you use Claude Code again.

## Make it yours

On the display: **MENU > SETTINGS**.

| Where | What |
| --- | --- |
| **AI USAGE** | **< PREV / NEXT >** picks an AI and its quota window; **AUTO / MOST URGENT** follows the tightest; **REFRESH** requests a host update. Saved on the display; alerts still check every window. |
| **APPEARANCE** | Companion (NOVA, ORBIT, CLAUDE; P4 also WRAITH, GLITCH) and theme (**Forest, Ocean, Amethyst, Ember**). Applies immediately and is saved. |

Quota windows: **Codex** 5 HOURS / 7 DAYS. **ZCode** 5 HOURS / 7 DAYS model quotas when the plan supplies them, plus **MONTHLY MCP** (tool calls, not model tokens; [usage guide](https://zcode.z.ai/en/docs/usage-stats)). **Claude Code** 5 HOURS / 7 DAYS. **NOT REPORTED** never means unused: the companion shows unavailable until real data arrives.

| Codex window selection | ZCode window selection |
| --- | --- |
| ![Codex quota choices and sign-in help](docs/ui/settings-quota-codex.png) | ![ZCode model quotas and monthly MCP tool quota](docs/ui/settings-quota-zcode.png) |

| Robot and color settings | Provider dashboard |
| --- | --- |
| ![Robot selection and theme settings](docs/ui/settings-appearance-ocean.png) | ![Provider dashboard in the Ocean theme](docs/ui/dashboard-ocean.png) |

| ORBIT in Amethyst | NOVA in Ember |
| --- | --- |
| ![ORBIT companion in the Amethyst theme](docs/ui/orbit-amethyst.png) | ![NOVA companion in the Ember theme](docs/ui/nova-ember.png) |

**Read the display at a glance**

| Needs you | Even-burn marker | Tightest window | History |
| --- | --- | --- | --- |
| ![NOVA with a WAIT tag while a session needs you](docs/ui/nova-session-waiting.png) | ![A white marker shows where an even burn would be by now](docs/ui/dashboard-pace-marker.png) | ![A ring shows the tightest quota window](docs/ui/nova-urgent-dial.png) | ![Seven-day history chart with weekday names](docs/ui/history-today-7d.png) |

The white marker on a bar is where an even burn would be by now: a "left" fill shorter than the marker means the quota is going faster than its window. Low or critical cards get an amber or red edge. [What each mark means](docs/QUICK_START.md#reading-the-display).

Also: reset countdowns, manual refresh, low/critical warnings ([larger alert preview](docs/ui/quota-critical-notification.png)), session history, brightness presets, idle dimming and night brightness. P4 dims with PWM; S3 dims the rendered image ([board differences](docs/BOARDS.md#brightness-and-performance)). [Provider details screen](docs/ui/details-ocean.png).

## If the robot is quiet

The robot follows **increases in recorded token counters**. The first sample is a baseline, and some clients save usage only when a request finishes, so activity can lag. This is an activity and quota display, not a billing ledger or per-token stream. Unsupported local formats stay unavailable; display history clears after a firmware restart.

| Symptom | First check |
| --- | --- |
| Codex quota unavailable | **Provider setup**: finish official CLI sign-in (needs a ChatGPT-backed login). |
| Claude card says "check login" | Open Claude Code once; the card recovers on the next query. |
| External provider inactive | Connect its numeric bridge. |

## Privacy and security

- The PC reads selected local usage sources, queries provider quota over HTTPS and sends display data over USB. No incoming network listener, no automatic code updater.
- For Claude, your existing login is used only to query quota; never logged or stored.
- Your optional Z.AI key is stored in plaintext in git-ignored `tools/aim_host.json`; keep it private. `ZAI_API_KEY` in the environment takes precedence; `.env` files are not loaded.
- GitHub Actions run on GitHub-hosted machines; no runner or webhook connects to the maintainer's PC. No maintainer credentials ship in source or releases.

[Security and private reporting](SECURITY.md) · [Host security review](docs/SECURITY_REVIEW.md) · [GitHub safeguards](docs/GITHUB_SECURITY.md)

## Watch the overview

[![Watch LimitBuddy: NOVA and ORBIT on an ESP32 touchscreen](docs/media/youtube-thumbnail.png)](https://www.youtube.com/watch?v=1JR9_E1lWDg)

[Two-minute video](https://www.youtube.com/watch?v=1JR9_E1lWDg) with subtitles (earlier companions and the retired graphical PC app; current releases use the terminal). UI previews use synthetic data.

## Run from source or contribute

Built one? [Show and tell](https://github.com/catorendal-a11y/limitbuddy/discussions/categories/show-and-tell) · [Q&A](https://github.com/catorendal-a11y/limitbuddy/discussions/categories/q-a) · [Ideas](https://github.com/catorendal-a11y/limitbuddy/discussions/categories/ideas) · [Report a bug](https://github.com/catorendal-a11y/limitbuddy/issues/new/choose). Keep keys, account data and private logs out of posts. A GitHub star helps others find the project.

Source needs **Python 3.10+**. Windows: double-click **AI-Monitor.bat**. Linux/macOS:

```sh
sh setup.sh
.venv/bin/python tools/aim_terminal.py
```

[Developer guide](docs/DEVELOPMENT.md) · [Release guide](docs/RELEASING.md) · [Contributing](CONTRIBUTING.md) · [Provider roadmap](docs/PROVIDER_ROADMAP.md) · [All releases](https://github.com/catorendal-a11y/limitbuddy/releases)

The graphical Windows app and EXE distribution are retired; see the [migration notes](docs/TERMINAL.md#upgrade-and-migrate).

Project-owned code and original NOVA/ORBIT artwork use [MIT](LICENSE). Drivers, dependencies, fonts and provider marks keep their own terms: [third-party notices](THIRD_PARTY_NOTICES.md), [NOVA/logo sources](assets/nova/SOURCES.md), [ORBIT artwork](assets/orbit/SOURCES.md). Independent project, not endorsed by its AI providers.
