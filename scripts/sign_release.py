"""Sign a draft release for in-place updates on the maintainer's PC, or create the key once.

The key never reaches GitHub, so control of the repository alone cannot produce an accepted update.

Each release:   python scripts/sign_release.py vX.Y.Z --key <key file>
One-time setup: python scripts/sign_release.py <key file> --generate-key
"""
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from host_security import UPDATE_PUBLIC_KEY
import private_files
import self_update


def public_hex(key):
    return key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw).hex()


def sign(path, seed):
    try:
        key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(seed))
    except ValueError:
        raise SystemExit('The key file must hold a 32-byte hex seed.') from None
    # A signature installations would reject must not reach a release.
    if public_hex(key) != UPDATE_PUBLIC_KEY:
        raise SystemExit('This key does not match UPDATE_PUBLIC_KEY in tools/host_security.py.')
    path = Path(path)
    signature = path.with_name(path.name + '.sig')
    signature.write_bytes(key.sign(path.read_bytes()))
    return signature


def sign_published_checksums(tag, key_path):
    """Download the release's checksum list, confirm it names this tag's package, sign it and upload the signature."""
    with tempfile.TemporaryDirectory() as folder:
        subprocess.run(['gh', 'release', 'download', tag, '--pattern', self_update.SUMS, '--dir', folder], check=True)
        sums = Path(folder, self_update.SUMS)
        try:
            self_update.expected_digest(sums.read_bytes(), self_update.package_name(tag))
        except self_update.UpdateError as error:
            raise SystemExit(str(error)) from None
        signature = sign(sums, Path(key_path).read_text(encoding='ascii').strip())
        subprocess.run(['gh', 'release', 'upload', tag, str(signature), '--clobber'], check=True)


def generate_key(path):
    """Write a new private seed with current-user permissions and return only the public key."""
    path = Path(path)
    if path.exists():
        raise SystemExit('A key already exists there; nothing was changed.')
    key = Ed25519PrivateKey.generate()
    private_files.write_bytes(path, key.private_bytes_raw().hex().encode('ascii'))
    return public_hex(key)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('target', help='release tag, or the key file to create with --generate-key')
    parser.add_argument('--key', help='private key file')
    parser.add_argument('--generate-key', action='store_true', help='create a key and print its public half')
    arguments = parser.parse_args()
    if arguments.generate_key:
        print(generate_key(arguments.target))
    elif arguments.key:
        sign_published_checksums(arguments.target, arguments.key)
    else:
        parser.error('--key is required to sign a release')


if __name__ == '__main__':
    main()
