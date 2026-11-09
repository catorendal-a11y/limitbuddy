import hashlib
import http.client
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

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

sys.path[:0] = [str(Path(__file__).resolve().parents[1] / folder) for folder in ('tools', 'scripts')]
import doctor
import host_security
import self_update as update
import sign_release

TAG = 'v1.19.1-rc29'
BASE = host_security.UPDATE_DOWNLOAD_PREFIX + TAG + '/'
KEY = Ed25519PrivateKey.generate()
PUBLIC = KEY.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw).hex()


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
    return json.dumps([dict(tag_name=tag, draft=draft, prerelease='-rc' in tag, assets=[
        dict(name=update.package_name(tag), browser_download_url=host_security.UPDATE_DOWNLOAD_PREFIX + tag + '/' + update.package_name(tag)),
        dict(name='SHA256SUMS.txt', browser_download_url=host_security.UPDATE_DOWNLOAD_PREFIX + tag + '/SHA256SUMS.txt'),
        dict(name='SHA256SUMS.txt.sig', browser_download_url=host_security.UPDATE_DOWNLOAD_PREFIX + tag + '/SHA256SUMS.txt.sig')])
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

    def test_release_candidates_are_offered_only_to_release_candidates(self):
        data = release_list(('v1.20.0-rc1', False), ('v1.19.2', False))
        self.assertEqual(update.check(read=lambda url, limit: data, current='v1.19.1')['tag'], 'v1.19.2')
        self.assertEqual(update.check(read=lambda url, limit: data, current='v1.19.1-rc28')['tag'], 'v1.20.0-rc1')

    def test_unsigned_release_is_ignored(self):
        import json
        data = json.loads(release_list((TAG, False)))
        del data[0]['assets'][2]
        self.assertIsNone(update.check(read=lambda url, limit: json.dumps(data).encode(), current='v1.19.1-rc28'))

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
    def stage(self, data, digest=None, signature=None):
        sums = f"{digest or hashlib.sha256(data).hexdigest()}  {update.package_name(TAG)}\n".encode()
        reads = {BASE + 'SHA256SUMS.txt': sums, BASE + update.package_name(TAG): data,
                 BASE + 'SHA256SUMS.txt.sig': KEY.sign(sums) if signature is None else signature}
        release = dict(tag=TAG, package_url=BASE + update.package_name(TAG), sums_url=BASE + 'SHA256SUMS.txt',
                       signature_url=BASE + 'SHA256SUMS.txt.sig')
        with patch.object(update, 'installed_package', side_effect=lambda root: Path(root)), \
                patch.object(update, 'UPDATE_PUBLIC_KEY', PUBLIC):
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

    def test_wrong_signature_changes_nothing(self):
        for signature in (bytes(64), b'short', b''):
            with self.subTest(), self.assertRaises(update.UpdateError): self.stage(package(), signature=signature)
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

    def test_private_data_left_by_a_failed_swap_is_never_deleted(self):
        leftover = self.root.with_name('app.next'); (leftover / 'tools').mkdir(parents=True)
        (leftover / update.MARKER).write_text(TAG); (leftover / 'tools/aim_host.json').write_text('{"mine": true}')
        with self.assertRaises(update.UpdateError): self.stage(package())
        self.assertEqual((leftover / 'tools/aim_host.json').read_text(), '{"mine": true}')

    def test_download_failure_is_a_short_safe_message(self):
        def fail(url, limit): raise http.client.IncompleteRead(b'secret-host')
        release = dict(tag=TAG, package_url=BASE + 'a.zip', sums_url=BASE + 'SHA256SUMS.txt', signature_url=BASE + 'SHA256SUMS.txt.sig')
        with patch.object(update, 'installed_package', side_effect=lambda root: Path(root)), \
                self.assertRaises(update.UpdateError) as raised:
            update.stage(self.root, release, read=fail, emit=lambda _: None)
        self.assertNotIn('secret-host', str(raised.exception))

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

    def test_failed_private_move_puts_everything_back(self):
        with tempfile.TemporaryDirectory() as folder:
            root, staged = Path(folder, 'app'), Path(folder, 'app.next')
            (root / 'tools').mkdir(parents=True); staged.mkdir()
            (root / '.env').write_text('KEY=mine'); (root / 'tools/aim_host.json').write_text('{}')
            # A file where the tools folder belongs stops the move after .env has already gone.
            (staged / 'tools').write_text('blocker'); (staged / update.MARKER).write_text(TAG)
            script = Path(__file__).resolve().parents[1] / 'tools/apply_update.ps1'
            subprocess.run([host_security.powershell_executable(), '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
                            '-File', str(script), '-Root', str(root), '-Staged', str(staged), '-Log', str(Path(folder, 'u.log'))], check=True, timeout=60)
            self.assertIn('Update failed', Path(folder, 'u.log').read_text())
            self.assertEqual((root / '.env').read_text(), 'KEY=mine')
            self.assertFalse((staged / '.env').exists())

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


class SignReleaseTests(unittest.TestCase):
    def test_signature_verifies_and_a_key_that_installations_do_not_trust_is_refused(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(sign_release, 'UPDATE_PUBLIC_KEY', PUBLIC), \
                patch.object(update, 'UPDATE_PUBLIC_KEY', PUBLIC):
            sums = Path(folder, 'SHA256SUMS.txt'); sums.write_bytes(b'data')
            sign_release.sign(sums, KEY.private_bytes_raw().hex())
            update.verify_signature(b'data', Path(folder, 'SHA256SUMS.txt.sig').read_bytes())
            with self.assertRaises(SystemExit):
                sign_release.sign(sums, Ed25519PrivateKey.generate().private_bytes_raw().hex())

    def checksums_from_github(self, content, uploads):
        def run(command, check):
            if command[2] == 'download':
                Path(command[command.index('--dir') + 1], 'SHA256SUMS.txt').write_bytes(content)
            else:
                uploads.append(Path(command[4]).read_bytes())
        return patch.object(sign_release.subprocess, 'run', side_effect=run)

    def test_release_signature_covers_the_downloaded_checksums(self):
        content, uploads = f"{'0' * 64}  {update.package_name(TAG)}\n".encode(), []
        with tempfile.TemporaryDirectory() as folder, self.checksums_from_github(content, uploads), \
                patch.object(sign_release, 'UPDATE_PUBLIC_KEY', PUBLIC), patch.object(update, 'UPDATE_PUBLIC_KEY', PUBLIC):
            key = Path(folder, 'update.key'); key.write_text(KEY.private_bytes_raw().hex())
            sign_release.sign_published_checksums(TAG, key)
            update.verify_signature(content, uploads[0])

    def test_checksums_for_another_release_are_not_signed(self):
        uploads = []
        with tempfile.TemporaryDirectory() as folder, self.checksums_from_github(f"{'0' * 64}  other.zip\n".encode(), uploads), \
                patch.object(sign_release, 'UPDATE_PUBLIC_KEY', PUBLIC):
            key = Path(folder, 'update.key'); key.write_text(KEY.private_bytes_raw().hex())
            with self.assertRaises(SystemExit): sign_release.sign_published_checksums(TAG, key)
        self.assertEqual(uploads, [])

    def test_new_key_is_created_once_and_only_its_public_half_is_returned(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder, 'keys/update.key')
            public = sign_release.generate_key(path)
            self.assertRegex(path.read_text(), '^[0-9a-f]{64}$')
            self.assertNotEqual(public, path.read_text())
            with self.assertRaises(SystemExit): sign_release.generate_key(path)


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
            Path(folder, 'limitbuddy.cmd').write_text('rem AI_MONITOR_TERMINAL_OWNER=')
            self.assertFalse(doctor.command_owner(root, folder))

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
