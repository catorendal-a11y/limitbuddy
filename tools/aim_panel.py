"""USB connection to the display: framing, handshake and acknowledgements."""
from datetime import datetime, timezone
import json
import math
import sys
import time

import serial

from board_profiles import matches_info
from host_status import HostStatus
from token_activity import TokenReporter, TokenSampler

MAX_FRAME_BYTES = 4095


def LOG(message):
    # The host script owns the log file and its lock, whether it runs as __main__ or is imported.
    (sys.modules.get('aim_host') or sys.modules['__main__']).LOG(message)


class ProviderRetries:
    """Monotonic, independent cooldowns survive USB reconnections."""
    def __init__(self, interval=240):
        self.interval = interval
        self.states = {}

    def remaining(self, provider):
        state = self.states.get(provider)
        return max(0, math.ceil(state[1] - time.monotonic())) if state else 0

    def deferred_notice(self, provider):
        return f"{provider}: retry in {self.remaining(provider)} s. {self.states[provider][2]}"

    def failed(self, provider, notice):
        failures = min(9, self.states.get(provider, (0, 0, ""))[0] + 1)
        delay = max(min(3600, max(15, self.interval) * 2 ** (failures - 1)),
                    getattr(notice, "retry_after", 0))
        self.states[provider] = (failures, time.monotonic() + delay, str(notice))

    def succeeded(self, provider):
        self.states.pop(provider, None)


