"""Check, verify and stage a published release, then replace this installation in place.

The installation keeps its folder, so provider hooks, the Start at sign-in entry and the
limitbuddy command stay valid (Codex does not ask to trust them again). Private settings,
history and companion packs move into the new version after NOVA closes; nothing is copied
out of the folder. The previous version stays beside it as <folder>.previous.
"""
import hashlib
import http.client
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

from host_security import UPDATE_DOWNLOAD_PREFIX, UPDATE_PUBLIC_KEY, UPDATE_RELEASES_URL, open_update_request, powershell_executable
from project_version import HOST_VERSION

MAX_LIST_BYTES = 1024 * 1024
MAX_SUMS_BYTES = 64 * 1024
MAX_PACKAGE_BYTES = 200 * 1024 * 1024
MAX_EXTRACTED_BYTES = 800 * 1024 * 1024
MAX_MEMBERS = 20000
MARKER = '.limitbuddy-staged'
SUMS = 'SHA256SUMS.txt'
SIGNATURE = SUMS + '.sig'
SIGNATURE_BYTES = 64
FINAL_RELEASE = 1 << 30
# Local-only data that belongs to this installation (see .gitignore); moved, never copied.
PRIVATE_ITEMS = ('.env', 'tools/aim_host.json', 'tools/aim_host.status.json', 'tools/aim_host.log',
                 'tools/aim_host.log.1', 'tools/activity', 'tools/companions', 'tools/permission-endpoint.json')
PRIVATE_PATTERNS = ('tools/aim_host.invalid-*.json', 'tools/permission-trust*')


class UpdateError(Exception):
    """A safe, user-facing reason; never contains paths, URLs or secrets."""


def release_key(tag):
    """Order vX.Y.Z-rcN before vX.Y.Z; anything else is not a LimitBuddy release."""
    match = re.fullmatch(r'v(\d{1,5})\.(\d{1,5})\.(\d{1,5})(?:-rc(\d{1,5}))?', tag) if isinstance(tag, str) else None
    if not match:
        return None
    major, minor, patch, candidate = match.groups()
    return int(major), int(minor), int(patch), int(candidate) if candidate else FINAL_RELEASE


def package_name(tag):
    return f'nova-{tag}-windows-x64-terminal.zip'


def read_limited(url, limit):
    with open_update_request(url) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise UpdateError('The release file is larger than expected.')
    return data


def check(read=read_limited, current=HOST_VERSION):
    """Newest signed release newer than this one, or None. Only a release candidate is offered candidates."""
    try:
        releases = json.loads(read(UPDATE_RELEASES_URL, MAX_LIST_BYTES))
    except (OSError, ValueError, http.client.HTTPException) as error:
        raise UpdateError('GitHub could not be reached. Check the connection and retry.') from error
    if not isinstance(releases, list):
        raise UpdateError('GitHub returned an unexpected release list.')
    newest, newest_key = None, release_key(current)
    if newest_key is None:
        raise UpdateError('This installation has no comparable version.')
    stable_channel = newest_key[3] == FINAL_RELEASE
    for release in releases[:20]:
        if not isinstance(release, dict) or release.get('draft') is not False:
            continue
        tag = release.get('tag_name')
        key = release_key(tag)
        if key is None or key <= newest_key:
            continue
        if stable_channel and (key[3] != FINAL_RELEASE or release.get('prerelease') is not False):
            continue
        assets = {asset.get('name'): asset for asset in release.get('assets', [])[:64] if isinstance(asset, dict)}
        package, sums, signature = assets.get(package_name(tag)), assets.get(SUMS), assets.get(SIGNATURE)
        if not package or not sums or not signature:
            continue
        urls = (package.get('browser_download_url'), sums.get('browser_download_url'), signature.get('browser_download_url'))
        if not all(isinstance(url, str) and url.startswith(UPDATE_DOWNLOAD_PREFIX + tag + '/') for url in urls):
            continue
        newest, newest_key = dict(tag=tag, package_url=urls[0], sums_url=urls[1], signature_url=urls[2],
                                  prerelease=release.get('prerelease') is True), key
    return newest


def verify_signature(sums, signature):
    """The checksum list names the tagged package, so a valid signature binds it to this release."""
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    try:
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(UPDATE_PUBLIC_KEY)).verify(signature, sums)
    except (InvalidSignature, ValueError) as error:
        raise UpdateError('The release signature is not valid; nothing was changed.') from error


def expected_digest(sums, name):
    for line in sums.decode('utf-8', 'replace').splitlines():
        parts = line.strip().split()
        if len(parts) == 2 and parts[1].lstrip('*') == name and re.fullmatch(r'[0-9a-f]{64}', parts[0]):
            return parts[0]
    raise UpdateError('The release checksum list does not cover the package.')


