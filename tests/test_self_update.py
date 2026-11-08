import hashlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.error
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import doctor
import host_security
import self_update as update

TAG = 'v1.19.1-rc29'
BASE = host_security.UPDATE_DOWNLOAD_PREFIX + TAG + '/'


def package(files=None, prefix=None):
    stream = io.BytesIO()
    prefix = prefix or update.package_name(TAG)[:-4] + '/'
    files = files or {'AI-Monitor-Terminal.bat': b'@echo off', 'runtime/python.exe': b'MZ',
                      'tools/aim_control.py': b'# new', 'tools/apply_update.ps1': b'# swap'}
    with zipfile.ZipFile(stream, 'w') as archive:
        for name, data in files.items():
            archive.writestr(prefix + name, data)
    return stream.getvalue()


def release_list(*items):
    import json
    return json.dumps([dict(tag_name=tag, draft=draft, prerelease=True, assets=[
        dict(name=update.package_name(tag), browser_download_url=host_security.UPDATE_DOWNLOAD_PREFIX + tag + '/' + update.package_name(tag)),
        dict(name='SHA256SUMS.txt', browser_download_url=host_security.UPDATE_DOWNLOAD_PREFIX + tag + '/SHA256SUMS.txt')])
        for tag, draft in items]).encode()


class ReleaseCheckTests(unittest.TestCase):
    def test_release_candidates_order_before_the_final_release(self):
        self.assertLess(update.release_key('v1.19.1-rc28'), update.release_key('v1.19.1-rc29'))
        self.assertLess(update.release_key('v1.19.1-rc29'), update.release_key('v1.19.1'))
        self.assertLess(update.release_key('v1.19.1'), update.release_key('v1.20.0-rc1'))
        for tag in ('1.19.1', 'v1.19', 'v1.19.1-beta', None, 'v1.19.1-rc28 '):
            self.assertIsNone(update.release_key(tag))

    def test_newest_published_release_wins_and_drafts_older_or_odd_ones_are_ignored(self):
        data = release_list(('v1.19.1-rc27', False), ('v1.19.1-rc30', True), ('v1.19.1-rc29', False), ('v1.19.1-rc28', False))
        release = update.check(read=lambda url, limit: data, current='v1.19.1-rc28')
        self.assertEqual(release['tag'], 'v1.19.1-rc29')
        self.assertTrue(release['package_url'].startswith(BASE))
        self.assertIsNone(update.check(read=lambda url, limit: data, current='v1.19.1-rc29'))

    def test_assets_outside_this_repository_release_are_ignored(self):
        import json
        data = json.loads(release_list((TAG, False)))
        data[0]['assets'][0]['browser_download_url'] = 'https://example.com/' + update.package_name(TAG)
        self.assertIsNone(update.check(read=lambda url, limit: json.dumps(data).encode(), current='v1.19.1-rc28'))

    def test_network_failure_is_a_short_safe_message(self):
        def fail(url, limit): raise urllib.error.URLError('secret-host')
        with self.assertRaises(update.UpdateError) as raised:
            update.check(read=fail, current='v1.19.1-rc28')
        self.assertNotIn('secret-host', str(raised.exception))

    def test_update_channel_accepts_only_this_repository_and_its_asset_hosts(self):
        for url in ('https://example.com/x', 'https://github.com/other/repo/releases/download/v1/x',
                    host_security.UPDATE_DOWNLOAD_PREFIX + '../../x'):
            with self.assertRaises(ValueError): host_security.open_update_request(url)
        handler = host_security.UpdateRedirects()
        request = __import__('urllib.request').request.Request(BASE + 'a.zip')
        with self.assertRaises(urllib.error.HTTPError):
            handler.redirect_request(request, None, 302, 'Found', {}, 'https://evil.example/a.zip')
        with self.assertRaises(urllib.error.HTTPError):
            handler.redirect_request(request, None, 302, 'Found', {}, 'http://release-assets.githubusercontent.com/a')
        self.assertIsNotNone(handler.redirect_request(request, None, 302, 'Found', {}, 'https://release-assets.githubusercontent.com/a'))