def clock_fields():
    local = datetime.now().astimezone()
    return {
        "time": local.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "displayTime": local.strftime("%H:%M"),
        "displaySeconds": local.second,
        "tzOffsetMinutes": int(local.utcoffset().total_seconds() // 60),
    }


class Panel:
    def __init__(self, port_name):
        self.ser = serial.Serial(port_name, 115200, timeout=0.2, write_timeout=2)
        self.name = port_name
        self._rx = bytearray()
        self.boot_id = None
        self.last_uptime = None
        self.refresh_request_id = None
        self.last_poll_success = True
        self.retries = ProviderRetries()
        self.cycle_active = False
        self.active_refresh_id = None
        self.cycle_deadline = None
        self.activity_supported = False
        self.tokens_supported = False
        self.provider_selection_supported = False
        self.sessions_supported = False
        self.token_reporter = None
        self.info = {}
        self.expected_board = None
        self.hardware_pending = False
        self.live_client = None
        self.live_retry_at = 0
        self.permission_runtime = None  # Explicit validated setup only; never auto-enable from USB.
        self.mirror_service = None
        self.companion_service = None

    def attach_permission_runtime(self, runtime):
        from permission_runtime import PermissionRuntime
        if not isinstance(runtime, PermissionRuntime):
            raise ValueError('A locally validated permission runtime is required')
        previous = getattr(self, 'permission_runtime', None)
        if previous is not None and previous is not runtime:
            previous.close()
        self.permission_runtime = runtime
        return runtime.attach(self)

    def close(self):
        try:
            runtime = getattr(self, 'permission_runtime', None)
            if runtime is not None: runtime.close()
        finally:
            mirror = getattr(self, "mirror_service", None)
            if mirror is not None: mirror.close()
            companion=getattr(self,'companion_service',None)
            if companion is not None:companion.detach()
            self.ser.close()

    def refresh_status(self, request_id, state, message):
        self.send_line(json.dumps({"cmd": "refresh_status", "requestId": request_id, "state": state, "message": message}))

    def take_refresh_request(self):
        request_id = self.refresh_request_id
        self.refresh_request_id = None
        return request_id

    def activity(self, state, message):
        if self.activity_supported:
            self.send_line(json.dumps({"cmd": "host_activity", "state": state, "message": message}))

    def handle_event(self, message):
        runtime = getattr(self, 'permission_runtime', None)
        if runtime is not None and runtime.handle_event(message):
            return True
        if message.get('type') == 'hardware':
            health = getattr(self, 'health', None)
            if not getattr(self, 'hardware_pending', False) or self.expected_board is None or not isinstance(health, HostStatus):
                return True
            try:
                from hardware_baseline import validate_hardware
                data = validate_hardware(message, self.expected_board.id)
                if self.boot_id is not None and data['bootId'] != self.boot_id:
                    return True
                health.data['hardware'] = data
                health.data['hardware_at'] = time.time()
                self.hardware_pending = False
                health.update()
            except ValueError:
                pass  # Invalid optional diagnostics never break quota/USB monitoring.
            return True
        request_id = message.get("requestId")
        if message.get("type") != "refresh_request" or type(request_id) is not int or not 0 < request_id <= 0xffffffff:
            return False
        if self.cycle_active:
            self.active_refresh_id = request_id
            self.refresh_status(request_id, "updating", "Joining the current provider update")
        else:
            self.refresh_request_id = request_id
            self.refresh_status(request_id, "waiting", "Queued; API polling cooldown is 15 s")
        return True

    def collect_requests(self):
        while self.ser.in_waiting:
            self._rx.extend(self.ser.read(min(512, self.ser.in_waiting)))
            if len(self._rx) > 16384:
                raise RuntimeError("Panel reply exceeds receive buffer")
        while b"\n" in self._rx:
            line, _, rest = self._rx.partition(b"\n")
            self._rx = bytearray(rest)
            try:
                message = json.loads(line)
            except (ValueError, UnicodeDecodeError):
                continue
            if isinstance(message, dict):
                self.handle_event(message)

    def heartbeat(self):
        fields = dict(clock_fields(), cmd="get_info", heartbeat=True, manualRefresh=True)
        self.send_line(json.dumps(fields))
        info = self.wait_for("info")
        if self.expected_board is not None and not matches_info(self.expected_board, info):
            raise RuntimeError('Connected display does not match the selected board. Open First-time setup.')
        self.info = info
        self.activity_supported = info.get("hostActivity") is True
        self.tokens_supported = info.get("tokenActivity") is True
        self.provider_selection_supported = info.get('providerSelection') is True
        self.sessions_supported = info.get('sessionActivity') is True
        boot_id, uptime = info.get("bootId"), info.get("uptime")
        if self.boot_id is not None and boot_id != self.boot_id:
            raise ConnectionResetError("Panel restarted; restoring views")
        if self.boot_id is None and self.last_uptime is not None and uptime is not None and uptime < self.last_uptime:
            raise ConnectionResetError("Panel uptime reset; restoring views")
        self.boot_id, self.last_uptime = boot_id, uptime
        status = getattr(self, 'health', None)
        if isinstance(status, HostStatus):
            source_mask=info.get('tokenSources')
            if type(source_mask) is int and 0<=source_mask<=255:
                age=info.get('tokenAgeSeconds')
                status.data['display_sources']=source_mask if info.get('tokenKnown') is True and type(age) is int and 0<=age<35 else 0
                status.data['display_sources_at']=time.time()
            history=getattr(self,'history',None)
            if history is not None:
                status.data['history']={'enabled':history.enabled,'error':history.last_error}
            if isinstance(self.token_reporter, TokenSampler):
                state=self.token_reporter.read_state()
                if state=='stalled' and status.data.get('local_reader')!='stalled':
                    LOG('Local token read exceeded 15 seconds; USB continues. Restart host if activity does not resume.')
                status.data['local_reader']=state
            status.update('connected', self.name)

    def report_tokens(self):
        message = None
        mirror = getattr(self, "mirror_service", None)
        if mirror is not None: mirror.pump(self)
        companion=getattr(self,'companion_service',None)
        if companion is not None:
            companion.pump(self)
            health=getattr(self,'health',None)
            if health is not None:health.data['companion']=companion.snapshot()
        runtime = getattr(self, 'permission_runtime', None)
        if runtime is not None: runtime.pump()
        sampler=getattr(self,'history_sampler',None)
        if sampler is not None and type(self.info.get('historyProtocol')) is int and self.info['historyProtocol'] in (1,2,3):
            summary=sampler.take()
            if summary is not None:
                from usb_history import UsbHistoryClient
                try:
                    if getattr(self,'history_client',None) is None:self.history_client=UsbHistoryClient(self)
                    self.history_client.send(summary)
                except (ValueError,TimeoutError,RuntimeError):self.history_client=None
                # Actual serial errors retain the normal reconnect path; optional history cannot block quota.
        if self.tokens_supported and isinstance(self.token_reporter, (TokenReporter, TokenSampler)):
            message = self.token_reporter.poll()
            if message is not None:
                sessions = message.get('sessions')
                self.send_line(json.dumps({key:value for key,value in message.items() if key not in ('sessions','deltas','live_agents','live_sampled_at')}))
                if sessions is not None:
                    if self.sessions_supported: self.send_line(json.dumps(sessions))
                    health = getattr(self, 'health', None)
                    if isinstance(health, HostStatus):
                        health.data['sessions'] = sessions
                        health.data['sessions_at'] = time.time()
        sampler=getattr(self,'live_sampler',None)
        # Dedicated production reader; keep compatibility with an older injected sampler.
        live_message=sampler.poll() if sampler is not None else message
        if not (isinstance(live_message,dict) and 'live_agents' in live_message):return
        supported=(type(self.info.get('liveProtocol')) is int and self.info['liveProtocol']==1
                   and self.info.get('livePermissions') is False)
        if not supported:
            self.live_health('unsupported',0);return
        if time.monotonic()<getattr(self,'live_retry_at',0):return
        from usb_live import UsbLiveClient
        try:
            if getattr(self,'live_client',None) is None:
                self.live_client=UsbLiveClient(self);self.live_client.open()
            sampled=live_message.get('live_sampled_at')
            fresh_sample=type(sampled) in (int,float) and 0<=time.monotonic()-sampled<=10
            agents=live_message['live_agents'] if fresh_sample else []
            summary=self.live_summary(live_message,len(agents)) if fresh_sample else None
            if summary is None:self.live_client.send(agents)
            else:self.live_client.send(agents,summary)
            self.live_health('acknowledged' if fresh_sample else 'stale',len(agents))
        except (ValueError,TimeoutError,RuntimeError):
            # Optional telemetry failure is visible but never takes down quota monitoring.
            self.live_client=None;self.live_retry_at=time.monotonic()+30
            self.live_health('error',0)
        # Serial I/O errors still propagate to the existing reconnect path.

    @staticmethod
    def live_summary(message,count):
        """Sessions beyond the eight listed and which AIs have observers; None when the sample has neither."""
        total,observers=message.get('live_total'),message.get('live_observers')
        if type(total) is not int or not isinstance(observers,(tuple,list)) or len(observers)!=2:return None
        return {'total':max(total,count),'selected':observers[0],'linked':observers[1]}

    def live_health(self,state,count):
        health=getattr(self,'health',None)
        if isinstance(health,HostStatus):
            health.data['live']={'state':state,'agent_count':count,'updated_at':time.time()}
            health.update()

    def _write(self, data):
        if self.ser.write(data) != len(data):
            raise serial.SerialTimeoutException("Incomplete serial write")

    def send_line(self, line):
        self._write(line.encode("utf-8") + b"\n")

    def send_frame(self, payload, frame_id):
        raw = payload.encode("utf-8")
        if not 0 < len(raw) <= MAX_FRAME_BYTES:
            raise ValueError(f"Frame must contain 1..{MAX_FRAME_BYTES} bytes")
        self._write(b"AIM1 %d %d\n" % (len(raw), frame_id) + raw + b"\n")

    def wait_for(self, message_type, seconds=2.0, frame_id=None, command=None):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            while b"\n" in self._rx:
                line, _, rest = self._rx.partition(b"\n")
                self._rx = bytearray(rest)
                try:
                    message = json.loads(line)
                except (ValueError, UnicodeDecodeError):
                    continue  # boot messages and debug logs
                if not isinstance(message, dict):
                    continue
                # A development collector explicitly waits for hardware. Only
                # unsolicited diagnostics belong to the asynchronous host path.
                if not (message_type == 'hardware' and message.get('type') == 'hardware') and self.handle_event(message):
                    continue
                if frame_id is not None and message.get("frameId") != frame_id:
                    continue
                if message.get("type") == "error":
                    if frame_id is None and "frameId" in message:
                        continue
                    raise RuntimeError("Panel rejected request")
                if command is not None and message.get("cmd") != command:
                    continue
                if message.get("type") == message_type:
                    return message
            available = getattr(self.ser, "in_waiting", 0)
            # Blocking read(512) waits for the full count even when a short JSON
            # reply is already complete. Wait for one byte, then drain available bytes.
            count = min(512, available) if type(available) is int and available > 0 else 1
            chunk = self.ser.read(count)
            if chunk:
                self._rx.extend(chunk)
                if len(self._rx) > 16384:
                    raise RuntimeError("Panel reply exceeds receive buffer")
        raise TimeoutError(f"{self.name}: no {message_type} reply")