def extract(package, tag, target):
    """Extract only regular files under the package folder; reject links and escaping names."""
    prefix = package_name(tag)[:-4] + '/'
    total = 0
    with zipfile.ZipFile(io.BytesIO(package)) as archive:
        members = archive.infolist()
        if len(members) > MAX_MEMBERS:
            raise UpdateError('The package has too many files.')
        for info in members:
            name = info.filename
            if not name.startswith(prefix) or '\\' in name or ':' in name:
                raise UpdateError('The package layout is not a LimitBuddy release.')
            relative = PurePosixPath(name[len(prefix):])
            if relative.is_absolute() or '..' in relative.parts or (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise UpdateError('The package contains an unsafe entry.')
            total += info.file_size
            if total > MAX_EXTRACTED_BYTES:
                raise UpdateError('The package is larger than expected.')
            if not relative.parts:
                continue
            destination = target.joinpath(*relative.parts)
            if info.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as source, destination.open('wb') as output:
                shutil.copyfileobj(source, output)


def installed_package(root):
    """Only the portable Windows package (its own runtime) can replace itself."""
    root = Path(root).resolve()
    if os.name != 'nt' or not (root / 'runtime/python.exe').is_file() or not (root / 'AI-Monitor-Terminal.bat').is_file():
        raise UpdateError('In-place update is available for the Windows package. Use Git for a source checkout.')
    return root


def stage(root, release, read=read_limited, emit=print):
    """Download, verify and extract beside the installation as <folder>.next."""
    root = installed_package(root)
    staged = root.with_name(root.name + '.next')
    if staged.exists():
        if not (staged / MARKER).is_file():
            raise UpdateError('A folder named like the update already exists; nothing was changed.')
        # A rollback that failed leaves the only copy of the settings here.
        if any((staged / item).exists() for item in PRIVATE_ITEMS) or any(any(staged.glob(pattern)) for pattern in PRIVATE_PATTERNS):
            raise UpdateError('A failed update left private data beside this folder; nothing was changed.')
        shutil.rmtree(staged)
    emit('Downloading ' + release['tag'] + '...')
    try:
        sums = read(release['sums_url'], MAX_SUMS_BYTES)
        signature = read(release['signature_url'], SIGNATURE_BYTES)
    except (OSError, http.client.HTTPException) as error:
        raise UpdateError('The download failed. Check the connection and retry.') from error
    verify_signature(sums, signature)
    try:
        package = read(release['package_url'], MAX_PACKAGE_BYTES)
    except (OSError, http.client.HTTPException) as error:
        raise UpdateError('The download failed. Check the connection and retry.') from error
    if hashlib.sha256(package).hexdigest() != expected_digest(sums, package_name(release['tag'])):
        raise UpdateError('The download does not match its published checksum; nothing was changed.')
    emit('Checksum verified. Extracting...')
    staged.mkdir()
    try:
        extract(package, release['tag'], staged)
        for required in ('AI-Monitor-Terminal.bat', 'runtime/python.exe', 'tools/aim_control.py', 'tools/apply_update.ps1'):
            if not (staged / required).is_file():
                raise UpdateError('The package is incomplete; nothing was changed.')
        (staged / MARKER).write_text(release['tag'] + '\n', encoding='ascii')
    except BaseException:
        shutil.rmtree(staged, ignore_errors=True)
        raise
    return staged


def apply_command(root, staged, wait_pid, start_host):
    script = Path(tempfile.mkdtemp(prefix='limitbuddy-update-')) / 'apply_update.ps1'
    shutil.copyfile(staged / 'tools/apply_update.ps1', script)
    command = [powershell_executable(), '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', str(script),
               '-Root', str(root), '-Staged', str(staged), '-WaitPid', str(int(wait_pid))]
    return command + (['-StartHost'] if start_host else [])


def finish(root, staged, wait_pid=None, emit=print):
    """Stop this installation's host and hand the swap to a detached PowerShell process."""
    from aim_control import owned_hosts
    from installation_lifecycle import prepare
    root = installed_package(root)
    if not (Path(staged) / MARKER).is_file():
        raise UpdateError('The staged update is missing. Check for updates again.')
    was_running = bool(owned_hosts(root))
    prepare(root)
    flags = getattr(subprocess, 'DETACHED_PROCESS', 0) | getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0) | getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    subprocess.Popen(apply_command(root, Path(staged), wait_pid or os.getpid(), was_running), cwd=root.parent,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=flags, close_fds=True)
    emit('Update ready. NOVA closes now; the new version replaces this folder' +
         (' and starts the host again.' if was_running else '.'))


def main(argv=None):
    """Command-line check used by `limitbuddy --check-update`."""
    try:
        release = check()
    except UpdateError as error:
        print(error); return 1
    print('LimitBuddy is up to date (' + HOST_VERSION + ').' if release is None else
          release['tag'] + ' is available. Open NOVA > Settings > Install update.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
