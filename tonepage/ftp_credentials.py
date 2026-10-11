"""Portable FTP password encoding. Base64 provides no encryption."""
import base64
import binascii
import copy


def encode_password(password):
    if any(c in password for c in '\r\n\0'):
        raise ValueError('FTP password cannot contain line breaks or null characters')
    return base64.b64encode(password.encode('utf-8')).decode('ascii')


def decode_password(value):
    try:
        password = base64.b64decode(value, validate=True).decode('utf-8')
        encode_password(password)
        return password
    except (ValueError, TypeError, UnicodeError, binascii.Error):
        raise ValueError('Saved FTP password is invalid; enter it again in destination settings') from None


def ftp_password(destination):
    from .integrations import secret
    if 'password_b64' in destination:
        return decode_password(destination['password_b64'])
    return secret(destination.get('password_env'))


def export_settings(config):
    result = copy.deepcopy(config)
    for destination in result.get('integrations', []):
        destination.pop('password_b64', None)
    return result