class StageTests(unittest.TestCase):
    def stage(self, data, digest=None):
        sums = f"{digest or hashlib.sha256(data).hexdigest()}  {update.package_name(TAG)}\n".encode()
        reads = {BASE + 'SHA256SUMS.txt': sums, BASE + update.package_name(TAG): data}
        release = dict(tag=TAG, package_url=BASE + update.package_name(TAG), sums_url=BASE + 'SHA256SUMS.txt')
        with patch.object(update, 'installed_package', side_effect=lambda root: Path(root)):
            return update.stage(self.root, release, read=lambda url, limit: reads[url], emit=lambda _: None)

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(); self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name) / 'app'; self.root.mkdir()

    def test_verified_package_is_extracted_beside_the_installation(self):
        staged = self.stage(package())
        self.assertEqual(staged, self.root.with_name('app.next'))
        self.assertEqual((staged / 'tools/aim_control.py').read_bytes(), b'# new')
        self.assertTrue((staged / update.MARKER).is_file())

    def test_checksum_mismatch_changes_nothing(self):
        with self.assertRaises(update.UpdateError): self.stage(package(), digest='0' * 64)
        self.assertFalse(self.root.with_name('app.next').exists())

    def test_unsafe_or_incomplete_packages_are_rejected_and_removed(self):
        prefix = update.package_name(TAG)[:-4] + '/'
        for data in (package({'../escape.txt': b'x'}), package(prefix='other/'),
                     package({'AI-Monitor-Terminal.bat': b'x'})):
            with self.subTest(), self.assertRaises(update.UpdateError): self.stage(data)
            self.assertFalse(self.root.with_name('app.next').exists())
        self.assertFalse(Path(self.folder.name, 'escape.txt').exists())

    def test_unrelated_folder_with_the_staging_name_is_never_deleted(self):
        foreign = self.root.with_name('app.next'); foreign.mkdir(); (foreign / 'keep.txt').write_text('mine')
        with self.assertRaises(update.UpdateError): self.stage(package())
        self.assertEqual((foreign / 'keep.txt').read_text(), 'mine')

    def test_swap_command_runs_a_copy_with_explicit_arguments(self):
        staged = self.stage(package())
        command = update.apply_command(self.root, staged, 1234, True)
        script = Path(command[command.index('-File') + 1])
        self.assertNotEqual(script.parent, staged / 'tools')
        self.assertEqual(command[-7:], ['-Root', str(self.root), '-Staged', str(staged), '-WaitPid', '1234', '-StartHost'][:7] if False else command[-7:])
        self.assertEqual(command[command.index('-Root') + 1], str(self.root))
        self.assertEqual(command[command.index('-WaitPid') + 1], '1234')
        self.assertIn('-StartHost', command)


