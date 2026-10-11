"""Optional authenticated HTTPS console. No audio capture or Tk calls in HTTP workers."""
import copy
import ipaddress
import json
import os
import re
import secrets
import ssl
import sys
import threading
import time
from datetime import datetime, timedelta, timezone
from importlib.resources import files
from pathlib import Path

from flask import Flask, abort, g, jsonify, request, Response, send_file
from werkzeug.security import check_password_hash, generate_password_hash

from .storage_paths import managed_audio

DEFAULTS = dict(enabled=False, bind='127.0.0.1', port=8767, host='localhost', users={})
ROLES = ('viewer', 'operator', 'admin')


def load_access(home):
    path = Path(home)/'web-access.json'
    return dict(DEFAULTS, **json.loads(path.read_text('utf-8'))) if path.exists() else copy.deepcopy(DEFAULTS)


def save_access(home, config):
    validate_access(config)
    path = Path(home)/'web-access.json'
    temporary = path.with_suffix('.tmp')
    with temporary.open('w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    temporary.replace(path)


def validate_access(c):
    ipaddress.IPv4Address(c['bind'])
    if type(c['port']) is not int or not 1024 <= c['port'] <= 65535:
        raise ValueError('Web port must be 1024–65535')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.-]{0,252}', c['host']):
        raise ValueError('Enter only the receiver IP address or DNS hostname, without https://, a port or a path')
    if type(c['enabled']) is not bool:
        raise ValueError('Enabled must be a checkbox value')
    if c['enabled'] and not any(u['role'] == 'admin' for u in c['users'].values()):
        raise ValueError('Create an administrator account before enabling web access')


def set_account(c, name, password, role):
    if not re.fullmatch(r'[A-Za-z0-9_.-]{1,40}', name):
        raise ValueError('Username must be 1–40 letters, digits, dots, underscores or dashes')
    if role not in ROLES or not 12 <= len(password) <= 256:
        raise ValueError('Choose a role and a password of 12–256 characters')
    if name not in c['users'] and len(c['users']) >= 20:
        raise ValueError('This console supports up to 20 accounts')
    c['users'][name] = dict(role=role, hash=generate_password_hash(password, method='scrypt'))


def certificate(home, host):
    """Locally generated certificate; its SHA-256 is shown in desktop setup."""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    directory = Path(home)/'web-tls'
    directory.mkdir(exist_ok=True)
    cert, key, name = directory/'certificate.pem', directory/'private-key.pem', directory/'host.txt'
    if not (cert.exists() and key.exists() and name.exists() and name.read_text() == host):
        private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = x509.Name([x509.NameAttribute(x509.NameOID.COMMON_NAME, host)])
        alternatives = [x509.DNSName('localhost'), x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]
        try:
            alternatives.append(x509.IPAddress(ipaddress.ip_address(host)))
        except ValueError:
            alternatives.append(x509.DNSName(host))
        now = datetime.now(timezone.utc)
        value = (x509.CertificateBuilder().subject_name(subject).issuer_name(subject)
            .public_key(private.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now-timedelta(minutes=5)).not_valid_after(now+timedelta(days=365))
            .add_extension(x509.SubjectAlternativeName(alternatives), critical=False)
            .sign(private, hashes.SHA256()))
        key.write_bytes(private.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                              serialization.NoEncryption()))
        try:
            key.chmod(0o600)
        except OSError:
            pass
        cert.write_bytes(value.public_bytes(serialization.Encoding.PEM))
        name.write_text(host)
    value = x509.load_pem_x509_certificate(cert.read_bytes())
    if value.not_valid_after_utc <= datetime.now(timezone.utc):
        raise ValueError('Web certificate expired. Remove web-tls/host.txt while web access is stopped, then restart it to renew.')
    return cert, key, value.fingerprint(hashes.SHA256()).hex().upper()


