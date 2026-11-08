"""Codex (ChatGPT plan) quota from the local Codex CLI login; the token stays in memory."""
import json
import urllib.error
import urllib.request

from codex_support import codex_command, codex_home, read_rate_limits
from project_version import HOST_VERSION, numeric_version

import quota_common as common
from quota_common import (credential, read_json_response, window_minutes, provider_failure, now_iso_epoch,
                          percent_value, http_notice)


CODEX_AUTH = codex_home() / 'auth.json'


def fetch_codex():
    """Codex (ChatGPT plan) usage via the local Codex CLI login token."""
    command = codex_command()
    if command:
        try:
            data = read_rate_limits(command)
            buckets = data.get('rateLimitsByLimitId')
            limit = buckets.get('codex') if isinstance(buckets, dict) else None
            if limit is None: limit = data.get('rateLimits')
            if not isinstance(limit, dict) or limit.get('limitId') not in (None, 'codex'):
                raise ValueError('No supported Codex quota bucket')
            rows = []
            for key, title in [('primary','Session'),('secondary','Secondary')]:
                window = limit.get(key)
                if window is None: continue
                if not isinstance(window, dict): raise ValueError('Invalid Codex window')
                minutes = window.get('windowDurationMins')
                if minutes is None: minutes = 0
                if type(minutes) is not int or not 0 <= minutes <= 0xffffffff: raise ValueError('Invalid window duration')
                reset = window.get('resetsAt')
                percent = min(100.0, percent_value(window.get('usedPercent')))
                rows.append({'title':'Week' if key == 'secondary' and minutes == 10080 else title,
                             'usedPercent':percent,
                             'windowMinutes':minutes, 'resetsAt':now_iso_epoch(reset) if reset is not None else ''})
            if not rows: return None, 'Codex: no plan quota; sign in to CLI with ChatGPT'
            return rows, None
        except Exception:
            return None, 'Codex: quota unavailable; retry setup or update the official CLI'
    try:
        auth = common.read_local_json(CODEX_AUTH)
        access = (auth.get("tokens") or {}).get("access_token")
        if not access:
            return None, "Codex: no access_token in auth.json"
        access = credential(access)
        req = urllib.request.Request("https://chatgpt.com/backend-api/wham/usage")
        req.add_header("Authorization", "Bearer " + access)
        req.add_header("User-Agent", "LimitBuddy/" + numeric_version(HOST_VERSION))
        with common.open_provider_request(req) as r:
            data = read_json_response(r)
        rl = data.get("rate_limit") or {}
        rows = []
        pw = rl.get("primary_window") or {}
        if pw:
            rows.append({
                "title": "Session",
                "usedPercent": percent_value(pw.get("used_percent")),
                "resetsAt": now_iso_epoch(pw["reset_at"]) if pw.get("reset_at") else "",
                "windowMinutes": window_minutes(pw.get("limit_window_seconds")),
            })
        sw = rl.get("secondary_window") or {}
        if sw:
            minutes = window_minutes(sw.get("limit_window_seconds"))
            rows.append({
                "title": "Week" if minutes == 10080 else "Secondary",
                "usedPercent": percent_value(sw.get("used_percent")),
                "resetsAt": now_iso_epoch(sw["reset_at"]) if sw.get("reset_at") else "",
                "windowMinutes": minutes,
            })
        if not rows:
            return None, "Codex: no rate_limit windows in response"
        return rows, None
    except urllib.error.HTTPError as error:
        return None, http_notice("Codex", error)
    except Exception as e:
        return None, provider_failure("Codex", e)
