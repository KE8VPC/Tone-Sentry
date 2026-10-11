"""Read-only address references; internet lookup is explicitly requested by the user."""
import ipaddress
import queue
import socket
import threading
import tkinter as tk
from tkinter import ttk


def local_addresses():
    import psutil
    states=psutil.net_if_stats()
    rows=[]
    for name,addresses in sorted(psutil.net_if_addrs().items()):
        for address in addresses:
            if address.family != socket.AF_INET:
                continue
            ip=ipaddress.IPv4Address(address.address)
            if ip.is_loopback or ip.is_unspecified:
                continue
            state=states.get(name)
            label='connected' if state and state.isup else 'disconnected / unknown'
            if ip.is_link_local:
                label+='; link-local'
            rows.append(f'{name}: {ip} ({label})')
    return '\n'.join(rows) or 'No non-loopback IPv4 address found. Check the network connection.'


def public_address():
    import requests
    # Do not pick up netrc credentials or environment proxy authentication.
    with requests.Session() as session:
        session.trust_env=False
        with session.get('https://api.ipify.org',timeout=(3,5),stream=True,allow_redirects=False) as response:
            if response.status_code != 200:
                raise ValueError('Public address service unavailable')
            chunks=[];size=0
            for chunk in response.iter_content(128):
                size+=len(chunk)
                if size>128:
                    raise ValueError('Unexpected public address response')
                chunks.append(chunk)
            ip=ipaddress.ip_address(b''.join(chunks).decode('ascii').strip())
            if not ip.is_global:
                raise ValueError('Invalid public internet address')
            return str(ip)


class AddressReference(ttk.Frame):
    def __init__(self,parent):
        super().__init__(parent)
        self.results=queue.Queue(maxsize=2)
        self.busy=set()
        self.closed=False
        self.timer=None
        self.local=tk.StringVar(master=self,value='Reading local network addresses…')
        self.public=tk.StringVar(master=self,value='Public internet IP: not looked up')
        ttk.Label(self,text='Network addresses — reference only').pack(anchor='w')
        self.local_label=ttk.Label(self,textvariable=self.local,wraplength=680)
        self.local_label.pack(anchor='w',fill='x',pady=(4,0))
        self.public_label=ttk.Label(self,textvariable=self.public,wraplength=680)
        self.public_label.pack(anchor='w',fill='x',pady=4)
        row=ttk.Frame(self);row.pack(anchor='w')
        self.local_button=ttk.Button(row,text='Refresh local IPs',command=lambda:self.start('local'))
        self.local_button.pack(side='left',padx=(0,8))
        self.public_button=ttk.Button(row,text='Look up public IP',command=lambda:self.start('public'))
        self.public_button.pack(side='left')
        self.note=ttk.Label(self,text='Public lookup contacts api.ipify.org only when clicked. A VPN may change the result. This does not configure internet access or change the listen address.',wraplength=680)
        self.note.pack(anchor='w',fill='x',pady=(4,8))
        self.bind('<Configure>',self.resize)
        self.bind('<Destroy>',self.destroyed)
        self.poll()
        self.start('local')

    def resize(self,event):
        for label in (self.local_label,self.public_label,self.note):
            label.configure(wraplength=max(160,event.width-8))

    def start(self,kind):
        if self.closed or kind in self.busy:
            return
        self.busy.add(kind)
        button=self.local_button if kind=='local' else self.public_button
        button.configure(state='disabled')
        variable=self.local if kind=='local' else self.public
        variable.set('Reading local addresses…' if kind=='local' else 'Public internet IP: looking up…')
        def work():
            try:
                text=local_addresses() if kind=='local' else 'Public internet IP: '+public_address()
            except Exception:
                text='Local IP addresses unavailable.' if kind=='local' else 'Public internet IP: unavailable / offline. You can try again.'
            self.results.put((kind,text))
        threading.Thread(target=work,name='web-ip-reference',daemon=True).start()

    def poll(self):
        if self.closed:
            return
        while True:
            try:kind,text=self.results.get_nowait()
            except queue.Empty:break
            self.busy.discard(kind)
            (self.local if kind=='local' else self.public).set(text)
            (self.local_button if kind=='local' else self.public_button).configure(state='normal')
        self.timer=self.after(100,self.poll)

    def destroyed(self,event):
        if event.widget is self:
            self.closed=True
            if self.timer is not None:
                self.after_cancel(self.timer)
