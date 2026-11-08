"""Shared parsing and error wording for provider quota requests.

Bounded responses, strict numbers and short, credential-free failure categories.
"""
import json
import math
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from host_security import open_provider_request, read_local_json  # patched in tests through this module

MAX_RESPONSE_BYTES = 65536


class CredentialError(ValueError):
    pass


def credential(value, optional=False):
    if not isinstance(value, str):
        raise CredentialError("Invalid credential format")
    value = value.strip()
    if not value and optional:
        return ""
    if not value or any(not 33 <= ord(character) <= 126 for character in value):
        raise CredentialError("Credentials must be a single printable token")
    return value


def read_json_response(response):
    raw = response.read(MAX_RESPONSE_BYTES + 1)
    if len(raw) > MAX_RESPONSE_BYTES:
        raise ValueError("API response exceeds size limit")
    data = json.loads(raw.decode("utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("API response must be an object")
    return data


def window_minutes(seconds):
    if seconds is None:
        return 0
    if isinstance(seconds, bool):
        raise ValueError("Invalid window duration")
    seconds = float(seconds)
    if not math.isfinite(seconds) or seconds < 0 or seconds / 60 > 0xffffffff:
        raise ValueError("Invalid window duration")
    return int(seconds // 60)


def provider_failure(provider, error):
    # Header/JSON exceptions may contain credentials or server response text.
    # Return a category without copying exception details to the display/log.
    if isinstance(error, CredentialError):
        return f"{provider}: invalid login or API key"
    if isinstance(error, FileNotFoundError):
        return f"{provider}: login file not found"
    if isinstance(error, (ValueError, TypeError, KeyError, AttributeError)):
        return f"{provider}: invalid response data"
    if isinstance(error, OSError):
        return f"{provider}: connection failed; retrying"
    return f"{provider}: request failed; retrying"


def now_iso_epoch(epoch_s):
    return datetime.fromtimestamp(epoch_s, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def percent_value(value):
    if value is None or isinstance(value, bool):
        raise ValueError("Missing usage percentage")
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise ValueError("Invalid usage percentage")
    return number


class ProviderNotice(str):
    def __new__(cls, message, retry_after=0):
        value = super().__new__(cls, message)
        value.retry_after = retry_after
        return value


def retry_after_seconds(headers):
    value = headers.get("Retry-After") if headers else None
    if not isinstance(value, str):
        return 0
    try:
        seconds = int(value) if value.strip().isdigit() else math.ceil(parsedate_to_datetime(value).timestamp() - time.time())
        return max(0, min(86400, seconds))
    except (ValueError, TypeError, OverflowError, OSError):
        return 0


def http_notice(provider, error):
    delay = retry_after_seconds(error.headers)
    if error.code in (401, 403):
        return ProviderNotice(f"{provider}: check login or API key", delay)
    if error.code == 429:
        return ProviderNotice(f"{provider}: rate limited; retrying", delay)
    return ProviderNotice(f"{provider}: HTTP {error.code}; retrying", delay)


def reset_display(value, minutes=0):
    """Use the PC's local timezone, retaining dates for long quota windows."""
    if not value:
        return ""
    try:
        reset = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone()
    except (ValueError, TypeError, AttributeError):
        return str(value)[:19]
    return reset.strftime("%d %b %H:%M" if minutes >= 1440 else "%H:%M")


def zai_reset_iso(value):
    if not value:
        return ""
    try:
        milliseconds = float(value)
    except (ValueError, TypeError):
        return str(value)
    try:
        return now_iso_epoch(milliseconds / 1000.0)
    except (ValueError, OverflowError, OSError):
        return ""



def reset_seconds(value, epoch_now=None):
    if not isinstance(value, str) or "T" not in value:
        return None
    try:
        reset = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if reset.tzinfo is None:
            return None
        remaining = math.ceil(reset.timestamp() - (time.time() if epoch_now is None else epoch_now))
        return max(0, min(0xffffffff - 60, remaining))
    except (ValueError, OverflowError, OSError):
        return None
