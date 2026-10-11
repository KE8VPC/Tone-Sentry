from __future__ import annotations

from .storage_paths import audio_root, managed_audio

import ftplib
import hashlib
import hmac
import json
import os
import random
import ssl
import smtplib
from email.message import EmailMessage
from email.utils import formatdate
from datetime import datetime
import subprocess
import threading
import time
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

import requests
from .config import validate_discord_template
from .message_templates import filename_for, values_for, render


class PermanentError(Exception):
    pass


class RetryError(Exception):
    def __init__(self, message, delay=None):
        super().__init__(message)
        self.delay = delay


def secret(env_name):
    if not env_name:
        return ""
    value = os.environ.get(env_name)
    if not value:
        raise PermanentError("Missing credential environment variable; check destination settings")
    return value


def check_url(url):
    p = urlparse(url)
    if p.username or p.password or p.fragment or not p.hostname:
        raise PermanentError("Invalid endpoint URL; use credential environment variables")
    if p.scheme != "https" and not (p.scheme == "http" and p.hostname in ("localhost", "127.0.0.1", "::1")):
        raise PermanentError("Remote HTTP endpoints require HTTPS; only loopback permits HTTP")


def is_discord_webhook(url):
    import re
    p = urlparse(url)
    return p.hostname in ('discord.com', 'discordapp.com', 'canary.discord.com', 'ptb.discord.com') and bool(re.fullmatch(r'/api/(?:v\d+/)?webhooks/\d+/[^/]+/?', p.path))


def is_google_chat_webhook(url):
    import re
    from urllib.parse import parse_qs
    try:
        p = urlparse(url)
        query = parse_qs(p.query)
        return (p.scheme == 'https' and p.netloc == 'chat.googleapis.com'
                and bool(re.fullmatch(r'/v1/spaces/[A-Za-z0-9_-]+/messages', p.path))
                and not p.fragment and bool(query.get('key')) and bool(query.get('token')))
    except ValueError:
        return False


def webhook_payload(destination, event):
    mode = destination.get('webhook_format', 'auto')
    if mode == 'google_chat' or mode == 'auto' and is_google_chat_webhook(destination.get('url', '')):
        from .message_templates import validate_template
        template = destination.get('google_chat_template', '{agency} - {time}')
        validate_template(template)
        text = render(template, event, destination.get('include_transcript', False))
        if destination.get('include_transcript') and event.get('text') and '{transcript}' not in template:
            text += '\nTranscript: ' + str(event['text'])
        if not text.strip():
            raise PermanentError('Google Chat message is empty; include agency or other nonempty text')
        # Leave space for JSON escaping within Google's message size limit.
        if len(json.dumps({'text': text}, ensure_ascii=True).encode('utf-8')) > 30000:
            raise PermanentError('Google Chat message is too large; shorten the template or omit the transcript')
        return {'text': text}
    if mode != 'discord' and not (mode == 'auto' and is_discord_webhook(destination.get('url', ''))):
        if destination.get('webhook_template'):
            return dict(event,message=render(destination['webhook_template'],event,destination.get('include_transcript',False)))
        return event
    agency = ', '.join(str(a) for a in event.get('agencies', [])) or 'Unknown agency'
    stamp = event.get('at', event.get('start', time.time()))
    local = datetime.fromtimestamp(stamp)
    local_time = local.strftime('%I:%M %p').lstrip('0')
    template=validate_discord_template(destination.get('discord_template','{agency} - {time}'))
    transcript=str(event.get('text','')) if destination.get('include_transcript') else ''
    values=values_for(event,destination.get('include_transcript',False))
    lines = [template.format_map(values)]
    if transcript and '{transcript}' not in template:
        lines.append('Transcript: '+str(event['text']))
    # Keep within Discord's limit, including supplementary Unicode characters.
    content = '\n'.join(lines).encode('utf-16-le')[:3900].decode('utf-16-le', errors='ignore')
    if not content.strip():
        raise PermanentError('Discord message is empty after replacing placeholders; include agency or other nonempty text')
    return {'content': content, 'allowed_mentions': {'parse': []}}