class Access:
    def __init__(self, settings):
        self.settings = copy.deepcopy(settings)
        self.lock = threading.RLock()
        self.sessions = {}
        self.attempts = {}
        self.dummy = generate_password_hash(secrets.token_urlsafe(24), method='scrypt')

    def login(self, name, password, address):
        now = time.monotonic()
        with self.lock:
            self.attempts = {k:v for k,v in self.attempts.items() if now-v[0] < 300}
            start, count = self.attempts.get(address, (now, 0))
            if count >= 10 or len(self.attempts) >= 512 and address not in self.attempts:
                abort(429, description='Too many login attempts. Wait five minutes.')
            self.attempts[address] = (start, count+1)
        user = self.settings['users'].get(name)
        valid = check_password_hash(user['hash'] if user else self.dummy, password)
        if not user or not valid:
            abort(401, description='Username or password is incorrect')
        with self.lock:
            self.sessions = {k:v for k,v in self.sessions.items() if now-v['seen'] < 1800 and now-v['created'] < 43200}
            if len(self.sessions) >= 64:
                abort(429, description='Too many sessions. Sign out elsewhere or wait for expiry.')
            token = secrets.token_urlsafe(32)
            self.sessions[token] = dict(name=name, role=user['role'], csrf=secrets.token_urlsafe(32), seen=now, created=now)
        return token

    def session(self, token):
        with self.lock:
            value = self.sessions.get(token)
            now = time.monotonic()
            if value and now-value['seen'] < 1800 and now-value['created'] < 43200:
                value['seen'] = now
                return dict(value)
            self.sessions.pop(token, None)
        return None


