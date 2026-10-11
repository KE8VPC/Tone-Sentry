"""Offline signature verification. This development build has no feature gates."""
import base64
import json
from importlib.resources import files
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


def public_keys():
    return json.loads(files('tonepage').joinpath('resources/license-public-keys.json').read_text(encoding='utf-8'))


def decode(value):
    return base64.b64decode(value+'='*((-len(value))%4), altchars=b'-_', validate=True)


def verify(key, keys=None):
    try:
        if not isinstance(key, str) or len(key) > 8192: raise ValueError()
        prefix, kid, payload, signature = key.strip().split('.')
        trusted = public_keys() if keys is None else keys
        if prefix != 'TS1' or kid not in trusted: raise ValueError()
        Ed25519PublicKey.from_public_bytes(decode(trusted[kid])).verify(decode(signature), (prefix+'.'+kid+'.'+payload).encode('ascii'))
        data = json.loads(decode(payload))
        if data.get('product') != 'Tone Sentry' or data.get('edition') != 'full' or data.get('schema') != 1:
            raise ValueError()
        if not isinstance(data.get('license_id'), str) or not data['license_id'] or not isinstance(data.get('licensed_to'), str) or not data['licensed_to'].strip():
            raise ValueError()
        # Expiry and device binding require an agreed policy, not ignored claims.
        if set(data) != {'product','edition','schema','license_id','licensed_to'}: raise ValueError()
        return data
    except (ValueError, KeyError, TypeError, AttributeError, UnicodeError, InvalidSignature):
        raise ValueError('Registration key is invalid or is not issued for this version of Tone Sentry') from None


def activate(home, key, keys=None):
    data = verify(key, keys)
    target = home/'registration.key'
    temp = target.with_suffix('.tmp')
    temp.write_text(key.strip(), encoding='utf-8')
    temp.replace(target)
    return data


def status(home, keys=None):
    path = home/'registration.key'
    if not path.is_file(): return None
    try:
        return verify(path.read_text(encoding='utf-8'), keys)
    except (ValueError, OSError):
        return None
