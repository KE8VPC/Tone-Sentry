import tkinter as tk
import pytest
from tonepage.gui import Application


def test_desktop_forms_initialize_without_starting_capture(tmp_path):
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Desktop display unavailable")
    root.withdraw()
    app = Application(root, tmp_path)
    try:
        root.update()
        assert len(app.pages) == 9
        assert not app.engine.running
        app.edit_tone()
        app.basic_settings()
        app.connection_settings()
        app.manage_integrations()
        app.edit_integration(None, lambda: None)
        root.update()
        assert len([w for w in root.winfo_children() if isinstance(w, tk.Toplevel)]) == 5
    finally:
        app.engine.close()
        root.destroy()


def test_scheduler_reference_and_help_controls_save(tmp_path, monkeypatch):
    from tkinter import ttk, messagebox
    from tonepage.config import load_config
    from tonepage.reference import frequency_for_code
    def error(*args, **kwargs):
        raise AssertionError(args)
    monkeypatch.setattr(messagebox, 'showerror', error)
    try:
        root=tk.Tk()
    except tk.TclError:
        pytest.skip('Desktop display unavailable')
    root.withdraw()
    app=Application(root,tmp_path)
    def descendants(widget):
        for child in widget.winfo_children():
            yield child
            yield from descendants(child)
    def window(title):
        return next(w for w in root.winfo_children() if isinstance(w,tk.Toplevel) and w.title()==title)
    def click(win,label):
        next(w for w in descendants(win) if isinstance(w,ttk.Button) and w.cget('text')==label).invoke()
    try:
        app.edit_schedule()
        click(window('Weekly test schedule'),'Save weekly schedule')
        assert len(load_config(tmp_path)['tones'][0]['tests'])==1
        assert not load_config(tmp_path)['tones'][1]['tests']
        app.edit_schedule()
        click(window('Weekly test schedule'),'Select all tones')
        click(window('Weekly test schedule'),'Save weekly schedule')
        assert all(len(t['tests'])==1 for t in load_config(tmp_path)['tones'])
        app.purge_days.set('14'); app.save_retention()
        assert load_config(tmp_path)['recording']['retention_days']==14
        app.purge_enabled.set(False); app.save_retention()
        assert load_config(tmp_path)['recording']['retention_days']==0
        var=tk.StringVar()
        app.tone_reference(var)
        win=window('Tone reference • 2-Tone Code Chart')
        tree=next(w for w in descendants(win) if isinstance(w,ttk.Treeview))
        tree.selection_set('0')
        click(win,'Use selected frequency')
        assert float(var.get())==frequency_for_code(0)
        app.show_help()
        helpwin=window('Help & how to use Tone Sentry')
        assert 'FIRST SETUP' in next(w for w in descendants(helpwin) if isinstance(w,tk.Text)).get('1.0','end')
        app.edit_tone(app.config['tones'][0])
        click(window('Tone set'),'Save tone set')
        assert len(load_config(tmp_path)['tones'][0]['tests'])==1
        app.edit_integration(None,lambda:None)
        destination=window('Destination settings')
        format_caption=next(w for w in descendants(destination) if isinstance(w,ttk.Label) and w.cget('text')=='Webhook message format')
        destination_format=format_caption.master.grid_slaves(row=format_caption.grid_info()['row'],column=1)[0]
        destination_format.set('discord')
        caption=next(w for w in descendants(destination) if isinstance(w,ttk.Label) and w.cget('text')=='Discord message template')
        entry=caption.master.grid_slaves(row=caption.grid_info()['row'],column=1)[0]
        entry.delete(0,'end');entry.insert(0,'Dispatch: {agency} - {time}')
        click(destination,'Preview Discord message')
        preview=window('Discord message preview (not sent)')
        assert next(w for w in descendants(preview) if isinstance(w,tk.Text)).get('1.0','end').startswith('Dispatch: DEMO Fire - ')
        click(window('Destination settings'),'Save destination')
        assert load_config(tmp_path)['integrations'][0]['enabled'] is False
        assert load_config(tmp_path)['integrations'][0]['discord_template']=='Dispatch: {agency} - {time}'
        app.coordinator_settings()
        click(window('Coordinator administration'),'Save changes')
        assert load_config(tmp_path)['coordinator']['port']==8766
        from tonepage.discovery import Discovery
        candidate=dict(kind='two',a_hz=712.5,b_hz=1122.5,a_seconds=1.,b_seconds=3.,gap_seconds=0.,start=0.,end=4.,quality=.99,ambiguous=False,truncated=False,sequence=[])
        app.engine.candidates.observe(candidate,'live',1000)
        app.refresh_discovery()
        app.candidate_tree.selection_set(app.candidate_tree.get_children()[0])
        app.discovery_draft()
        click(window('Tone set'),'Save tone set')
        added=load_config(tmp_path)['tones'][-1]
        assert added['a_hz']==712.5 and added['b_hz']==1122.5 and not added['enabled']
        import json
        played=[]; details=[]
        monkeypatch.setattr(app.player,'play',lambda path,config:played.append(path))
        monkeypatch.setattr(app,'text_dialog',lambda title,text:details.append(json.loads(text)))
        audio=tmp_path/'recordings'/'play.mp3'; audio.parent.mkdir(exist_ok=True); audio.write_bytes(b'test')
        event=dict(id='event-play',recording_id='record-play',type='recording_complete',agencies=['Fire'])
        app.engine.store.recording('record-play',1,2,'complete',audio,event)
        app.engine.store.event('recording_complete',event,event_id='event-play')
        app.refresh()
        app.events_tree.selection_set('event-play')
        click(app.pages['Overview'],'▶ Play recording')
        click(app.pages['Overview'],'ⓘ JSON details')
        assert played==[audio] and details[-1]['recording_id']=='record-play'
        app.recordings_tree.selection_set('record-play')
        click(app.pages['Recordings'],'▶ Play recording')
        click(app.pages['Recordings'],'ⓘ JSON details')
        assert played==[audio,audio] and details[-1]['recording']['recording_id']=='record-play'
    finally:
        app.engine.close(); root.destroy()