def post(url, **kwargs):
    check_url(url)
    try:
        response = requests.post(url, timeout=(5, 60), allow_redirects=False, **kwargs)
    except requests.RequestException:
        raise RetryError("Network request failed or timed out") from None
    if response.status_code == 429 or response.status_code >= 500:
        try:
            delay = float(response.headers.get("Retry-After", ""))
        except ValueError:
            delay = None
        raise RetryError(f"Endpoint returned HTTP {response.status_code}", delay)
    if not 200 <= response.status_code < 300:
        if response.status_code == 400 and is_discord_webhook(url):
            raise PermanentError('Discord returned HTTP 400. Check webhook message format and channel type; forum/media channels require a thread_id in the webhook URL. No response body or webhook token was logged.')
        raise PermanentError(f"Endpoint returned HTTP {response.status_code}; redirects are not followed")
    return response


def destinations(config, event, scope=None):
    trigger = event["type"]
    tones = set(event.get("tone_ids", []))
    for d in config["integrations"]:
        if not d.get("enabled", False) or scope is not None and d.get("scope", "shared") != scope:
            continue
        if trigger not in d.get("triggers", ["recording_complete"]):
            continue
        if d.get("tone_ids") and not tones.intersection(d["tone_ids"]):
            continue
        if d["kind"] in ("ftp", "ftps", "transcription", "email") and trigger != "recording_complete":
            continue
        if event.get("test") or event.get("duplicate"):
            continue
        yield d


def queue_actions(store, config, event, scope=None):
    # Queue uploads first so a concurrent worker can always find their jobs.
    for d in sorted(destinations(config, event, scope),key=lambda d:d['kind']=='webhook'):
        includes_audio = d["kind"] in ("ftp", "ftps", "transcription", "email")
        includes_text = d["kind"] == "webhook" and d.get("include_transcript", False)
        if (includes_audio or includes_text) and not event.get("allow_cloud", False):
            store.event("sharing_blocked", {"destination": d["id"], "event_id": event["id"],
                "message": 'Delivery to '+(d.get('name') or d['id'])+' skipped: external audio / transcript sharing is disabled for this page. Review its tone sets in Tone library.',
                "agencies": event.get('agencies', []), "tone_ids": event.get('tone_ids', [])})
            continue
        payload_event = dict(event)
        payload_event['filename']=filename_for(event)
        if d["kind"] == "webhook":
            payload_event.pop("path", None)
            if not d.get("include_transcript", False):
                payload_event.pop("text", None)
        key = f"action:{event['id']}:{d['id']}"
        if d['kind'] == 'email':
            # Separate recipient jobs avoid resending to accepted recipients after
            # another recipient fails. Addresses are never placed in job IDs.
            for recipient in dict.fromkeys(d.get('recipients', [])):
                recipient_key = hashlib.sha256(recipient.encode()).hexdigest()[:20]
                store.enqueue(key+':'+recipient_key, 'email', {'destination':dict(d,recipients=[recipient]),
                    'event':payload_event,'recording_id':event.get('recording_id'),
                    'protect':d.get('protect_recording',True),'action_scope':scope})
            continue
        store.enqueue(key, d["kind"], {"destination": d, "event": payload_event,
                                     "recording_id": event.get("recording_id"), "protect": d.get("protect_recording", True),
                                     "action_scope": scope})


