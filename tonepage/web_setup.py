"""Local-only web access setup and account administration."""
import copy
import tkinter as tk
import webbrowser
from .forms import Form
from .web_console import load_access, save_access, set_account, ROLES


def settings_dialog(app):
    form=Form(app,'Remote web console')
    saved=load_access(app.home)
    enabled=form.field('Enable HTTPS web console',saved['enabled'])
    bind=form.field('Listen address',saved['bind'],choices=['127.0.0.1','0.0.0.0'])
    host=form.field('Receiver IP or hostname (browser address)',saved['host'])
    port=form.field('HTTPS port',saved['port'])
    from .network_reference import AddressReference
    addresses=AddressReference(form.body)
    addresses.grid(row=form.row,column=0,columnspan=2,sticky='ew',pady=(6,0))
    form.row+=1
    form.note('For another device: select 0.0.0.0 and enter this receiver’s LAN or VPN IP address as the browser address. Use a private network or VPN. No firewall or router settings are changed automatically.')
    form.note('Current listener: '+app.web_console.status)
    if app.web_console.fingerprint:
        form.note('Certificate SHA-256 (compare in browser certificate details):\n'+app.web_console.fingerprint)
    def open_console():
        web=app.web_console
        if not web.thread or not web.thread.is_alive() or not web.status.startswith('https://'):
            raise ValueError('The web listener is not running. Save and apply web access to restart it.')
        webbrowser.open(web.status)
    form.button('Open current web console',lambda:app.safe(open_console))
    form.note('Accounts: '+(', '.join(n+' ('+v['role']+')' for n,v in saved['users'].items()) or 'None — add an administrator below'))
    name=form.field('Add / replace account username','')
    password=form.field('New password (12+ characters)','',masked=True)
    role=form.field('Account role','admin',choices=list(ROLES),readonly=True)
    remove=form.field('Remove account (optional)','',choices=['']+list(saved['users']),readonly=True)
    form.note('Viewer: status and recordings. Operator: also edit tones and control monitoring. Administrator: same browser controls; account administration remains local in this release. A saved password change or listener restart signs everyone out. Leave username/password blank to keep accounts unchanged.')
    form.note('HTTPS uses a locally generated certificate. On your other device, compare its SHA-256 fingerprint with this dialog before accepting the browser certificate warning. Keep the receiver desktop open. Stop web access by clearing Enable and saving. The radio keeps monitoring.')
    def save():
        c=copy.deepcopy(saved)
        c.update(enabled=enabled.get(),bind=bind.get().strip(),host=host.get().strip(),port=int(port.get()))
        if name.get() or password.get():
            set_account(c,name.get().strip(),password.get(),role.get())
        if remove.get():
            c['users'].pop(remove.get(),None)
        from .web_console import validate_access
        validate_access(c)
        previous=load_access(app.home)
        app.web_console.stop()
        try:
            app.web_console.start(c)
            save_access(app.home,c)
        except Exception:
            app.web_console.stop()
            try:
                app.web_console.start(previous)
            except Exception:
                app.web_console.status='Web access failed to start; review address/port in Settings'
            raise
        app.engine.store.event('web_access_changed',{'message':'Web console enabled' if c['enabled'] else 'Web console disabled'})
    form.save(save,'Save and apply web access')


def initialize(app):
    from .receiver_controller import ReceiverController
    from .web_console import WebConsole
    app.receiver_controller=ReceiverController(app,busy=lambda:any(isinstance(w,tk.Toplevel) and w.winfo_exists() for w in app.root.winfo_children()))
    app.web_console=WebConsole(app.home,app.receiver_controller,app.engine.store)
    app.web_timer=None
    def pump():
        app.receiver_controller.pump()
        app.web_timer=app.root.after(200,pump)
    pump()
    try:
        app.web_console.start(load_access(app.home))
    except Exception as exc:
        app.web_console.status='Web access unavailable; review Settings ('+type(exc).__name__+')'
        app.engine.store.event('web_access_error',{'message':app.web_console.status})
