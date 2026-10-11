import json
import pytest
from tonepage.ftp_credentials import encode_password, decode_password, ftp_password, export_settings


def test_password_roundtrip_and_export(monkeypatch):
    password=' spaces / and ünicode $! '
    encoded=encode_password(password)
    destination=dict(kind='ftp',password_b64=encoded,password_env='ABSENT_FTP_PASSWORD')
    monkeypatch.delenv('ABSENT_FTP_PASSWORD',raising=False)
    assert ftp_password(destination)==password
    config=dict(integrations=[destination])
    exported=export_settings(config)
    assert 'password_b64' not in exported['integrations'][0]
    assert destination['password_b64']==encoded
    assert password not in json.dumps(config)


@pytest.mark.parametrize('value',['!!!!','/w==',None,123])
def test_invalid_saved_password_has_safe_error(value):
    with pytest.raises(ValueError,match='Saved FTP password is invalid'):
        decode_password(value)


def test_missing_environment_does_not_echo_password(monkeypatch):
    from tonepage.integrations import secret, PermanentError
    monkeypatch.delenv('accidentally-entered-password',raising=False)
    with pytest.raises(PermanentError) as error:secret('accidentally-entered-password')
    assert 'accidentally-entered-password' not in str(error.value)
