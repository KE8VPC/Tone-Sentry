"""Opt-in frozen-build diagnostic; isolated synthetic reception, no deliveries."""
import json
import tempfile
import time
import traceback
from pathlib import Path


def run(report_path):
    report_path=Path(report_path).resolve()
    report_path.parent.mkdir(parents=True,exist_ok=True)
    report={}
    root=app=None
    try:
        import sys
        import tkinter as tk
        import sounddevice as sd
        from importlib.resources import files
        from zoneinfo import ZoneInfo
        from .gui import Application
        from .engine import ffmpeg_exe
        from .demo import write_demo
        from .reference import entries
        from .config import defaults,save_config
        home=Path(tempfile.mkdtemp(prefix='tonepage-exe-check-',dir=report_path.parent))
        config=defaults();config['discovery'].update(enabled=True, record_enabled=True)
        save_config(home,config)
        root=tk.Tk();root.withdraw()
        app=Application(root,home)
        root.update()
        try:
            compiled = __compiled__ is not None
        except NameError:
            compiled = False
        from . import __version__
        report.update(frozen=bool(getattr(sys,'frozen',False) or compiled),native_compiled=compiled,
                      version=__version__,window_title=root.title(),data_home=str(home),gui_tabs=list(app.pages))
        engine_before_theme = app.engine
        app.change_theme('Dark')
        assert root.cget('background') == '#111b29'
        assert app.engine is engine_before_theme
        report['theme'] = 'Dark persisted without replacing the engine'
        app.set_input_gain(1.25)
        app.save_live_gain()
        assert app.engine is engine_before_theme and app.engine.config['input']['gain']==1.25
        app.meter.set_gain(1.)
        app.save_live_gain()
        report['live_gain'] = 'saved without replacing engine; restored to 1x for replay'
        assert len(entries())==256
        assert files('tonepage').joinpath('resources/tone-chart.pdf').read_bytes().startswith(b'%PDF')
        app.show_help()
        help_window = next(w for w in root.winfo_children() if isinstance(w,tk.Toplevel) and w.title()=='Help & how to use Tone Sentry')
        help_text = next(w for w in help_window.winfo_children() if isinstance(w,tk.Text))
        assert help_text.tag_cget('heading','underline')=='1'
        report['formatted_help'] = 'underlined section headings and navigation loaded'
        app.edit_tone()
        app.edit_schedule()
        app.edit_integration(None,lambda:None)
        app.discovery_settings()
        app.web_settings()
        root.update()
        from .integrations import webhook_payload
        assert webhook_payload(dict(webhook_format='google_chat'),dict(agencies=['Package test']))['text'].startswith('Package test - ')
        report['google_chat']='compiled message formatter and destination controls loaded; no message sent'
        report['reference_and_help']='ok'
        report['timezone']=str(ZoneInfo('America/New_York'))
        report['audio_devices']=len(sd.query_devices())
        from .playback import output_devices
        report['playback_outputs']=len(output_devices(sd))
        app.playback_settings()
        app.auto_gain.set(True);app.set_auto_gain()
        assert app.config['input']['auto_gain']
        app.discovery_meter.set_gain(1.);app.save_live_gain();app.refresh_meter()
        assert not app.auto_gain.get() and app.meter.gain==app.discovery_meter.gain==1.
        report['shared_meter_controls']='auto mode saved; discovery manual override synchronized'
        encoder=Path(ffmpeg_exe(app.config))
        # Require the packaged encoder, not an unrelated executable on PATH.
        import imageio_ffmpeg
        bundled=Path(imageio_ffmpeg.get_ffmpeg_exe())
        assert bundled.is_file()
        app.config['recording']['ffmpeg']=str(bundled)
        app.engine.config['recording']['ffmpeg']=str(bundled)
        report['bundled_encoder']=str(bundled)
        app.engine.replay(write_demo(home/'sample.wav',app.config))
        deadline=time.monotonic()+45
        while app.engine.store.rows("SELECT id FROM jobs WHERE status IN ('pending','running')") and time.monotonic()<deadline:
            time.sleep(.1)
        recordings=app.engine.store.recent('recordings')
        assert recordings and all(r['status']=='complete' and Path(r['path']).stat().st_size>0 for r in recordings),recordings
        assert all(Path(r['path']).parent==home/'audio' for r in recordings)
        report['audio_layout'] = 'audio/ without instance subfolders'
        import re
        from .message_templates import render
        assert all(re.fullmatch('[0-9a-f]{6}',Path(r['path']).stem.rsplit('_',1)[-1]) for r in recordings)
        completed=json.loads(recordings[0]['data'])
        assert render('{filename}',dict(completed,type='recording_complete'))==Path(recordings[0]['path']).name
        from urllib.parse import unquote
        assert all(not any(c.isspace() for c in Path(r['path']).name) for r in recordings)
        assert unquote(render('{filename_url}',dict(completed,type='recording_complete')))==Path(recordings[0]['path']).name
        report['short_filenames_and_templates']='six-character suffixes; filename matches completed MP3'
        from .recording_names import filename_clock
        for row in recordings:
            recorded=json.loads(row['data'])
            clock=filename_clock(recorded['start'],recorded['encoding_settings']['filename_timezone'])
            assert Path(row['path']).name.startswith(clock['date']+'_'+clock['time']+'_')
        assert 'Time (local)' in app.events_tree['columns']
        assert 'Start (local)' in app.recordings_tree['columns']
        report['filename_timezone']='local recording-start filenames and labeled local table times verified'

        from contextlib import ExitStack
        from .data_migration import prepare_default_home
        profile=home/'migration-check';profile.mkdir()
        old=profile/'TonePageDetectData';save_config(old,config)
        with ExitStack() as lifetime:
            migrated=prepare_default_home(lifetime,profile)
            from .config import load_config
            assert load_config(migrated)['instance_id']==config['instance_id']
        report['default_folder_migration']='isolated legacy configuration copied with identity preserved'
        from .settings_import import prepare_import
        from .ftp_credentials import export_settings
        exported=home/'settings-roundtrip.json'
        exported.write_text(json.dumps(export_settings(app.config)),encoding='utf-8')
        reviewed,summary=prepare_import(exported,app.config)
        assert reviewed['instance_id']==app.config['instance_id']
        assert reviewed['tones']==app.config['tones']
        assert all(not d['enabled'] for d in reviewed['integrations'])
        report['settings_import']='export reviewed with identity and tones preserved'
        assert all(j['kind']=='encode' for j in app.engine.store.recent('jobs'))
        candidates=app.engine.candidates.rows()
        assert candidates and all(r['source']=='replay' for r in candidates)
        assert any(json.loads(r['data']).get('recording_id') for r in candidates)
        assert any(json.loads(r['data']).get('discovery_only') for r in recordings)
        internal_events = len(app.engine.store.recent('events',1000))
        app.engine.store.clear_history('events')
        assert not app.engine.store.visible_history('events')
        assert len(app.engine.store.recent('events',1000))==internal_events
        report['history_clearing'] = 'view cleared; internal records retained'
        from .web_check import check
        report['web_console'] = check(app,recordings[0])
        report.update(mp3_recordings=len(recordings),discovery_candidates=len(candidates),external_actions=0,success=True)
    except Exception:
        report.update(success=False,error=traceback.format_exc())
    finally:
        if app: app.close()
        elif root: root.destroy()
        report_path.write_text(json.dumps(report,indent=2),encoding='utf-8')
    return 0 if report.get('success') else 1
