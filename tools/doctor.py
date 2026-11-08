"""One readable health check for this installation.

Read-only: reuses the host status, setup report and ownership checks. It opens no second USB
connection, starts no model turn and prints no keys, tokens or paths outside this installation.
"""
import base64
import os
from pathlib import Path
import tempfile

from host_security import safe_text
from project_version import HOST_VERSION


def _row(name, ok, detail):
    return dict(name=name, ok=ok, detail=safe_text(detail, 160))


def firmware_matches(firmware, host=HOST_VERSION):
    """Firmware reports '1.19.1-rc28' or 'v1.19.1-rc28'; None when unknown."""
    if not isinstance(firmware, str) or not firmware or firmware == 'Unknown':
        return None
    return firmware.lstrip('v') == host.lstrip('v')


def command_owner(root, bin_dir=None):
    """True when the limitbuddy command starts this installation, False for another, None if absent."""
    folder = Path(bin_dir) if bin_dir else Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs/NOVA Terminal/bin'
    try:
        text = (folder / 'limitbuddy.cmd').read_text(encoding='utf-8', errors='replace')[:4096]
    except OSError:
        return None
    marker = 'AI_MONITOR_TERMINAL_OWNER='
    if marker not in text:
        return False
    encoded = text.split(marker, 1)[1].split()[0]
    try:
        owner = base64.b64decode(encoded).decode('utf-8')
    except (ValueError, UnicodeDecodeError):
        return False
    return os.path.normcase(os.path.normpath(owner)) == os.path.normcase(os.path.normpath(str(root)))


def last_update_note():
    try:
        lines = (Path(tempfile.gettempdir()) / 'limitbuddy-update.log').read_text(encoding='utf-8', errors='replace').splitlines()
    except OSError:
        return None
    return lines[-1][:160] if lines else None


def claude_login():
    """(ok, detail) without opening the login file: only the quota worker reads the token."""
    import aim_host as host
    if not host.claude_credentials().is_file():
        return None, 'No Claude Code login on this PC'
    if host.claude_command():
        return True, 'Login found; the host renews it with the Claude CLI near expiry'
    return False, 'Login found; install the Claude Code CLI so the host can renew it'


def run(root, status=None, report=None, autostart_state=None, command=None):
    """List of {name, ok (True/False/None = not applicable), detail}."""
    from aim_control import local_config, owned_hosts
    from host_status import read_status
    root = Path(root).resolve()
    rows = []
    try:
        config = local_config(root)
        rows.append(_row('Settings', True, 'Valid; ' + str(len(config['providers'])) + ' AI(s) selected'))
    except (ValueError, OSError, KeyError):
        rows.append(_row('Settings', False, 'Invalid or missing; use Settings > Recover invalid settings'))
        return rows
    processes = owned_hosts(root)
    rows.append(_row('Host', bool(processes), 'Running' if processes else 'Stopped; use Settings > Start host'))
    health = (status if status is not None else read_status(root, {p.pid for p in processes})) or {}
    connected = health.get('state') == 'connected'
    rows.append(_row('USB display', connected if processes else None,
                     ('Connected on ' + str(health.get('port', ''))) if connected else 'Not connected; check the cable and port'))
    firmware = health.get('hardware', {}).get('firmwareVersion')
    match = firmware_matches(firmware)
    rows.append(_row('Firmware', match, 'Unknown until the display reports' if match is None else
                     ('Same version as this host' if match else str(firmware) + ' differs from ' + HOST_VERSION + '; use Device > Firmware')))
    if autostart_state is None:
        from autostart import state
        autostart_state = state(root)
    wanted = config.get('start_host_at_login') is True
    rows.append(_row('Start at sign-in', (autostart_state == 'on') == wanted if autostart_state != 'foreign' else False,
                     {'on': 'Starts this installation', 'off': 'Off', 'other': 'Starts another LimitBuddy folder',
                      'foreign': 'An unrelated entry uses this name'}.get(autostart_state, 'Unknown')))
    owner = command_owner(root) if command is None else command
    rows.append(_row('limitbuddy command', owner, 'Starts this installation' if owner else
                     ('Not installed; run Install-LimitBuddy.cmd' if owner is None else 'Starts another folder; run Install-LimitBuddy.cmd here')))
    if report is None:
        from provider_setup import setup_report
        report = setup_report(root)
    for item in report:
        name = item['provider'].upper()
        events = item.get('events')
        linked = isinstance(events, str) and events.startswith('installed')
        rows.append(_row(name + ' events', None if events == 'unsupported' else linked,
                         'Hooks linked' + events[len('installed'):] if linked else
                         ('Not linked; use Agents > Provider events' if events == 'not linked' else str(events))))
        quota = item.get('quota')
        if quota != 'unsupported':
            rows.append(_row(name + ' quota', True if quota == 'verified' else False if quota == 'failed' else None,
                             {'verified': 'Reported by the host', 'failed': 'Last request failed; see Settings > Recent host log',
                              'pending-running': 'Waiting for the first report', 'pending-stopped': 'Host stopped'}.get(quota, str(quota))))
    if 'claude' in config['providers']:
        ok, detail = claude_login()
        rows.append(_row('Claude login', ok, detail))
    note = last_update_note()
    if note:
        rows.append(_row('Last update', 'failed' not in note.lower(), note))
    return rows


def render(rows):
    marks = {True: 'OK  ', False: 'FIX ', None: ' -  '}
    width = max((len(row['name']) for row in rows), default=0)
    return '\n'.join(marks[row['ok']] + row['name'].ljust(width) + '  ' + row['detail'] for row in rows)
