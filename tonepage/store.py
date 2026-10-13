from __future__ import annotations

from .storage_paths import audio_root, managed_audio

import contextlib
import json
import os
import sqlite3
import threading
import time
import uuid
from pathlib import Path


class InstanceLock:
    def __init__(self, home: Path, name="instance.lock"):
        home.mkdir(parents=True, exist_ok=True)
        self.file = (home / name).open("a+b")
        self.file.seek(0)
        if os.fstat(self.file.fileno()).st_size == 0:
            self.file.write(b"0")
            self.file.flush()
        self.file.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (OSError, BlockingIOError):
            self.file.close()
            raise RuntimeError("Another instance is already using this data directory") from None

    def close(self):
        if not self.file.closed:
            self.file.close()


class Store:
    def __init__(self, home: Path, filename="events.sqlite3"):
        self.home = home.resolve()
        home.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.db = sqlite3.connect(home / filename, check_same_thread=False, timeout=15)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS kv(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS hidden_history(table_name TEXT NOT NULL,id TEXT NOT NULL,PRIMARY KEY(table_name,id));
        CREATE TABLE IF NOT EXISTS hidden_job_versions(id TEXT PRIMARY KEY,status TEXT NOT NULL,attempts INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY,at REAL NOT NULL,type TEXT NOT NULL,data TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS events_type_at ON events(type,at);
        CREATE TABLE IF NOT EXISTS recordings(id TEXT PRIMARY KEY,at REAL NOT NULL,end REAL,status TEXT NOT NULL,path TEXT,data TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,kind TEXT NOT NULL,payload TEXT NOT NULL,status TEXT NOT NULL,
          attempts INTEGER NOT NULL DEFAULT 0,due REAL NOT NULL,claim TEXT,error TEXT,created REAL NOT NULL);
        CREATE INDEX IF NOT EXISTS jobs_due ON jobs(status,due);
        CREATE TABLE IF NOT EXISTS transcripts(id TEXT PRIMARY KEY,recording_id TEXT NOT NULL,text TEXT NOT NULL,data TEXT NOT NULL);
        """)
        self.db.commit()

    @contextlib.contextmanager
    def transaction(self):
        with self.lock:
            self.db.execute("BEGIN IMMEDIATE")
            try:
                yield self.db
            except BaseException:
                self.db.rollback()
                raise
            else:
                self.db.commit()

    def rows(self, sql, args=()):
        with self.lock:
            return [dict(r) for r in self.db.execute(sql, args).fetchall()]

    def get(self, key, default=None):
        rows = self.rows("SELECT value FROM kv WHERE key=?", (key,))
        return json.loads(rows[0]["value"]) if rows else default

    def set(self, key, value):
        with self.transaction() as db:
            db.execute("INSERT OR REPLACE INTO kv VALUES(?,?)", (key, json.dumps(value)))

    def event(self, kind, data, at=None, event_id=None):
        eid = event_id or str(uuid.uuid4())
        with self.transaction() as db:
            db.execute("INSERT OR IGNORE INTO events VALUES(?,?,?,?)", (eid, time.time() if at is None else at, kind, json.dumps(data)))
        return eid

    def enqueue(self, key, kind, payload, delay=0):
        with self.transaction() as db:
            db.execute("INSERT OR IGNORE INTO jobs(id,kind,payload,status,due,created) VALUES(?,?,?,'pending',?,?)",
                       (key, kind, json.dumps(payload), time.time()+delay, time.time()))

    def recover(self):
        with self.transaction() as db:
            # External acceptance may have occurred before the prior process died.
            db.execute("UPDATE jobs SET status=CASE WHEN kind='script' THEN 'ambiguous' ELSE 'pending' END, claim=NULL, error='Interrupted; previous outcome may be unknown' WHERE status='running'")

    def claim(self, kinds=None):
        with self.transaction() as db:
            extra, args = "", [time.time()]
            if kinds:
                extra = " AND kind IN (" + ",".join("?" for _ in kinds) + ")"
                args += list(kinds)
            row = db.execute("SELECT * FROM jobs WHERE status='pending' AND due<=?"+extra+" ORDER BY due,created LIMIT 1", args).fetchone()
            if row is None:
                return None
            token = str(uuid.uuid4())
            db.execute("UPDATE jobs SET status='running',claim=?,attempts=attempts+1 WHERE id=?", (token, row["id"]))
            result = dict(row)
            result.update(claim=token, attempts=row["attempts"]+1, payload=json.loads(row["payload"]))
            return result

    def finish(self, job, error=None, permanent=False, ambiguous=False, retry_after=None):
        status = "done" if error is None else ("ambiguous" if ambiguous else "failed" if permanent or job["attempts"] >= 8 else "pending")
        delay = min(3600, 2 ** min(job["attempts"], 10)) if retry_after is None else min(86400, max(1, retry_after))
        with self.transaction() as db:
            db.execute("UPDATE jobs SET status=?,error=?,due=?,claim=NULL WHERE id=? AND claim=? AND status='running'",
                       (status, error, time.time()+delay, job["id"], job["claim"]))

    def recording(self, rid, start, end, status, path, data):
        with self.transaction() as db:
            db.execute("INSERT OR REPLACE INTO recordings VALUES(?,?,?,?,?,?)", (rid, start, end, status, str(path) if path else None, json.dumps(data)))

    def recent(self, table, limit=200):
        if table not in {"events", "recordings", "jobs", "transcripts"}:
            raise ValueError("Unknown table")
        return self.rows(f"SELECT * FROM {table} ORDER BY rowid DESC LIMIT ?", (limit,))

    def reconcile_recordings(self):
        """Mark completed managed audio absent from disk; never delete files or jobs."""
        missing = []
        for row in self.rows("SELECT id,path FROM recordings WHERE status='complete' AND path IS NOT NULL"):
            path = Path(row['path'])
            try:
                if not path.is_absolute() or not managed_audio(self.home, path):
                    continue
                path.stat()
            except FileNotFoundError:
                missing.append((row['id'], row['path']))
            except OSError:
                # Access/device errors do not prove that a recording was deleted.
                continue
        if not missing:
            return 0
        with self.transaction() as db:
            before = db.total_changes
            db.executemany("UPDATE recordings SET status='deleted' WHERE id=? AND path=? AND status='complete'", missing)
            return db.total_changes-before

    def cleanup(self, days):
        if not days:
            return 0
        root = (self.home / "recordings").resolve()
        count = 0
        for row in self.rows("SELECT * FROM recordings WHERE end<? AND status='complete'", (time.time()-days*86400,)):
            # Includes terminal failures: operator must retry or explicitly cancel.
            protected = any(json.loads(j["payload"]).get("recording_id") == row["id"] and json.loads(j["payload"]).get("protect", True)
                            for j in self.rows("SELECT payload FROM jobs WHERE status NOT IN ('done','cancelled')"))
            if protected:
                continue
            path = Path(row["path"]).resolve()
            if not managed_audio(self.home,path):
                self.event("retention_error", {"message": "Refused path outside recording root", "recording_id": row["id"]})
                continue
            path.unlink(missing_ok=True)
            path.with_suffix(".json").unlink(missing_ok=True)
            with self.transaction() as db:
                db.execute("UPDATE recordings SET status='deleted' WHERE id=?", (row["id"],))
            count += 1
        return count

    def clear_history(self, table, completed=False, mode=None):
        if table not in ('events','jobs','tone_candidates','recordings'):
            raise ValueError('This view cannot be cleared')
        if table == 'jobs':
            mode = mode or ('completed' if completed else None)
            if mode not in ('completed','cancelled','all'):
                raise ValueError('Choose which deliveries to clear')
            status = {'completed':'done','cancelled':'cancelled','all':None}[mode]
            with self.transaction() as db:
                rows = db.execute('SELECT id,status,attempts FROM jobs WHERE (? IS NULL OR status=?) AND NOT EXISTS (SELECT 1 FROM hidden_job_versions h WHERE h.id=jobs.id AND h.status=jobs.status AND h.attempts=jobs.attempts) AND NOT EXISTS (SELECT 1 FROM hidden_history h WHERE h.table_name=\'jobs\' AND h.id=jobs.id AND jobs.status=\'done\')',(status,status)).fetchall()
                db.executemany('INSERT OR REPLACE INTO hidden_job_versions VALUES(?,?,?)',[tuple(r) for r in rows])
                return len(rows)
        if table == 'recordings' and mode != 'deleted':
            raise ValueError('Only deleted recordings can be cleared')
        if table == 'recordings':
            self.reconcile_recordings()
        where = " WHERE status='deleted'" if table == 'recordings' else '' 
        with self.transaction() as db:
            before = db.total_changes
            db.execute(f'INSERT OR IGNORE INTO hidden_history SELECT ?,id FROM {table}'+where,(table,))
            return db.total_changes-before

    def visible_history(self, table, limit=200):
        if table not in ('events','jobs','tone_candidates','recordings'):
            raise ValueError('Unknown history view')
        if table == 'jobs':
            return self.rows("SELECT t.* FROM jobs t WHERE NOT EXISTS (SELECT 1 FROM hidden_job_versions h WHERE h.id=t.id AND h.status=t.status AND h.attempts=t.attempts) AND NOT EXISTS (SELECT 1 FROM hidden_history h WHERE h.table_name='jobs' AND h.id=t.id AND t.status='done') ORDER BY t.rowid DESC LIMIT ?",(limit,))
        if table == 'recordings':
            return self.rows("SELECT t.* FROM recordings t WHERE t.status!='deleted' OR NOT EXISTS (SELECT 1 FROM hidden_history h WHERE h.table_name='recordings' AND h.id=t.id) ORDER BY t.at DESC LIMIT ?", (limit,))
        order = 'last_seen' if table == 'tone_candidates' else 'rowid' 
        return self.rows(f'SELECT t.* FROM {table} t WHERE NOT EXISTS (SELECT 1 FROM hidden_history h WHERE h.table_name=? AND h.id=t.id) ORDER BY t.{order} DESC LIMIT ?', (table,limit))

    def close(self):
        with self.lock:
            self.db.close()
