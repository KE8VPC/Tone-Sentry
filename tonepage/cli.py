from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import time
import uuid
from pathlib import Path
from contextlib import ExitStack

from .config import default_home, load_config, save_config
from .store import InstanceLock, Store


def main(argv=None):
    parser = argparse.ArgumentParser(description="Tone Sentry · portable radio paging receiver")
    parser.add_argument("--home", type=Path, default=None, help="Instance data directory (keep outside synchronized folders)")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("gui", help="Open the desktop receiver console (default)")
    sub.add_parser("init", help="Create a default configuration without monitoring")
    sub.add_parser("devices", help="List audio input devices")
    sub.add_parser("run", help="Run the receiver without a desktop")
    replay = sub.add_parser("replay", help="Replay a WAV safely: external actions are disabled")
    replay.add_argument("file", type=Path)
    replay.add_argument("--realtime", action="store_true")
    sub.add_parser("demo", help="Generate and process a synthetic page stack safely")
    imp = sub.add_parser("import-other", aliases=["import-ttd"], help="Preview or apply other application settings")
    imp.add_argument("file", type=Path)
    imp.add_argument("--apply", action="store_true")
    sub.add_parser("status", help="Show recordings, jobs, and receiver registrations")
    sub.add_parser("coordinator", help="Run the optional receiver group coordinator")
    sub.add_parser("new-identity", help="Give a cloned installation a new instance ID")
    sub.add_parser("doctor", help="Check audio, MP3 encoder, configuration, and runtime")
    args = parser.parse_args(argv)
    home = (args.home or default_home()).expanduser().resolve()
    command = args.command or "gui"
    migration_lifetime=ExitStack()
    try:
        if command == "devices":
            import sounddevice as sd
            for index, d in enumerate(sd.query_devices()):
                if d["max_input_channels"]:
                    print(f"{index}: {d['name']} ({d['max_input_channels']} input channels, {d['default_samplerate']:g} Hz default)")
            return 0
        if args.home is None and os.name=='nt':
            from .data_migration import prepare_default_home
            home=prepare_default_home(migration_lifetime)
        elif (home/'moved-to-ToneSentryData.json').exists():
            raise ValueError('This folder is a retained migration backup. Use ToneSentryData to avoid resuming outdated delivery state.')
        if command == "status":
            store = Store(home)
            result = {"recordings": [{k: r[k] for k in ("id", "at", "end", "status", "path")} for r in store.recent("recordings", 20)],
                      "jobs": [{k: r[k] for k in ("id", "kind", "status", "attempts", "error")} for r in store.recent("jobs", 20)]}
            if (home / "coordinator.sqlite3").exists():
                coord = Store(home, "coordinator.sqlite3")
                result["receivers"] = coord.rows("SELECT * FROM nodes")
                result["shared_events"] = coord.rows("SELECT id,group_id,coverage,at FROM shared ORDER BY at DESC LIMIT 20")
                result["shared_jobs"] = [{k: r[k] for k in ("id", "kind", "status", "error")} for r in coord.recent("jobs", 20)]
                coord.close()
            print(json.dumps(result, indent=2))
            store.close()
            return 0
        lock = InstanceLock(home, "coordinator.lock" if command == "coordinator" else "instance.lock")
        try:
            config = load_config(home)
            if command == "init":
                print(f"Created configuration: {home / 'config.json'}")
            elif command == "new-identity":
                config["instance_id"] = str(uuid.uuid4())
                save_config(home, config)
                print(f"New instance identity: {config['instance_id']}")
            elif command in ("import-other", "import-ttd"):
                from .importer import import_other_application
                imported, notes = import_other_application(args.file, config)
                from .config import validate
                validate(imported)
                for t in imported["tones"]:
                    print(f"{t['agency']}: {t['a_hz']:g} / {t.get('b_hz', 'long')} Hz; minimum {t['a_min']} / {t.get('b_min', '—')} s; repeats {t['duplicate_seconds']:g}s")
                print("\n"+"\n".join(notes))
                if args.apply:
                    save_config(home, imported)
                    (home / "import-report.txt").write_text("\n".join(notes), encoding="utf-8")
                    print(f"\nApplied {len(imported['tones'])} tone sets. Original file unchanged.")
            elif command == "doctor":
                from .engine import ffmpeg_exe
                import sounddevice as sd
                print(f"Python: {sys.version.split()[0]} ({sys.platform})")
                print(f"Configuration: valid, {len(config['tones'])} tone sets")
                print(f"Data directory: {home}")
                print(f"MP3 encoder: {ffmpeg_exe(config)}")
                print(f"Audio inputs: {sum(bool(d['max_input_channels']) for d in sd.query_devices())}")
                import tkinter
                print(f"Desktop toolkit: Tk {tkinter.TkVersion}")
            elif command == "gui":
                from .gui import launch
                launch(home)
            elif command == "coordinator":
                from .coordination import Coordinator, server_for
                from .integrations import secret
                store = Store(home, "coordinator.sqlite3")
                coordinator = Coordinator(store, config)
                server = server_for(coordinator, secret(config["coordinator"]["token_env"]))
                if config["coordinator"]["bind"] not in ("127.0.0.1", "::1", "localhost"):
                    raise ValueError("Bind coordinator to loopback and use an authenticated HTTPS reverse proxy for remote access")
                coordinator.start()
                print(f"Coordinator listening on {server.server_address[0]}:{server.server_address[1]}; Ctrl+C to stop")
                try:
                    server.serve_forever(poll_interval=.25)
                except KeyboardInterrupt:
                    pass
                finally:
                    server.server_close()
                    coordinator.stop()
            else:
                from .engine import Engine
                engine = Engine(home, config)
                try:
                    if command in ("demo", "replay"):
                        if command == "demo":
                            from .demo import write_demo
                            path = write_demo(home / "demo.wav", config)
                        else:
                            path = args.file
                        engine.replay(path, getattr(args, "realtime", False))
                        deadline = time.monotonic()+90
                        while engine.store.rows("SELECT id FROM jobs WHERE kind='encode' AND status IN ('pending','running')") and time.monotonic() < deadline:
                            time.sleep(.1)
                        records = engine.store.recent("recordings", 5)
                        print(json.dumps([{k: r[k] for k in ("id", "status", "path")} for r in records], indent=2))
                        failed = engine.store.rows("SELECT id FROM jobs WHERE kind='encode' AND status NOT IN ('done','cancelled')")
                        if failed:
                            print("Encoding is incomplete; inspect status for details", file=sys.stderr)
                            return 1
                    else:
                        engine.start()
                        print("Receiver running; Ctrl+C to stop")
                        last_cleanup = 0
                        while True:
                            time.sleep(1)
                            if time.monotonic()-last_cleanup > 3600:
                                engine.store.cleanup(config["recording"]["retention_days"])
                                last_cleanup = time.monotonic()
                except KeyboardInterrupt:
                    pass
                finally:
                    engine.close()
        finally:
            lock.close()
        return 0
    except Exception as e:
        print(f"Tone Sentry: {e}", file=sys.stderr)
        if command == "gui":
            try:
                import tkinter as tk
                from tkinter import messagebox
                error_root = tk.Tk()
                error_root.withdraw()
                messagebox.showerror("Tone Sentry", str(e), parent=error_root)
                error_root.destroy()
            except Exception:
                pass
        return 1
    finally:
        migration_lifetime.close()


if __name__ == "__main__":
    raise SystemExit(main())
