import copy
import json
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import ttk, filedialog
from .discovery import configured_matches, draft, DEFAULTS
from .discovery_recording import AUDIO_DEFAULTS


class DiscoveryForms:
    def build_discovery(self):
        p=self.scrollable_page(self.pages['Discover Tones'])
        ttk.Label(p,text='Discover paging tones',font=('Segoe UI',14,'bold')).pack(anchor='w',pady=(0,2))
        hint=ttk.Label(p,text='Capture → Listen / review → Select tones → Save a disabled draft. Confirm agency before enabling.',wraplength=740)
        hint.pack(anchor='w',pady=(0,4))
        from .level_meter import LevelMeter
        meter_row=ttk.Frame(p);meter_row.pack(fill='x',pady=(0,4))
        meter_row.columnconfigure(0,weight=1,uniform='meter')
        meter_row.columnconfigure(1,weight=1,uniform='meter')
        self.discovery_meter=LevelMeter(meter_row,self.config['input']['gain'],self.set_input_gain)
        self.discovery_meter.canvas.configure(width=1)
        self.discovery_meter.grid(row=0,column=0,sticky='ew',padx=(0,8))
        controls=ttk.Frame(meter_row);controls.grid(row=0,column=1,sticky='w')
        self.discovery_meter.add_controls(self.auto_gain,self.set_auto_gain,self.save_live_gain,self.meter_feedback,parent=controls)
        self.discovery_meter.controls.bind('<Configure>',lambda e:self.discovery_meter.caption.configure(wraplength=max(100,e.width-4)))
        bar=ttk.Frame(p);bar.pack(fill='x',pady=(0,4))
        for label,fn in [('Start discovery',lambda:self.safe(self.start_discovery)),('Analyze WAV…',self.discover_wav),('Discovery settings…',self.discovery_settings)]:
            ttk.Button(bar,text=label,command=fn).pack(side='left',padx=(0,6))
        self.discovery_status=ttk.Label(p,text='Discovery disabled',wraplength=740)
        self.discovery_status.pack(anchor='w',pady=(0,4))
        filters=ttk.Frame(p);filters.pack(fill='x',pady=(0,4))
        self.unknown_only=tk.BooleanVar(value=True)
        ttk.Checkbutton(filters,text='Hide tones already in my library',variable=self.unknown_only,command=self.refresh_discovery).pack(side='left')
        ttk.Label(filters,textvariable=self.history_feedback).pack(side='right')
        actions=ttk.Frame(p);actions.pack(fill='x',pady=(0,4))
        buttons=[]
        for label,fn in [('▶ Play recording',self.play_candidate),('Stop playback',self.stop_playback),('Review stacked…',lambda:self.safe(self.review_sequence)),('Create draft',self.discovery_draft),('ⓘ Details',self.discovery_details),('Export…',self.export_candidates),('Clear candidates',lambda:self.clear_history('tone_candidates'))]:
            button=ttk.Button(actions,text=label,command=fn)
            buttons.append(button)
        def arrange(event=None):
            width=max(1,actions.winfo_width());row=used=0
            height=max(button.winfo_reqheight() for button in buttons)+2
            for button in buttons:
                needed=button.winfo_reqwidth()+6
                if used and used+needed>width:
                    row+=1;used=0
                button.place(x=used,y=row*height,width=button.winfo_reqwidth(),height=button.winfo_reqheight())
                used+=needed
            actions.configure(height=(row+1)*height)
        actions.bind('<Configure>',arrange)
        self.root.after_idle(arrange)
        def fit_text(event):
            width=max(200,event.width-8)
            hint.configure(wraplength=width)
            self.discovery_status.configure(wraplength=width)
        p.bind('<Configure>',fit_text,add='+')
        self.candidate_tree=self.table(p,('Last seen (local)','Type','A / long Hz','B Hz','A / B seconds','Purity','Seen','Source','Audio','Review'),(125,55,90,75,115,60,45,55,75,140))
        self.candidate_tree.bind('<Double-1>',lambda _:self.discovery_details())

    def start_discovery(self):
        if not self.config.get('discovery',{}).get('enabled'):
            c=copy.deepcopy(self.config)
            c.setdefault('discovery',dict(DEFAULTS))['enabled']=True
            self.apply(c)
        if not self.engine.running: self.engine.start()

    def discover_wav(self):
        path=filedialog.askopenfilename(filetypes=[('16-bit PCM WAV','*.wav')])
        if not path:return
        def action():
            if self.engine.running: raise ValueError('Stop monitoring before analyzing a WAV')
            if not self.config.get('discovery',{}).get('enabled'):
                c=copy.deepcopy(self.config);c.setdefault('discovery',dict(DEFAULTS))['enabled']=True
                self.apply(c)
            self.replay_path(path)
        self.safe(action)

    def discovery_settings(self):
        from .forms import Form
        form=Form(self,'Unknown tone discovery settings')
        settings=dict(DEFAULTS,**AUDIO_DEFAULTS)
        settings.update(self.config.get('discovery',{}))
        labels={'enabled':'Enable discovery during reception / replay','min_seconds':'Minimum stable tone seconds','long_seconds':'Minimum single long-tone seconds','max_seconds':'Maximum stable tone seconds','gap_seconds':'Maximum gap between tones (seconds)','stability_hz':'Allowed frequency variation ± Hz','min_purity':'Minimum spectral purity (0–1)'}
        labels['dropout_seconds']='Bridge brief missing tone audio (seconds, 0 disables)'
        labels.update(min_hz='Lowest paging frequency to consider (Hz)',max_hz='Highest paging frequency to consider (Hz)')
        labels.update(record_enabled='Record discovered candidates (local only)', audio_pre_roll='Audio before the first tone (seconds)', audio_silence_seconds='Continuous silence to stop recording (seconds)', audio_silence_rms='Silence threshold (RMS, 0–1)', audio_min_seconds='Minimum audio after capture starts (seconds)', audio_post_roll='Audio after the last tone (seconds)', audio_max_seconds='Maximum total clip duration (seconds)')
        variables={key:form.field(label,settings[key]) for key,label in labels.items()}
        def weekly():
            for key,value in dict(enabled=True,record_enabled=True,min_seconds=.4,long_seconds=2.,max_seconds=15.,gap_seconds=.8,stability_hz=12.,min_purity=.75,dropout_seconds=.12,min_hz=250.,max_hz=3500.).items():
                variables[key].set(value)
        form.button('Fill weekly-test starting values (review, then Save)',weekly)
        form.note('Starting values require review for your radio. The 250 Hz lower bound excludes low-frequency components; lower it if your paging tones are below that. Lower purity can admit speech. Keep frequency variation smaller than the separation of close A/B tones. Gain, minimum signal and frame size remain shared; discovery purity is independent. Bridging joins missing/low-purity frames, not a different tone. Silence stopping must exceed the allowed gap. Save applies at the next safe boundary. Up to 1,000 groups and 20 recent observations per group are retained.')
        def save():
            c=copy.deepcopy(self.config)
            c['discovery']={key:var.get() if key in ('enabled','record_enabled') else float(var.get()) for key,var in variables.items()}
            self.apply(c)
        form.save(save)

    def refresh_discovery(self):
        if not hasattr(self,'candidate_tree'):return
        observer=self.engine.discovery
        enabled=observer.settings.get('enabled',False)
        frequency=f'{observer.frequency:.1f} Hz' if observer.frequency is not None else '—'
        audio='on' if self.engine.discovery_audio.settings['record_enabled'] else 'off'
        self.discovery_status.configure(text=f"{'Enabled' if enabled else 'Disabled'} · {'Detection paused' if self.engine.detection_paused else 'Analyzing input' if self.engine.running else 'Stopped'} · Peak: {frequency} · Purity: {observer.quality:.0%} · Capture audio: {audio}"+(' · Settings pending' if self.engine.pending_settings else ''))
        items=[]
        for row in self.engine.store.visible_history('tone_candidates',1000):
            data=json.loads(row['data'])
            matches=configured_matches(data,self.config['tones'])
            if matches and self.unknown_only.get():continue
            review='Stack / ambiguous' if data['ambiguous'] else 'End cut off' if data['truncated'] else 'Candidate'
            if matches:review='In library: '+', '.join(matches)
            items.append((row['id'],(datetime.fromtimestamp(row['last_seen']).strftime('%m/%d %H:%M:%S'),data['kind'],data['a_hz'],data['b_hz'] or '—',f"{data['a_seconds']} / {data['b_seconds'] or '—'}",f"{data['quality']:.0%}",row['count'],row['source'],self.candidate_audio_state(data.get('recording_id')),review)))
        self.update_table(self.candidate_tree,items)

    def selected_candidate(self):
        selected=self.candidate_tree.selection()
        rows=self.engine.store.rows('SELECT * FROM tone_candidates WHERE id=?',(selected[0],)) if selected else []
        return rows[0] if rows else None

    def review_sequence(self):
        row=self.selected_candidate()
        if not row:raise ValueError('Select a candidate first. Neighboring candidates from a stack may share the same measured sequence.')
        from .forms import Form
        from .discovery_review import selected_candidate
        data=json.loads(row['data'])
        panel=Form(self,'Review captured sequence / split stacked pages')
        panel.note('Listen to the full capture to identify the agency. Select TWO neighboring runs for an A/B pair, or ONE for a long-tone draft. For A–B–C–D, review A/B and C/D separately; B/C may simply cross the agency boundary. No automatic split is treated as confirmed. Separate drafts reference the same original audio; the MP3 is not cut or overwritten.')
        observations=[dict(data,label='Latest measurement')]
        for item in reversed(data.get('recent',[])):
            if item.get('sequence'):
                observations.append(dict(data,**{k:v for k,v in item.items() if k in ('sequence','recording_id','quality','truncated')},label=datetime.fromtimestamp(item['at']).strftime('%m/%d %H:%M:%S')))
        choices={f'{i+1}. '+o['label']:o for i,o in enumerate(observations)}
        selected=panel.field('Observation',next(iter(choices)),list(choices),True)
        tree=ttk.Treeview(panel.body,columns=('run','hz','duration','gap'),show='headings',selectmode='extended',height=10)
        for key,label,width in [('run','Run',55),('hz','Frequency Hz',140),('duration','Duration seconds',140),('gap','Gap before seconds',140)]:
            tree.heading(key,text=label);tree.column(key,width=width)
        tree.grid(row=panel.row,columnspan=2,sticky='ew');panel.row+=1
        def refresh(*args):
            tree.delete(*tree.get_children())
            for i,run in enumerate(choices[selected.get()].get('sequence',[])):
                tree.insert('','end',iid=str(i),values=(i+1,run['hz'],run['seconds'],run.get('gap_before','Not saved')))
        selected.trace_add('write',refresh);refresh()
        panel.note('Ctrl-click to select two rows. Timing is measured, not a standard-tone lookup. A gap marked Not saved requires a new capture/reanalysis for splitting. Drafts start disabled with external sharing off. Review timings and agency names before enabling.')
        panel.button('Play full captured audio',lambda:self.safe(lambda:self.play_candidate(choices[selected.get()].get('recording_id'))))
        def create():
            item=selected_candidate(choices[selected.get()],[int(i) for i in tree.selection()])
            self.edit_tone(proposed=draft(item))
        panel.button('Create draft from selected run(s)',lambda:self.safe(create))
        ttk.Button(panel.footer,text='Close',command=panel.win.destroy).pack(side='right')

    def discovery_details(self):
        row=self.selected_candidate()
        if not row:return
        from .reference import entries
        data=json.loads(row['data'])
        chart=entries(selectable_only=True)
        nearest={key:[dict(x,error_hz=round(abs(x['hz']-data[key]),2)) for x in sorted(chart,key=lambda x:abs(x['hz']-data[key]))[:3]] for key in ('a_hz','b_hz') if data.get(key)}
        report=dict(first_seen=row['first_seen'],last_seen=row['last_seen'],observations=row['count'],measurement=data,
                    library_frequency_matches=configured_matches(data,self.config['tones']),nearest_chart_entries=nearest,
                    note='Chart matches suggest standard frequencies only. They do not identify the agency. Purity is spectral concentration, not probability of a valid page.')
        from .discovery_context import context, label
        report['recording_contexts']=[]
        for rid in dict.fromkeys(o.get('recording_id') for o in data.get('recent',[]) if o.get('recording_id')):
            clips=self.engine.store.rows('SELECT data FROM recordings WHERE id=?',(rid,))
            if clips:
                clip=context(self.engine.store,json.loads(clips[0]['data']))
                report['recording_contexts'].append(dict(recording_id=rid,label=label(clip),known_page_overlaps=clip.get('known_page_overlaps',[]),note=clip.get('discovery_note')))
        win = self.text_dialog('Unknown tone candidate details',json.dumps(report,indent=2))
        if win:
            self.candidate_observations(data, win)

    def candidate_audio_state(self, rid):
        rows = self.engine.store.rows('SELECT * FROM recordings WHERE id=?', (rid,)) if rid else []
        if not rows: return 'Not recorded' if not rid else 'Missing'
        row = rows[0]
        if row['status'] == 'deleted': return 'Purged'
        if row['status'] == 'complete': return 'Ready' if Path(row['path']).is_file() else 'Missing'
        return {'capturing':'Recording', 'encoding':'Encoding'}.get(row['status'], row['status'])

    def play_candidate(self, rid=None):
        if rid is None:
            row = self.selected_candidate()
            if not row: return
            rid = json.loads(row['data']).get('recording_id')
        rows = self.engine.store.rows('SELECT * FROM recordings WHERE id=?', (rid,)) if rid else []
        self.play_recording_row(rows[0] if rows else None)

    def candidate_observations(self, data, win):
        panel = ttk.Frame(win, padding=12)
        panel.pack(side='bottom', fill='x', before=win.winfo_children()[0])
        ttk.Label(panel, text='Recent observations — choose captured radio audio to replay.', wraplength=670).pack(fill='x')
        tree = self.table(panel, ('Observed','A / B seconds','Audio'), (240,200,140))
        tree.configure(height=4)
        observations = list(reversed(data.get('recent', [])))
        for index, item in enumerate(observations):
            tree.insert('', 'end', iid=str(index), values=(datetime.fromtimestamp(item['at']).strftime('%Y-%m-%d %H:%M:%S'), f"{item['a_seconds']} / {item.get('b_seconds') or '—'}", self.candidate_audio_state(item.get('recording_id'))))
        def play():
            selected = tree.selection()
            if selected:
                rid = observations[int(selected[0])].get('recording_id')
                if rid: self.play_candidate(rid)
        ttk.Button(panel, text='▶ Play selected recording', command=play).pack(anchor='e', pady=(8,0))
        tree.bind('<Double-1>', lambda _:play())

    def discovery_draft(self):
        row=self.selected_candidate()
        if row:self.edit_tone(proposed=draft(json.loads(row['data'])))

    def export_candidates(self):
        path=filedialog.asksaveasfilename(defaultextension='.json',initialfile='unknown-tone-candidates.json')
        if path:
            rows=self.engine.candidates.rows()
            for row in rows:row['data']=json.loads(row['data'])
            self.safe(lambda:Path(path).write_text(json.dumps(rows,indent=2),encoding='utf-8'))
