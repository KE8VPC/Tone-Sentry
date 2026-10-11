"""Publisher-only utility. Never distribute private keys or this utility to customers."""
import argparse
import base64
import getpass
import json
import uuid
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def encode(value):
    return base64.urlsafe_b64encode(value).decode('ascii').rstrip('=')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    init = sub.add_parser('init')
    init.add_argument('--private-key', type=Path, required=True)
    init.add_argument('--public-keys', type=Path, required=True)
    init.add_argument('--key-id', required=True)
    issue = sub.add_parser('issue')
    issue.add_argument('--private-key', type=Path, required=True)
    issue.add_argument('--key-id', required=True)
    issue.add_argument('--licensed-to', required=True)
    issue.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not args.key_id.isalnum(): parser.error('Key ID must contain letters and digits only')
    password = getpass.getpass('Publisher private-key passphrase: ').encode('utf-8')
    if args.command == 'init':
        if len(password) < 16: parser.error('Use a private-key passphrase of at least 16 characters')
        if password != getpass.getpass('Confirm passphrase: ').encode('utf-8'): parser.error('Passphrases differ')
        existing = json.loads(args.public_keys.read_text(encoding='utf-8')) if args.public_keys.exists() else {}
        if args.key_id in existing: parser.error('Key ID already exists; original public key preserved')
        key = Ed25519PrivateKey.generate()
        # Exclusive writes refuse to replace an existing signing identity.
        with args.private_key.open('xb') as out:
            out.write(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.BestAvailableEncryption(password)))
        public = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        existing[args.key_id] = encode(public)
        args.public_keys.write_text(json.dumps(existing, indent=2), encoding='utf-8')
    else:
        if not args.licensed_to.strip(): parser.error('Licensed-to name is required')
        key = serialization.load_pem_private_key(args.private_key.read_bytes(), password=password)
        if not isinstance(key, Ed25519PrivateKey): parser.error('Expected an Ed25519 private key')
        data = dict(product='Tone Sentry', edition='full', schema=1, license_id=str(uuid.uuid4()), licensed_to=args.licensed_to.strip())
        unsigned = 'TS1.'+args.key_id+'.'+encode(json.dumps(data, separators=(',',':'), sort_keys=True).encode('utf-8'))
        with args.output.open('x', encoding='utf-8') as out:
            out.write(unsigned+'.'+encode(key.sign(unsigned.encode('ascii'))))
    print('Saved. Keep the encrypted private key and its passphrase outside release bundles.')


if __name__ == '__main__': main()