class JobWorker:
    def __init__(self, store, config, handlers=None):
        self.store, self.config = store, config
        self.handlers = handlers or {}
        self.stop_event = threading.Event()
        self.threads = []

    def start(self):
        # Encoding/coordination have their own workers to isolate slow third-party APIs.
        for kinds in (("encode",), ("observe", "coordinate_recording"), ("webhook", "ftp", "ftps", "script", "transcription", "email")):
            thread = threading.Thread(target=self.loop, args=(kinds,), daemon=True, name="jobs-"+kinds[0])
            thread.start()
            self.threads.append(thread)
        maintenance = threading.Thread(target=self.maintenance, daemon=True, name="retention")
        maintenance.start()
        self.threads.append(maintenance)

    def maintenance(self):
        while not self.stop_event.wait(60):
            try:
                self.store.cleanup(self.config["recording"]["retention_days"])
            except Exception as e:
                self.store.event("retention_error", {"message": type(e).__name__})
            if self.stop_event.wait(3540):
                return

    def loop(self, kinds):
        while not self.stop_event.is_set():
            if not self.run_one(kinds):
                self.stop_event.wait(.25)

    def run_one(self, kinds=None):
        job = self.store.claim(kinds)
        if job is None:
            return False
        try:
            if job['kind']=='webhook' and job['payload']['destination'].get('wait_for_ftp'):
                destination=job['payload']['destination']
                event=job['payload']['event']
                if event.get('type')!='recording_complete':
                    raise PermanentError('Waiting for FTP requires the Recording complete trigger')
                dependency=f"action:{event['id']}:{destination['wait_for_ftp']}"
                uploads=self.store.rows('SELECT kind,status FROM jobs WHERE id=?',(dependency,))
                if not uploads or uploads[0]['kind'] not in ('ftp','ftps'):
                    raise PermanentError('Required FTP upload was not queued; check upload destination, scope, tone filters and sharing permission')
                state=uploads[0]['status']
                if state in ('failed','cancelled','ambiguous'):
                    raise PermanentError('Required FTP upload failed or was cancelled; retry the upload first, then this notification')
                if state!='done':
                    with self.store.transaction() as db:
                        db.execute("UPDATE jobs SET status='pending',due=?,attempts=MAX(0,attempts-1),claim=NULL,error='Waiting for FTP upload' WHERE id=? AND claim=? AND status='running'",
                                   (time.time()+2,job['id'],job['claim']))
                    return True
            if job["kind"] in self.handlers:
                self.handlers[job["kind"]](job["payload"])
            else:
                self.execute(job)
            self.store.finish(job)
        except PermanentError as e:
            self.store.finish(job, str(e), permanent=True)
        except Exception as e:
            # Never persist URLs, response bodies, subprocess output or credentials.
            message = str(e) if isinstance(e, RetryError) else type(e).__name__ + ": operation failed; check destination settings"
            self.store.finish(job, message, ambiguous=job["kind"] == "script",
                              retry_after=getattr(e, "delay", None) or (2 ** min(job["attempts"], 10) + random.random()))
        return True

    def execute(self, job):
        p = job["payload"]
        d, event = p["destination"], p["event"]
        if not filename_for(event) and event.get('type') in ('recording_complete','transcript_complete'):
            rows=self.store.rows("SELECT path FROM recordings WHERE id=? AND status='complete'",(event.get('recording_id'),))
            if rows:
                event=dict(event,filename=filename_for(dict(event,path=rows[0]['path'])))
        kind = job["kind"]
        if event.get("shared_id") and (kind in ("ftp", "ftps", "transcription", "email") or kind == "webhook" and d.get("include_transcript")):
            rows = self.store.rows("SELECT data FROM shared WHERE id=?", (event["shared_id"],))
            if not rows or not json.loads(rows[0]["data"]).get("allow_cloud"):
                raise PermanentError("Sharing policy changed; shared audio/transcript delivery blocked")
        if kind == "webhook":
            body = json.dumps(webhook_payload(d, event), sort_keys=True, separators=(",", ":")).encode()
            headers = {"Content-Type": "application/json", "Idempotency-Key": job["id"]}
            if d.get("token_env"):
                headers["Authorization"] = "Bearer " + secret(d["token_env"])
            for name, env in d.get("header_env", {}).items():
                headers[name] = secret(env)
            if d.get("hmac_env"):
                stamp = str(int(time.time()))
                headers["X-TonePage-Timestamp"] = stamp
                headers["X-TonePage-Signature"] = hmac.new(secret(d["hmac_env"]).encode(), stamp.encode()+b"."+body, hashlib.sha256).hexdigest()
            post(d["url"], data=body, headers=headers)
        elif kind == 'email':
            path = self.recording_path(event['path'])
            if path.suffix.lower() != '.mp3':
                raise PermanentError('Email attachment must be an MP3 recording')
            if path.stat().st_size > d.get('email_max_mb', 15)*1024*1024:
                raise PermanentError('MP3 exceeds the configured email attachment limit')
            message = EmailMessage()
            message['From'] = d['email_from']
            message['To'] = ', '.join(d['recipients'])
            subject = d.get('email_subject','Dispatch recording')+' — '+', '.join(event.get('agencies',[]))
            if d.get('email_subject_template'):subject=render(d['email_subject_template'],event)
            message['Subject'] = ' '.join(subject.splitlines())[:250]
            message['Date'] = formatdate(event.get('at',time.time()),localtime=False,usegmt=True)
            message['Message-ID'] = '<'+hashlib.sha256(job['id'].encode()).hexdigest()+'@tonepage.local>'
            body=render(d['email_body_template'],event) if d.get('email_body_template') else 'Dispatch recording attached.\nReceiver: '+str(event.get('site',''))+'\nRecording ID: '+str(event.get('recording_id',''))
            message.set_content(body)
            message.add_attachment(path.read_bytes(),maintype='audio',subtype='mpeg',filename=path.name)
            security = d.get('smtp_security','starttls')
            if security not in ('starttls','ssl'):
                raise PermanentError('SMTP requires STARTTLS or implicit TLS')
            context=ssl.create_default_context()
            client = smtplib.SMTP_SSL(d['smtp_host'],int(d.get('smtp_port',465)),timeout=60,context=context) if security=='ssl' else smtplib.SMTP(d['smtp_host'],int(d.get('smtp_port',587)),timeout=60)
            try:
                with client:
                    if security=='starttls':
                        client.ehlo(); client.starttls(context=context); client.ehlo()
                    if d.get('smtp_username'):
                        client.login(d['smtp_username'],secret(d.get('smtp_password_env')))
                    refused=client.send_message(message,from_addr=d['email_from'],to_addrs=d['recipients'])
                    if refused: raise PermanentError('SMTP recipient rejected; check recipient and server policy')
            except smtplib.SMTPRecipientsRefused as error:
                if any(code < 500 for code, _ in error.recipients.values()):
                    raise RetryError('SMTP temporarily rejected the recipient') from None
                raise PermanentError('SMTP rejected the recipient; check the address and server policy') from None
            except smtplib.SMTPResponseException as error:
                if error.smtp_code >= 500:
                    raise PermanentError(f'SMTP rejected delivery with code {error.smtp_code}; check account, recipient and server limits') from None
                raise RetryError(f'SMTP temporarily rejected delivery with code {error.smtp_code}') from None
        elif kind in ("ftp", "ftps"):
            path = self.recording_path(event["path"])
            remote_name=render(d['remote_filename_template'],event) if d.get('remote_filename_template') else path.name
            if not remote_name or remote_name in ('.','..') or any(ch in remote_name for ch in '/\\\r\n\0'):
                raise PermanentError('FTP filename must be a plain filename without directory separators')
            directory = PurePosixPath(d.get("directory", "/"))
            if ".." in directory.parts or "\r" in str(directory) or "\n" in str(directory):
                raise PermanentError("Unsafe FTP directory")
            client = ftplib.FTP_TLS(context=ssl.create_default_context()) if kind == "ftps" else ftplib.FTP()
            with client:
                client.connect(d["host"], int(d.get("port", 21)), timeout=30)
                from .ftp_credentials import ftp_password
                client.login(d.get("username", "anonymous"), ftp_password(d))
                if kind == "ftps":
                    client.prot_p()
                for part in directory.parts:
                    if part == "/":
                        client.cwd("/")
                        continue
                    try:
                        client.cwd(part)
                    except ftplib.error_perm:
                        client.mkd(part)
                        client.cwd(part)
                client.voidcmd("TYPE I")
                try:
                    remote_size = client.size(remote_name)
                except ftplib.error_perm as error:
                    if str(error).startswith('550'):
                        remote_size = None
                    elif str(error).startswith(('500','502','504')):
                        remote_size = -1 if remote_name in client.nlst() else None
                    else:
                        raise
                exists = remote_size is not None
                if exists:
                    # Flat destinations may contain files from other receivers.
                    # Only acknowledge a retry after verifying identical bytes.
                    if remote_size != -1 and remote_size != path.stat().st_size:
                        raise PermanentError('FTP filename already exists with different contents; choose a unique filename')
                    remote_hash = hashlib.sha256()
                    client.retrbinary('RETR '+remote_name,remote_hash.update)
                    local_hash = hashlib.sha256()
                    with path.open('rb') as source:
                        for block in iter(lambda:source.read(65536),b''):local_hash.update(block)
                    if remote_hash.digest()!=local_hash.digest():
                        raise PermanentError('FTP filename already exists with different contents; choose a unique filename')
                if not exists:
                    temp = remote_name + "." + hashlib.sha256(job["id"].encode()).hexdigest()[:12] + ".part"
                    with path.open("rb") as f:
                        client.storbinary("STOR " + temp, f)
                    client.rename(temp, remote_name)
        elif kind == "script":
            values = {k: str(v) for k, v in event.items() if isinstance(v, (str, int, float))}
            values['filename']=filename_for(event)
            values['filename_url']=values_for(event)['filename_url']
            cwd=None
            if d.get('script_file'):
                from .script_files import script_command
                try:argv,cwd=script_command(d['script_file'],filename_for(event))
                except ValueError as error:raise PermanentError(str(error)) from None
            else:
                argv = [str(x).format_map(values) for x in d["argv"]]
            flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            # Suppress unbounded or secret-bearing output. Exit code is the result.
            result = subprocess.run(argv, shell=False, cwd=cwd, timeout=float(d.get("timeout", 30)), stdin=subprocess.DEVNULL,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=flags)
            if result.returncode:
                raise RuntimeError("Script failed")
        elif kind == "transcription":
            path = self.recording_path(event["path"])
            if path.stat().st_size > d.get("max_bytes", 25_000_000):
                raise PermanentError("Recording exceeds transcription upload limit")
            budget = d.get("daily_limit", 100)
            day = time.strftime("%Y-%m-%d", time.gmtime())
            key = f"usage:{d['id']}:{day}"
            used = self.store.get(key, 0)
            if used >= budget:
                raise PermanentError("Daily transcription submission limit reached")
            headers = {"Idempotency-Key": job["id"]}
            if d.get("token_env"):
                headers["Authorization"] = "Bearer " + secret(d["token_env"])
            fields = dict(d.get("fields", {}))
            self.store.set(key, used+1)
            with path.open("rb") as f:
                response = post(d["url"], headers=headers, data=fields, files={d.get("file_field", "file"): (path.name, f, "audio/mpeg")})
            try:
                data = response.json()
                text = data[d.get("text_field", "text")]
                if not isinstance(text, str):
                    raise ValueError()
            except (ValueError, KeyError, TypeError):
                raise PermanentError("Transcription response must contain the configured text string") from None
            with self.store.transaction() as db:
                db.execute("INSERT OR REPLACE INTO transcripts VALUES(?,?,?,?)", (job["id"], event["recording_id"], text, json.dumps({"provider": d["id"], "machine_generated": True})))
            tid = event["id"] + ":transcript:" + d["id"]
            completed = dict(event, id=tid, type="transcript_complete", text=text)
            self.store.event("transcript_complete", completed, event_id=tid)
            queue_actions(self.store, self.config, completed, scope=p.get("action_scope"))
        else:
            raise PermanentError("Unknown job kind")

    def recording_path(self, name):
        path = Path(name).resolve()
        if not managed_audio(self.store.home,path) or not path.is_file():
            raise PermanentError("Recording is missing or outside the managed directory")
        return path

    def stop(self):
        self.stop_event.set()
        for t in self.threads:
            t.join(timeout=2)
