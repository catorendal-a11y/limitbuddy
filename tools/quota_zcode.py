"""Z.AI GLM coding plan quota. The key is sent raw (no Bearer prefix) and never logged."""
import math
import urllib.error
import urllib.request

import quota_common as common
from quota_common import (credential, read_json_response, provider_failure, percent_value, http_notice,
                          zai_reset_iso)


def fetch_zcode(api_key):
    """Z.AI GLM coding plan quota. Auth: raw key, NO Bearer prefix."""
    try:
        api_key = credential(api_key)
        req = urllib.request.Request("https://api.z.ai/api/monitor/usage/quota/limit")
        req.add_header("Authorization", api_key.strip())
        req.add_header("Accept-Language", "en-US,en")
        with common.open_provider_request(req) as r:
            data = read_json_response(r)
        success, code = data.get("success"), data.get("code")
        if success is not None and type(success) is not bool:
            raise ValueError("Invalid success flag")
        accepted_code = type(code) is int and code in (0, 200)
        accepted = success is not False and (success is True or accepted_code) and (code is None or accepted_code)
        if not accepted:
            code = data.get("code")
            if type(code) is int and code in (401, 403):
                return None, "Z.AI: check login or API key"
            if type(code) is int and code == 429:
                return None, "Z.AI: rate limited; retrying"
            return None, "Z.AI: request rejected"
        limits = ((data.get("data") or {}).get("limits")) or []
        rows = []
        for lim in limits:
            quota_type = lim.get("type")
            if quota_type not in ("CREDIT_LIMIT", "TOKENS_LIMIT", "TIME_LIMIT"):
                continue
            unit = lim.get("unit")
            # The provider's official usage plugin distinguishes monthly MCP
            # calls (TIME_LIMIT) from model quotas. Unit 6 is a weekly model
            # window, not a month; unit 3 is hours (normally number=5).
            if quota_type == "TIME_LIMIT":
                title, minutes = "Monthly MCP", 43200
            elif type(unit) is int and unit in (3, 6):
                number = lim.get("number", 5 if unit == 3 else 1)
                if type(number) is not int or number < 1:
                    raise ValueError("Invalid quota window length")
                minutes = number * (60 if unit == 3 else 10080)
                if minutes > 0xffffffff:
                    raise ValueError("Invalid quota window length")
                title = "Session" if minutes == 300 else "Week" if minutes == 10080 else "Quota"
            elif quota_type == "TOKENS_LIMIT" and unit is None:
                title, minutes = "Session", 300  # legacy official plugin format
            else:
                title, minutes = "Quota", 0
            percentage = lim.get("percentage")
            if percentage is None and quota_type == "TIME_LIMIT":
                used, total = lim.get("currentValue"), lim.get("usage")
                if (type(used) not in (int, float) or type(total) not in (int, float)
                        or not math.isfinite(used) or not math.isfinite(total)
                        or used < 0 or total <= 0):
                    raise ValueError("Invalid MCP quota counts")
                percentage = 100 * used / total
            reset = lim.get("nextResetTime") or lim.get("resetAt")
            reset_iso = zai_reset_iso(reset)
            rows.append({
                "title": title,
                "usedPercent": percent_value(percentage),
                "resetsAt": reset_iso,
                "windowMinutes": minutes,
            })
        if not rows:
            return None, "Z.AI: no quota entries"
        return rows, None
    except urllib.error.HTTPError as error:
        return None, http_notice("Z.AI", error)
    except Exception as e:
        return None, provider_failure("Z.AI", e)


# ───────────────────────────────────────────────────────────────────────────────
# PANEL LINK (esp32-ai-monitor protocol)
# ───────────────────────────────────────────────────────────────────────────────
