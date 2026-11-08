"""Claude plan quota from the local Claude Code login (undocumented oauth usage endpoint).

Read-only: the token is read in the quota worker, never logged or stored. Near expiry only the
official `claude auth status` renews it; LimitBuddy never writes credentials.
"""
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from claude_paths import config_root
from host_security import allowed_executable, path_executable
from project_version import HOST_VERSION, numeric_version

import quota_common as common
from quota_common import (credential, read_json_response, provider_failure, now_iso_epoch, percent_value,
                          ProviderNotice, retry_after_seconds, http_notice)


def LOG(message):
    import aim_host  # the host owns the protected log file
    aim_host.LOG(message)


CLAUDE_USAGE_URL = "https://api.anthropic.com/api/oauth/usage"
CLAUDE_MIN_FETCH_SECONDS = 300  # The undocumented endpoint rate-limits aggressively.
CLAUDE_RENEW_MARGIN_MS = 10 * 60 * 1000
CLAUDE_RENEW_TIMEOUT_SECONDS = 10


def claude_credentials():
    return config_root() / ".credentials.json"


def claude_reset_iso(value):
    if value is None:
        return ""
    if not isinstance(value, str) or len(value) > 64:
        raise ValueError("Invalid reset time")
    moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if moment.tzinfo is None:
        raise ValueError("Reset time lacks a timezone")
    return now_iso_epoch(moment.timestamp())


def claude_command():
    local = Path.home() / ".local/bin" / ("claude.exe" if os.name == "nt" else "claude")
    for candidate in (path_executable("claude.exe" if os.name == "nt" else "claude"), str(local)):
        if candidate and allowed_executable(candidate):
            return candidate
    return None


def renew_claude_login():
    """Let the official Claude Code CLI renew its own login file; no model turn, no output kept."""
    command = claude_command()
    if not command:
        return False
    try:
        subprocess.run([command, "auth", "status"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=CLAUDE_RENEW_TIMEOUT_SECONDS, check=False,
                       creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    except (OSError, subprocess.SubprocessError):
        pass  # The request below then reports the expired login.
    return True


def claude_oauth():
    auth = common.read_local_json(claude_credentials())
    oauth = auth.get("claudeAiOauth") if isinstance(auth, dict) else None
    return oauth if isinstance(oauth, dict) else {}


# Model-specific weekly limits follow the shared ones; the panel keeps the first three reported.
CLAUDE_WINDOWS = (("five_hour", "Session", 300), ("seven_day", "Week", 10080),
                  ("seven_day_opus", "Opus week", 10080), ("seven_day_sonnet", "Sonnet week", 10080))
_claude_fields_seen = set()


def note_claude_fields(data):
    """Log the names (never values) of unparsed usage fields once, so new limits can be supported later."""
    if not isinstance(data, dict):
        return
    known = {name for name, _, _ in CLAUDE_WINDOWS}
    fields = sorted(str(key)[:40] for key, value in data.items()
                    if key not in known and value not in (None, [], {}) and key not in _claude_fields_seen)
    if fields:
        _claude_fields_seen.update(fields)
        LOG("claude: unparsed usage fields: " + ", ".join(fields[:12]))


def fetch_claude():
    """Claude plan quota via the local Claude Code OAuth login (read-only; token stays in memory)."""
    try:
        cli_missing = False
        oauth = claude_oauth()
        expires = oauth.get("expiresAt")
        # Claude Code desktop does not rewrite this file, so its 8-hour token lapses unless the CLI renews it.
        if type(expires) in (int, float) and expires - time.time() * 1000 < CLAUDE_RENEW_MARGIN_MS:
            cli_missing = not renew_claude_login()
            oauth = claude_oauth()
        access = credential(oauth.get("accessToken"))
        req = urllib.request.Request(CLAUDE_USAGE_URL)
        req.add_header("Authorization", "Bearer " + access)
        req.add_header("anthropic-beta", "oauth-2025-04-20")
        req.add_header("User-Agent", "LimitBuddy/" + numeric_version(HOST_VERSION))
        with common.open_provider_request(req) as r:
            data = read_json_response(r)
        rows = []
        note_claude_fields(data)
        for name, title, minutes in CLAUDE_WINDOWS:
            window = data.get(name)
            if window is None:
                continue
            if not isinstance(window, dict):
                raise ValueError("Invalid quota window")
            if window.get("utilization") is None:
                continue
            # utilization is already a percentage (4.0 means 4 %), never a fraction.
            rows.append({"title": title, "usedPercent": percent_value(window["utilization"]),
                         "resetsAt": claude_reset_iso(window.get("resets_at")), "windowMinutes": minutes})
        if not rows:
            return None, "Claude: no plan quota in response"
        return rows[:3], None  # the panel protocol carries three windows
    except urllib.error.HTTPError as error:
        if cli_missing and error.code in (401, 403):
            return None, ProviderNotice("Claude: login expired; install the Claude Code CLI to renew it",
                                        retry_after_seconds(error.headers))
        return None, http_notice("Claude", error)
    except Exception as e:
        return None, provider_failure("Claude", e)