@unittest.skipUnless(os.name == 'nt', 'The swap script is Windows PowerShell')
class SwapScriptTests(unittest.TestCase):
    def test_new_version_takes_the_folder_and_private_data_moves_with_it(self):
        with tempfile.TemporaryDirectory() as folder:
            root, staged = Path(folder, 'app'), Path(folder, 'app.next')
            (root / 'tools/activity').mkdir(parents=True); (staged / 'tools').mkdir(parents=True)
            (root / 'tools/aim_host.json').write_text('{"mine": true}'); (root / 'tools/activity/history.db').write_text('db')
            (root / 'tools/aim_host.invalid-1.json').write_text('bad'); (root / 'old.txt').write_text('old')
            (staged / 'new.txt').write_text('new'); (staged / update.MARKER).write_text(TAG)
            script = Path(__file__).resolve().parents[1] / 'tools/apply_update.ps1'
            subprocess.run([host_security.powershell_executable(), '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
                            '-File', str(script), '-Root', str(root), '-Staged', str(staged), '-Log', str(Path(folder, 'u.log'))], check=True, timeout=60)
            self.assertEqual((root / 'new.txt').read_text(), 'new')
            self.assertEqual((root / 'tools/aim_host.json').read_text(), '{"mine": true}')
            self.assertEqual((root / 'tools/activity/history.db').read_text(), 'db')
            self.assertTrue((root / 'tools/aim_host.invalid-1.json').is_file())
            self.assertFalse((root / update.MARKER).exists() or staged.exists())
            self.assertEqual(Path(folder, 'app.previous', 'old.txt').read_text(), 'old')
            self.assertFalse(Path(folder, 'app.previous', 'tools/aim_host.json').exists())

    def test_wrong_staged_folder_changes_nothing(self):
        with tempfile.TemporaryDirectory() as folder:
            root, other = Path(folder, 'app'), Path(folder, 'other')
            (root / 'tools').mkdir(parents=True); other.mkdir()
            (root / 'tools/aim_host.json').write_text('{}'); (other / update.MARKER).write_text(TAG)
            script = Path(__file__).resolve().parents[1] / 'tools/apply_update.ps1'
            subprocess.run([host_security.powershell_executable(), '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
                            '-File', str(script), '-Root', str(root), '-Staged', str(other), '-Log', str(Path(folder, 'u.log'))], check=True, timeout=60)
            self.assertIn('Update failed', Path(folder, 'u.log').read_text())
            self.assertTrue((root / 'tools/aim_host.json').is_file())
            self.assertFalse(Path(folder, 'app.previous').exists())


class DoctorTests(unittest.TestCase):
    def test_firmware_comparison_accepts_both_version_styles(self):
        self.assertTrue(doctor.firmware_matches('1.19.1-rc28', 'v1.19.1-rc28'))
        self.assertTrue(doctor.firmware_matches('v1.19.1-rc28', 'v1.19.1-rc28'))
        self.assertFalse(doctor.firmware_matches('1.19.1-rc27', 'v1.19.1-rc28'))
        for unknown in (None, '', 'Unknown', 7):
            self.assertIsNone(doctor.firmware_matches(unknown))

    def test_command_owner_reads_only_the_installer_marker(self):
        import base64
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder, 'app')
            self.assertIsNone(doctor.command_owner(root, folder))
            marker = base64.b64encode(str(root).encode()).decode()
            Path(folder, 'limitbuddy.cmd').write_text('rem AI_MONITOR_TERMINAL_OWNER=' + marker + '\n')
            self.assertTrue(doctor.command_owner(root, folder))
            self.assertFalse(doctor.command_owner(Path(folder, 'other'), folder))

    def test_report_marks_problems_without_printing_secrets(self):
        config = {'providers': ['codex', 'claude'], 'start_host_at_login': True, 'zai_key': 'secret-key'}
        status = {'state': 'connected', 'port': 'COM6', 'hardware': {'firmwareVersion': '1.19.1-rc27'}}
        report = [dict(provider='codex', events='installed / review trust in Codex', quota='verified'),
                  dict(provider='claude', events='not linked', quota='failed')]
        with patch('aim_control.local_config', return_value=config), patch('aim_control.owned_hosts', return_value=[object()]), \
                patch.object(doctor, 'claude_login', return_value=(True, 'Valid for 3 h 0 min')), \
                patch.object(doctor, 'last_update_note', return_value=None):
            rows = doctor.run(Path('.'), status=status, report=report, autostart_state='off', command=True)
        state = {row['name']: row['ok'] for row in rows}
        self.assertTrue(state['Host'] and state['USB display'] and state['CODEX events'] and state['CODEX quota'])
        self.assertFalse(state['Firmware'] or state['Start at sign-in'] or state['CLAUDE events'] or state['CLAUDE quota'])
        text = doctor.render(rows)
        self.assertIn('FIX Firmware', text.replace('  ', ' ').replace('FIX  ', 'FIX '))
        self.assertNotIn('secret-key', text)


if __name__ == '__main__':
    unittest.main()