def create_app(controller, store, settings):
    app = Flask(__name__, static_folder=None)
    app.config.update(MAX_CONTENT_LENGTH=32768, PROPAGATE_EXCEPTIONS=False)
    access = Access(settings)
    app.extensions['tone_access'] = access
    hosts = {f"{settings['host'].lower()}:{settings['port']}", f"localhost:{settings['port']}", f"127.0.0.1:{settings['port']}"}

    @app.before_request
    def authorize():
        if request.host.lower() not in hosts or request.scheme != 'https':
            abort(400, description='Use the HTTPS address shown in receiver Settings')
        if request.method not in ('GET', 'HEAD', 'POST', 'DELETE'):
            abort(405)
        changing = request.method in ('POST', 'DELETE')
        if changing and request.headers.get('Origin') != 'https://'+request.host:
            abort(403, description='Request origin rejected')
        if request.path in ('/', '/console.js', '/console.css'):
            return
        if request.path == '/api/session' and request.method == 'POST':
            if not request.is_json:
                abort(415)
            return
        g.user = access.session(request.cookies.get('ts_session'))
        if not g.user:
            abort(401, description='Sign in to this receiver')
        if changing:
            if not secrets.compare_digest(request.headers.get('X-CSRF-Token',''), g.user['csrf']):
                abort(403, description='Session changed. Reload the page.')
            if request.path != '/api/session' and g.user['role'] not in ('operator', 'admin'):
                abort(403, description='An operator account is required')

    @app.after_request
    def headers(response):
        response.headers.update({'Cache-Control':'no-store', 'X-Content-Type-Options':'nosniff',
            'X-Frame-Options':'DENY', 'Referrer-Policy':'no-referrer',
            'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; media-src 'self'; img-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"})
        return response

    from werkzeug.exceptions import HTTPException
    @app.errorhandler(HTTPException)
    def http_error(exc):
        return jsonify(error=exc.description), exc.code

    @app.errorhandler(Exception)
    def error(exc):
        store.event('web_request_error', {'message':'Web request failed ('+type(exc).__name__+')'})
        return jsonify(error='Console request failed; check receiver status and try again.'), 500

    @app.get('/')
    def index():
        return Response(files('tonepage').joinpath('resources/web-console.html').read_text('utf-8'), mimetype='text/html')

    @app.get('/console.js')
    def script():
        return Response(files('tonepage').joinpath('resources/web-console.js').read_text('utf-8'), mimetype='text/javascript')

    @app.get('/console.css')
    def style():
        return Response(files('tonepage').joinpath('resources/web-console.css').read_text('utf-8'), mimetype='text/css')

    @app.route('/api/session', methods=['GET','POST','DELETE'])
    def session():
        if request.method == 'POST':
            d = body()
            if not isinstance(d.get('username'), str) or not isinstance(d.get('password'), str) or len(d['username'])>40 or len(d['password'])>256:
                abort(400, description='Enter a username and password')
            token = access.login(d['username'], d['password'], request.remote_addr)
            now=time.time()
            client_ip=request.remote_addr or 'unknown'
            local_time=datetime.fromtimestamp(now,timezone.utc).astimezone().isoformat(timespec='seconds')
            try:
                store.event('web_sign_in', {'actor':d['username'], 'client_ip':client_ip,
                    'message':f"Web console accessed: {d['username']} from {client_ip} · {local_time}"},at=now)
            except Exception:
                with access.lock:
                    access.sessions.pop(token,None)
                abort(503,description='Unable to record sign-in. Check receiver storage and try again.')
            with access.lock:
                access.sessions.pop(request.cookies.get('ts_session'), None)
            response = jsonify(ok=True)
            response.set_cookie('ts_session', token, secure=True, httponly=True, samesite='Strict', path='/')
            return response
        if request.method == 'DELETE':
            with access.lock:
                access.sessions.pop(request.cookies.get('ts_session'), None)
            response = jsonify(ok=True)
            response.delete_cookie('ts_session', secure=True, httponly=True, samesite='Strict')
            return response
        return jsonify({k:g.user[k] for k in ('name','role','csrf')})

    @app.get('/api/status')
    def status():
        snapshot = controller.read()
        snapshot.pop('tones', None)
        snapshot['snapshot_age'] = max(0, time.time()-snapshot['updated'])
        return jsonify(snapshot)

    @app.get('/api/tones')
    def tones():
        snap = controller.read()
        return jsonify(tones=snap['tones'], revision=snap['revision'])

    def body():
        d = request.get_json()
        if not isinstance(d, dict):
            abort(400, description='Expected an object')
        return d

    @app.post('/api/commands/<action>')
    def command(action):
        if action not in ('start','pause','resume','stop','save-tone','delete-tone','clear-deleted'):
            abort(404)
        key = request.headers.get('Idempotency-Key','')
        if not re.fullmatch(r'[A-Za-z0-9-]{8,80}',key):
            abort(400, description='A unique command key is required')
        try:
            oid = controller.submit(action, body(), g.user['name'], key)
        except ValueError as exc:
            abort(409, description=str(exc))
        return jsonify(id=oid, status='pending'), 202

    @app.get('/api/operations/<oid>')
    def operation(oid):
        result = controller.operation(oid, g.user['name'])
        if not result:
            abort(404)
        return jsonify(result)

    def page():
        try:
            return max(0, min(1000000, int(request.args.get('offset','0'))))
        except ValueError:
            abort(400)

    def record(row):
        d = json.loads(row['data'])
        return dict(id=row['id'], start=row['at'], end=row['end'], status=row['status'],
            local_time=datetime.fromtimestamp(row['at'], timezone.utc).astimezone().isoformat(timespec='seconds'),
            filename=Path(row['path']).name if row['path'] else '', agencies=d.get('agencies',[]),
            duplicate=bool(d.get('duplicate')), synthetic=bool(d.get('synthetic')), interrupted=bool(d.get('interrupted')))

    @app.get('/api/recordings')
    def recordings():
        offset = page()
        search = request.args.get('search','')[:160]
        rows = store.rows("SELECT r.* FROM recordings r WHERE NOT (r.status='deleted' AND EXISTS (SELECT 1 FROM hidden_history h WHERE h.table_name='recordings' AND h.id=r.id)) AND r.data LIKE ? ORDER BY r.at DESC LIMIT 51 OFFSET ?", ('%'+search+'%',offset))
        return jsonify(items=[record(r) for r in rows[:50]], more=len(rows)>50)

    @app.get('/api/recordings/<rid>')
    def details(rid):
        rows = store.rows('SELECT * FROM recordings WHERE id=?',(rid,))
        if not rows:
            abort(404)
        return jsonify(record(rows[0]))

    @app.get('/api/recordings/<rid>/audio')
    def audio(rid):
        rows = store.rows("SELECT path FROM recordings WHERE id=? AND status='complete'",(rid,))
        if not rows or not rows[0]['path']:
            abort(404, description='Recording is not available')
        path = Path(rows[0]['path'])
        if not path.is_absolute() or not managed_audio(store.home,path) or path.suffix.lower() != '.mp3':
            abort(404)
        try:
            return send_file(path, mimetype='audio/mpeg', conditional=True, download_name=path.name,
                             as_attachment=request.args.get('download')=='1', etag=False)
        except OSError:
            abort(404, description='Recording was removed or is unavailable')

    @app.get('/api/activity')
    def activity():
        rows = store.rows('SELECT id,at,type,data FROM events ORDER BY at DESC LIMIT 51 OFFSET ?', (page(),))
        items=[]
        for row in rows[:50]:
            d=json.loads(row.pop('data'))
            # Allowlist only. Raw errors/config/URLs are deliberately not exposed.
            row.update(agencies=d.get('agencies',[]), actor=d.get('actor'), action=d.get('action'), result=d.get('result'),
                       local_time=datetime.fromtimestamp(row['at'], timezone.utc).astimezone().isoformat(timespec='seconds'))
            items.append(row)
        return jsonify(items=items, more=len(rows)>50)
    return app


class WebConsole:
    def __init__(self, home, controller, store):
        self.home, self.controller, self.store = Path(home), controller, store
        self.server = self.thread = None
        self.status = 'Off'
        self.fingerprint = ''
        self._last_warning = 0.

    def server_error(self, msg='', level=20, traceback=False):
        # Cheroot's default logger writes directly to sys.stderr. A windowed
        # Windows executable has no stderr, including during a failed TLS handshake.
        # Never let logging kill the listener. Do not retain raw request/error text.
        now = time.monotonic()
        if now-self._last_warning < 30:
            return
        self._last_warning = now
        error = sys.exc_info()[0]
        kind = error.__name__ if error else 'ConnectionWarning'
        try:
            self.store.event('web_connection_warning', {
                'message': 'Web connection warning ('+kind+'); listener remains available'})
        except Exception:
            pass  # Logging/storage failures must not disable web access either.

    def start(self, settings):
        validate_access(settings)
        if not settings['enabled']:
            return
        if self.server:
            raise ValueError('Stop web access before restarting it')
        from cheroot.wsgi import Server
        from cheroot.ssl.builtin import BuiltinSSLAdapter
        cert,key,self.fingerprint = certificate(self.home, settings['host'])
        server = Server((settings['bind'],settings['port']), create_app(self.controller,self.store,settings),
                        numthreads=6, max=6, timeout=10, request_queue_size=16)
        server.max_request_header_size=16384
        server.max_request_body_size=32768
        server.error_log=self.server_error
        server.ssl_adapter=BuiltinSSLAdapter(str(cert),str(key))
        server.ssl_adapter.context.minimum_version=ssl.TLSVersion.TLSv1_2
        try:
            server.prepare()
        except Exception:
            server.stop()
            raise
        self.server=server
        self.status=f"https://{settings['host']}:{settings['port']}"
        def serve():
            try:
                server.serve()
            except Exception as exc:
                self.status='Web listener stopped unexpectedly ('+type(exc).__name__+'); restart it in Settings'
                try:
                    self.store.event('web_access_error', {'message':self.status})
                except Exception:
                    pass
        self.thread=threading.Thread(target=serve, name='tone-web',daemon=True)
        self.thread.start()

    def stop(self):
        self.controller.cancel_pending()
        if self.server:
            self.server.stop()
            if self.thread:
                self.thread.join(timeout=12)
            self.server=None
        self.status='Off'
