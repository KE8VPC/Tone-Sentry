import socket
import threading
import time
from types import SimpleNamespace

import pytest

from tonepage import network_reference as network


def test_local_addresses_are_labeled_and_do_not_lookup_internet(monkeypatch):
    import psutil
    addr=lambda ip:SimpleNamespace(family=socket.AF_INET,address=ip)
    monkeypatch.setattr(psutil,'net_if_addrs',lambda:{'Ethernet':[addr('192.168.12.165')],
        'Loopback':[addr('127.0.0.1')], 'VPN':[addr('10.1.2.3')], 'Wi-Fi':[addr('169.254.1.2')]})
    monkeypatch.setattr(psutil,'net_if_stats',lambda:{'Ethernet':SimpleNamespace(isup=True),'VPN':SimpleNamespace(isup=True)})
    result=network.local_addresses()
    assert 'Ethernet: 192.168.12.165 (connected)' in result
    assert 'VPN: 10.1.2.3' in result and 'link-local' in result
    assert '127.0.0.1' not in result
    monkeypatch.setattr(psutil,'net_if_addrs',lambda:{})
    assert 'No non-loopback' in network.local_addresses()


@pytest.mark.parametrize('body,valid',[(b'8.8.8.8\n',True),(b'192.168.1.1',False),(b'<html>error</html>',False),(b'x'*129,False)])
def test_public_lookup_is_bounded_validated_and_without_ambient_credentials(monkeypatch,body,valid):
    import requests
    class Response:
        status_code=200
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def iter_content(self,size):yield body
    class Session:
        trust_env=True
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def get(self,url,**kw):
            assert not self.trust_env
            assert url=='https://api.ipify.org' and kw['timeout']==(3,5)
            assert kw['stream'] and not kw['allow_redirects']
            return Response()
    monkeypatch.setattr(requests,'Session',Session)
    if valid:assert network.public_address()=='8.8.8.8'
    else:
        with pytest.raises(ValueError):network.public_address()


def test_dialog_lookup_is_opt_in_nonblocking_and_safe_after_close(monkeypatch):
    import tkinter as tk
    monkeypatch.setattr(network,'local_addresses',lambda:'Ethernet: sample')
    entered=threading.Event();release=threading.Event();calls=[]
    def public():
        calls.append(1);entered.set();release.wait(2);return '8.8.8.8'
    monkeypatch.setattr(network,'public_address',public)
    root=tk.Tk();root.withdraw()
    frame=network.AddressReference(root)
    try:
        assert not calls
        frame.start('public');assert entered.wait(1)
        frame.start('public');assert len(calls)==1
        root.update()
        assert 'looking up' in frame.public.get()
        frame.destroy()
        release.set()
        root.update()
        assert frame.closed
    finally:
        release.set();root.destroy()
