import base64
import json
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from tonepage.licensing import activate, status, verify


def signed(data=None):
    key = Ed25519PrivateKey.generate()
    encode = lambda b:base64.urlsafe_b64encode(b).decode().rstrip('=')
    data = data or dict(product='Tone Sentry',edition='full',schema=1,license_id='unit-test',licensed_to='Test receiver')
    message = 'TS1.test.'+encode(json.dumps(data).encode())
    return message+'.'+encode(key.sign(message.encode())), {'test':encode(key.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw))}


def test_offline_activation_persistence_and_no_config_export(tmp_path):
    token, public = signed()
    assert activate(tmp_path,token,public)['licensed_to']=='Test receiver'
    assert status(tmp_path,public)['license_id']=='unit-test'
    assert sorted(p.name for p in tmp_path.iterdir()) == ['registration.key']
    with pytest.raises(ValueError): activate(tmp_path, token+'tampered',public)
    assert status(tmp_path,public)['license_id']=='unit-test'


def test_forged_key_and_wrong_product_are_rejected():
    token, public = signed()
    forged, _ = signed()
    with pytest.raises(ValueError): verify(forged,public)
    wrong, keys = signed(dict(product='Other',edition='full',schema=1,license_id='x',licensed_to='x'))
    with pytest.raises(ValueError): verify(wrong,keys)
    with pytest.raises(ValueError): verify(token,{})
