"""Desktop configuration controls; serialized settings are never an editing surface."""
import copy
import tkinter as tk
import uuid
from importlib.resources import files
from tkinter import ttk
from zoneinfo import available_timezones
from .discovery_gui import DiscoveryForms


class Form:
    def __init__(self, app, title):
        self.app = app
        self.win = tk.Toplevel(app.root)
        self.win.title(title)
        self.win.geometry('820x'+str(min(680,max(400,app.root.winfo_screenheight()-110))))
        self.footer = ttk.Frame(self.win, padding=12)
        self.footer.pack(side='bottom', fill='x')
        canvas = tk.Canvas(self.win, highlightthickness=0)
        scroll = ttk.Scrollbar(self.win, command=canvas.yview)
        scroll.pack(side='right', fill='y')
        canvas.pack(fill='both', expand=True)
        canvas.configure(yscrollcommand=scroll.set)
        self.body = ttk.Frame(canvas, padding=12)
        item = canvas.create_window(0, 0, window=self.body, anchor='nw')
        canvas.bind('<Configure>', lambda e: canvas.itemconfigure(item, width=e.width))
        self.body.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        self.body.columnconfigure(1, weight=1)
        self.row = 0
        self.controls = {}

    def field(self, label, value, choices=None, readonly=False, masked=False):
        row = self.row
        self.row += 1
        caption=ttk.Label(self.body, text=label, wraplength=260)
        caption.grid(row=row, column=0, sticky='w', padx=(0,16), pady=4)
        var = tk.BooleanVar(value=value) if isinstance(value, bool) else tk.StringVar(value=str(value))
        if isinstance(value, bool):
            widget = ttk.Checkbutton(self.body, variable=var)
        elif choices is not None:
            widget = ttk.Combobox(self.body, textvariable=var, values=choices, state='readonly' if readonly else 'normal')
        elif isinstance(value, (int, float)):
            widget = ttk.Spinbox(self.body, textvariable=var, from_=0, to=100000, increment=1 if isinstance(value,int) else .1)
        else:
            widget = ttk.Entry(self.body, textvariable=var, state='readonly' if readonly else 'normal', show='*' if masked else '')
        widget.grid(row=row, column=1, sticky='ew', pady=4)
        self.controls[str(var)]=(caption,widget)
        return var

    def note(self, text):
        ttk.Label(self.body, text=text, wraplength=720).grid(row=self.row, columnspan=2, sticky='w', pady=10)
        self.row += 1

    def multiline(self,label,value):
        caption=ttk.Label(self.body,text=label,wraplength=260)
        caption.grid(row=self.row,column=0,sticky='nw',padx=(0,16),pady=4)
        text=tk.Text(self.body,height=3,width=35,wrap='word',font=('Segoe UI',10))
        text.grid(row=self.row,column=1,sticky='ew',pady=4)
        text.insert('1.0',value)
        variable=tk.StringVar(value=value)
        def changed(event=None):
            if text.edit_modified():
                variable.set(text.get('1.0','end-1c'))
                text.edit_modified(False)
        text.bind('<<Modified>>',changed)
        text.edit_modified(False)
        self.controls[str(variable)]=(caption,text)
        self.row+=1
        return variable

    def button(self, label, action):
        ttk.Button(self.body, text=label, command=action).grid(row=self.row, column=1, sticky='e', pady=5)
        self.row += 1

    def save(self, action, label='Save changes'):
        ttk.Button(self.footer, text='Cancel', command=self.win.destroy).pack(side='left')
        ttk.Button(self.footer, text=label, command=lambda: self.app.safe(lambda: (action(), self.win.destroy()))).pack(side='right')

    def rows(self, label, values, mapping=False):
        self.note(label)
        box = ttk.Frame(self.body)
        box.grid(row=self.row, columnspan=2, sticky='ew')
        self.row += 1
        data = list(values.items()) if mapping else list(values)
        listing = tk.Listbox(box, height=4, exportselection=False)
        listing.pack(fill='x')
        def refresh():
            listing.delete(0,'end')
            for value in data:
                listing.insert('end', f'{value[0]} = {value[1]}' if mapping else value)
        def edit(new=False):
            selected = listing.curselection()
            if not new and not selected:
                return
            index = len(data) if new else selected[0]
            value = ('','') if new and mapping else '' if new else data[index]
            form = Form(self.app, label)
            if mapping:
                key = form.field('Name', value[0])
                val = form.field('Value', value[1])
            else:
                val = form.field('Value (one complete item)', value)
            def save():
                result = (key.get().strip(), val.get()) if mapping else val.get()
                if mapping and (not result[0] or any(x[0]==result[0] for i,x in enumerate(data) if i!=index)):
                    raise ValueError('Provide a unique nonempty field name')
                if new: data.append(result)
                else: data[index] = result
                refresh()
            form.save(save)
        def remove():
            if listing.curselection():
                data.pop(listing.curselection()[0]); refresh()
        for text, fn in [('Add',lambda: edit(True)),('Edit',edit),('Remove',remove)]:
            ttk.Button(box,text=text,command=fn).pack(side='left')
        refresh()
        return data


class FriendlyForms(DiscoveryForms):
    def build_settings(self):
        p = self.scrollable_page(self.pages['Settings'])
        self.heading(p, 'Settings & integrations', 'Save while monitoring. Detector/recording changes wait for a quiet boundary; input changes reconnect automatically with a brief gap.')
        appearance = ttk.Frame(p)
        appearance.pack(fill='x', pady=(0, 12))
        ttk.Label(appearance, text='Appearance (can change while monitoring)').pack(side='left', padx=(0, 16))
        self.theme_choice = tk.StringVar(value=self.config.get('ui', {}).get('theme', 'Light'))
        theme = ttk.Combobox(appearance, textvariable=self.theme_choice, values=['Light','Dark'], state='readonly', width=12)
        theme.pack(side='left')
        theme.bind('<<ComboboxSelected>>', lambda _:self.safe(lambda:self.change_theme(self.theme_choice.get())))
        self.startup_monitoring = tk.BooleanVar(value=self.config.get('ui',{}).get('start_monitoring',False))
        ttk.Checkbutton(p, text='Start monitoring when Tone Sentry opens', variable=self.startup_monitoring,
                        command=lambda:self.safe(self.save_startup_monitoring)).pack(anchor='w',pady=(0,4))
        ttk.Label(p,text='Saved automatically. Applies on the next launch; uses this receiver’s saved input and settings.',wraplength=740).pack(anchor='w',pady=(0,12))
        for title, detail, fn in [
            ('Audio, detection & recording', 'Input device, sensitivity, recording limits, MP3 quality and filename controls.',self.basic_settings),
            ('Audio playback device', 'Choose speakers/headphones for recording playback, independently of radio input.',self.playback_settings),
            ('Remote web console', 'Enable HTTPS browser access, accounts, tone editing and recording playback.',self.web_settings),
            ('Destinations & actions', 'Webhooks, MP3 email, FTP / FTPS, transcription providers and per-agency scripts.',self.manage_integrations),
            ('Receiver connection','Connect independent receivers to a shared coordinator.',self.connection_settings),
            ('Coordinator administration','Configure the coordinator listener and receiver enrollment lists.',self.coordinator_settings),
            ('Export settings','Save a backup of this receiver configuration.',self.export_config),
            ('Import settings','Review a saved settings file and back up current settings before applying.',self.import_settings),
            ('Help & how to','Setup walkthrough, tone chart, schedules, imports and troubleshooting.',self.show_help)]:
            row=ttk.Frame(p)
            row.pack(fill='x',pady=7)
            button=ttk.Button(row,text=title,width=29,command=lambda fn=fn:self.safe(fn))
            button.pack(side='left',padx=(0,16))
            description=ttk.Label(row,text=detail,wraplength=550)
            description.pack(side='left',fill='x',expand=True)
            row.bind('<Configure>',lambda e,b=button,d=description:d.configure(wraplength=max(160,e.width-b.winfo_reqwidth()-16)))

    def reset_editor(self):
        if hasattr(self,'schedule_tree'): self.refresh_schedules()

    def coordinator_settings(self):
        form=Form(self,'Coordinator administration')
        values={}
        labels={'bind':'Listen address','port':'Listen port','token_env':'Shared token environment variable','match_seconds':'Detection correlation window seconds','max_age_seconds':'Maximum late alert age seconds','selection_wait_seconds':'Recording selection delay seconds'}
        for key,label in labels.items(): values[key]=form.field(label,self.config['coordinator'][key])
        allowed=form.rows('Allowed receiver instance UUIDs',self.config['coordinator']['allowed_instances'])
        revoked=form.rows('Revoked receiver instance UUIDs',self.config['coordinator']['revoked_instances'])
        form.note('These settings configure the separate coordinator service. Restart that service after saving. Use a dedicated data folder for the service; do not open this console on its active database. See Help and docs/COORDINATION.md for starting the service and remote TLS setup.')
        def save():
            c=copy.deepcopy(self.config)
            for key,var in values.items(): c['coordinator'][key]=type(c['coordinator'][key])(var.get())
            c['coordinator'].update(allowed_instances=list(allowed),revoked_instances=list(revoked))
            self.apply(c)
        form.save(save)

    def show_help(self):
        from .help_view import show_help
        show_help(self.root)

    def tone_reference(self, target=None):
        from .reference import entries
        from .gui import open_file
        win = tk.Toplevel(self.root)
        win.title('Tone reference • 2-Tone Code Chart')
        win.geometry('930x620')
        body = ttk.Frame(win,padding=16); body.pack(fill='both',expand=True)
        bar = ttk.Frame(body); bar.pack(fill='x')
        query = tk.StringVar()
        group = tk.StringVar(value='All groups')
        ttk.Label(bar,text='Search code, tone number or Hz').pack(side='left')
        ttk.Entry(bar,textvariable=query,width=22).pack(side='left',padx=8)
        ttk.Combobox(bar,textvariable=group,values=['All groups']+sorted({x['group'] for x in entries()}),state='readonly',width=30).pack(side='left')
        tree = self.table(body,('Group','Tone number','Code','Hz','Available'),(310,110,70,110,100))
        def refresh(*_):
            tree.delete(*tree.get_children())
            for x in entries(group=None if group.get()=='All groups' else group.get(),query=query.get()):
                tree.insert('','end',iid=str(x['code']),values=(x['group'],x['number'],x['code'],x['hz'],'Yes' if x['selectable'] else 'Undefined'))
        def choose():
            from .reference import frequency_for_code
            if tree.selection() and target:
                target.set(str(frequency_for_code(int(tree.selection()[0])))); win.destroy()
        query.trace_add('write',refresh); group.trace_add('write',refresh)
        bottom = ttk.Frame(body); bottom.pack(fill='x',pady=10)
        ttk.Button(bottom,text='Open original reference PDF',command=lambda: open_file(files('tonepage').joinpath('resources/tone-chart.pdf'))).pack(side='left')
        if target:
            ttk.Button(bottom,text='Use selected frequency',command=lambda:self.safe(choose)).pack(side='right')
            tree.bind('<Double-1>',lambda _:self.safe(choose))
        refresh()

    def edit_tone(self, original=None, proposed=None):
        tone = copy.deepcopy(original or proposed) if original or proposed else dict(id='tone-'+uuid.uuid4().hex[:12],agency='New agency',kind='two',a_hz=600.,b_hz=900.,a_min=.5,a_max=5.,b_min=.5,b_max=8.,gap_max=.3,tolerance_hz=5.,duplicate_seconds=120.,enabled=True,allow_cloud=False,tests=[])
        form = Form(self,'Tone set')
        values = {}
        for key,label in [('id','Stable tone ID'),('agency','Agency name'),('kind','Paging format'),('enabled','Enable detection'),('allow_cloud','Allow external audio / transcript sharing'),('record_enabled','Record detected pages')]:
            values[key]=form.field(label,tone.get(key,True if key=='record_enabled' else False),choices=['two','long'] if key=='kind' else None,readonly=key in ('kind','id'))
        for key,label,default in [('a_hz','A / long frequency (Hz)',600.),('b_hz','B frequency (two tone only)',900.),('a_min','A / long minimum seconds',.5),('a_max','A / long maximum seconds',5.),('b_min','B minimum seconds',.5),('b_max','B maximum seconds',8.),('gap_max','Maximum A–B gap seconds',.3),('tolerance_hz','Absolute tolerance ± Hz',5.),('duplicate_seconds','Duplicate suppression seconds',120.)]:
            values[key]=form.field(label,tone.get(key,default))
            if key.endswith('_hz') and key in ('a_hz','b_hz'):
                form.button('Select from tone reference…',lambda v=values[key]:self.tone_reference(v))
        percent = form.field('Use percentage tolerance', 'tolerance_percent' in tone)
        fraction = form.field('Frequency tolerance ± percent',tone.get('tolerance_percent',.02)*100)
        override = form.field('Override recording duration for this agency', 'record_min_seconds' in tone or 'record_max_seconds' in tone)
        minimum = form.field('Recording minimum seconds',tone.get('record_min_seconds',self.config['recording']['min_seconds']))
        maximum = form.field('Recording maximum part seconds',tone.get('record_max_seconds',self.config['recording']['max_seconds']))
        def save():
            result = dict(tone)
            for key,var in values.items():
                result[key]=var.get() if key in ('id','agency','kind','enabled','allow_cloud','record_enabled') else float(var.get())
            result.pop('tolerance_percent',None)
            if percent.get(): result['tolerance_percent']=float(fraction.get())/100
            for key,var in [('record_min_seconds',minimum),('record_max_seconds',maximum)]:
                result.pop(key,None)
                if override.get(): result[key]=float(var.get())
            c=copy.deepcopy(self.config)
            if original: c['tones']=[result if t['id']==original['id'] else t for t in c['tones']]
            else: c['tones'].append(result)
            self.apply(c)
        form.save(save,'Save tone set')

    def build_scheduler(self):
        p=self.scrollable_page(self.pages['Scheduler'])
        self.heading(p,'Schedules & automatic cleanup','Weekly windows use each schedule’s time zone. Ignore suppresses paging actions; record only keeps audio without notifications.')
        bar=ttk.Frame(p); bar.pack(fill='x',pady=8)
        for label,fn in [('Add weekly test',lambda:self.edit_schedule()),('Edit selected',self.edit_selected_schedule),('Remove selected',self.remove_schedule)]:
            ttk.Button(bar,text=label,command=fn).pack(side='left',padx=(0,8))
        self.schedule_tree=self.table(p,('Agency','Days','Start','Minutes','Time zone','Mode','Enabled'),(190,170,70,70,170,90,70))
        self.schedule_tree.bind('<Double-1>',lambda _:self.edit_selected_schedule())
        retention=ttk.Frame(p,padding=(0,8)); retention.pack(fill='x')
        self.purge_enabled=tk.BooleanVar(value=self.config['recording']['retention_days']>0)
        self.purge_days=tk.StringVar(value=f"{self.config['recording']['retention_days'] or 30:g}")
        ttk.Checkbutton(retention,text='Automatically delete recordings older than',variable=self.purge_enabled).pack(side='left')
        ttk.Spinbox(retention,textvariable=self.purge_days,from_=1,to=36500,width=7).pack(side='left',padx=8)
        ttk.Label(retention,text='days').pack(side='left')
        ttk.Button(retention,text='Save cleanup schedule',command=lambda:self.safe(self.save_retention)).pack(side='right')
        ttk.Label(p,text='Unfinished deliveries protect their recordings from deletion. Zero / unchecked keeps recordings indefinitely.').pack(anchor='w')
        self.refresh_schedules()

    def save_retention(self):
        c=copy.deepcopy(self.config)
        days=int(self.purge_days.get()) if self.purge_enabled.get() else 0
        if self.purge_enabled.get() and days<1: raise ValueError('Choose at least one day')
        c['recording']['retention_days']=days
        self.apply(c)

    def refresh_schedules(self):
        self.schedule_tree.delete(*self.schedule_tree.get_children())
        days=['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
        for tone in self.config['tones']:
            for i,s in enumerate(tone.get('tests',[])):
                self.schedule_tree.insert('','end',iid=f"{tone['id']}:{i}",values=(tone['agency'],', '.join(days[d] for d in s['days']),s['start'],s['minutes'],s['timezone'],s.get('mode','ignore'),'Yes' if s.get('enabled',True) else 'No'))
        self.purge_enabled.set(self.config['recording']['retention_days']>0)
        self.purge_days.set(f"{self.config['recording']['retention_days'] or 30:g}")

    def schedule_selection(self):
        selected=self.schedule_tree.selection()
        if selected:
            tid,index=selected[0].rsplit(':',1)
            return tid,int(index)

    def edit_selected_schedule(self):
        selected=self.schedule_selection()
        if selected: self.edit_schedule(*selected)

    def remove_schedule(self):
        selected=self.schedule_selection()
        if selected:
            c=copy.deepcopy(self.config)
            next(t for t in c['tones'] if t['id']==selected[0])['tests'].pop(selected[1])
            self.safe(lambda:self.apply(c))

    def edit_schedule(self, tid=None, index=None):
        if not self.config['tones']:
            return self.safe(lambda: (_ for _ in ()).throw(ValueError('Add an agency tone set first')))
        tone=next((t for t in self.config['tones'] if t['id']==tid),self.config['tones'][0])
        s=tone['tests'][index] if index is not None else dict(days=[0],start='12:00',minutes=5,timezone='America/New_York',mode='ignore',enabled=True)
        form=Form(self,'Weekly test schedule')
        form.note('Choose individual tones or Select all. Saving creates a separate weekly rule for each selected tone; future tones are not automatically included.')
        selections={t['id']:form.field(t['agency'],t['id']==tone['id']) for t in self.config['tones']}
        form.button('Select all tones',lambda:[v.set(True) for v in selections.values()])
        form.button('Clear tone selection',lambda:[v.set(False) for v in selections.values()])
        enabled=form.field('Enable weekly window',s.get('enabled',True))
        weekdays=[form.field(day,i in s['days']) for i,day in enumerate(['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])]
        hour,minute=s['start'].split(':')
        h=form.field('Start hour (24 hour)',hour,[f'{i:02}' for i in range(24)],True)
        m=form.field('Start minute',minute,[f'{i:02}' for i in range(60)],True)
        duration=form.field('Window length in minutes',s['minutes'])
        zone=form.field('Time zone',s['timezone'],sorted(available_timezones()))
        mode=form.field('During window',s.get('mode','ignore'),['ignore','record_only'],True)
        form.note('Windows can cross midnight. Time-zone daylight saving changes are handled automatically. No notification is sent for a scheduled test.')
        def save():
            result=dict(days=[i for i,v in enumerate(weekdays) if v.get()],start=h.get()+':'+m.get(),minutes=int(duration.get()),timezone=zone.get(),mode=mode.get(),enabled=enabled.get())
            c=copy.deepcopy(self.config)
            selected=[key for key,var in selections.items() if var.get()]
            if not selected: raise ValueError('Select at least one tone for this schedule')
            if index is not None: next(t for t in c['tones'] if t['id']==tid)['tests'].pop(index)
            for target in c['tones']:
                if target['id'] in selected and result not in target.get('tests',[]):
                    target.setdefault('tests',[]).append(copy.deepcopy(result))
            self.apply(c)
        form.save(save,'Save weekly schedule')

    def playback_settings(self):
        from .playback import output_devices
        import sounddevice as sd
        from .config import save_config, validate
        form=Form(self,'Audio playback device')
        selected=self.config.get('playback',{}).get('device')
        choices={}
        device=form.field('Playback output','System default',['System default'],True)
        live=form.field('Play live dispatch audio after tone detection',self.config.get('playback',{}).get('live_after_detection',False))
        form.note('Live audio starts after an accepted configured page and follows its dispatch recording until it ends. Enable recording for that tone set. Ignored/test pages, suppressed repeats and discovery-only candidates do not start playback. Stop playback silences this session; the next accepted dispatch recording can start it again. Manual recording playback takes priority. Device/option changes stop current playback and take effect on the next page.')
        form.note('Used by Overview, Recordings and Discover Tones. This does not change the monitored input. Avoid routing speaker or loopback playback into that input.')
        def refresh():
            current=choices.get(device.get(),selected)
            choices.clear();choices['System default']=None
            for index,key,info in output_devices(sd):
                choices[f"{key['name']} — {key['hostapi']} ({index})"]=key
            label=next((label for label,key in choices.items() if key==current),None)
            if label is None:
                label='Unavailable saved device';choices[label]=current
            form.controls[str(device)][1].configure(values=list(choices))
            device.set(label)
        self.safe(refresh)
        form.button('Refresh devices',lambda:self.safe(refresh))
        def save():
            if device.get()=='Unavailable saved device':raise ValueError('Choose an available output or System default')
            updated=copy.deepcopy(self.config)
            updated['playback']={'device':choices[device.get()],'live_after_detection':bool(live.get())}
            validate(updated)
            save_config(self.home,updated)
            self.stop_playback()
            self.config['playback']=copy.deepcopy(updated['playback'])
            with self.engine.settings_lock:
                self.engine.config['playback']=copy.deepcopy(updated['playback'])
                self.engine.delivery_config['playback']=copy.deepcopy(updated['playback'])
                if self.engine.pending_settings:
                    self.engine.pending_settings['playback']=copy.deepcopy(updated['playback'])
        form.save(save,'Save playback device')

    def basic_settings(self):
        form=Form(self,'Audio, detection & recording')
        import sounddevice as sd
        from .audio_diagnostics import input_inventory, input_choices, report
        try: devices=input_choices(input_inventory(sd))
        except Exception: devices={}
        devices={'System default':None,**devices}
        current=self.config['input']['device']
        selected=next((k for k,v in devices.items() if v==current),'System default')
        if current is not None and selected=='System default':
            selected=f'Configured device: {current}'; devices[selected]=current
        device=form.field('Audio input device',selected,list(devices),True)
        form.note('The same device can appear through different audio interfaces. All inputs remain available; keep the interface that works for your receiver. Device numbers can change after reconnecting hardware.')
        def diagnostics():
            panel=Form(self,'Audio diagnostics')
            text=report(sd,devices[device.get()],self.config['input']['channel'],self.config['input']['sample_rate'],getattr(self.engine,'last_audio_error',None))
            panel.note('Input selection is from this dialog; channel/sample rate are the currently saved values. Default sample rate is reported by the device, not a list of all supported rates. This report does not open an input or change monitoring.')
            box=tk.Text(panel.body,height=18,wrap='word')
            box.grid(row=panel.row,columnspan=2,sticky='ew');panel.row+=1
            box.insert('1.0',text);box.configure(state='disabled')
            def copy_report():
                self.root.clipboard_clear();self.root.clipboard_append(text)
                feedback.configure(text='Copied audio diagnostics')
            panel.button('Copy audio diagnostics',copy_report)
            feedback=ttk.Label(panel.footer,text='');feedback.pack(side='left')
            ttk.Button(panel.footer,text='Close',command=panel.win.destroy).pack(side='right')
        form.button('Audio diagnostics…',lambda:self.safe(diagnostics))
        site=form.field('Site name',self.config['site'])
        values=[]
        choices={'filename_timezone':['Local time','UTC'],'sample_rate':[8000,16000,22050,24000,32000,44100,48000],'bitrate':['32k','48k','64k','96k','128k','192k']}
        labels={'filename_timezone':'Filename time zone','channel':'Channel (0 = first)','gain':'Input gain multiplier','frame_ms':'Analysis frame milliseconds','min_rms':'Minimum tone signal level','min_purity':'Minimum tone purity (0–1)','pre_roll':'Pre-roll seconds','post_roll':'Post-roll seconds','silence_seconds':'Silence before closing (seconds)','min_seconds':'Minimum recording seconds','max_seconds':'Maximum part seconds','fixed_seconds':'Fixed seconds (0 = silence mode)','silence_rms':'Silence level (0–1)','stack_seconds':'Stacked page window seconds','filename':'Filename template','bitrate':'MP3 bitrate','ffmpeg':'FFmpeg executable (blank = discover)'}
        for section in ('input','detector','recording'):
            form.note(section.title())
            for key,old in self.config[section].items():
                if key in ('device','retention_days'): continue
                var=form.field(labels.get(key,key.replace('_',' ').title()),old,choices.get(key),key in choices)
                values.append((section,key,old,var))
        form.note('Filename fields: {date}, {time}, {agencies}, {agency}, {site}, {instance}, {session}, {offset}. A unique recording ID is always appended. Filename date/time uses recording START in the selected zone; Local time follows this computer, including daylight saving. {offset} is the numeric local offset or UTC. Log tables use local time; completion rows occur later than the filename start. Existing files and queued recordings keep their names/settings. Cleanup is on the Scheduler tab.')
        def save():
            c=copy.deepcopy(self.config); c['site']=site.get(); c['input']['device']=devices[device.get()]
            for section,key,old,var in values: c[section][key]=type(old)(var.get())
            self.apply(c)
        form.save(save)

    def edit_integration(self, original, refresh):
        d=copy.deepcopy(original) if original else dict(id='destination-'+uuid.uuid4().hex[:8],kind='webhook',scope='shared',enabled=False)
        form=Form(self,'Destination settings')
        from .ftp_credentials import encode_password
        sections=[]
        def section(kinds,build):
            before=set(form.body.winfo_children())
            result=build()
            sections.append((set(kinds),set(form.body.winfo_children())-before))
            return result
        common={'id','name','kind','scope','enabled','protect_recording'}
        relevant={'webhook':{'url','include_transcript'},
                  'email':{'smtp_host','smtp_port','smtp_security','smtp_username','smtp_password_env','email_from','email_subject','email_max_mb','email_subject_template','email_body_template'},
                  'ftp':{'host','port','username','directory','password_env','remote_filename_template'},
                  'ftps':{'host','port','username','directory','password_env','remote_filename_template'},
                  'transcription':{'url','token_env','file_field','text_field','daily_limit'},'script':{'timeout'}}
        def subtype():
            from .integrations import is_discord_webhook, is_google_chat_webhook
            kind=values['kind'].get()
            if kind!='webhook':return kind
            try:detected=is_discord_webhook(values['url'].get())
            except ValueError:detected=False
            if webhook_format.get()=='google_chat' or webhook_format.get()=='auto' and is_google_chat_webhook(values['url'].get()):return 'google_chat'
            return 'discord' if webhook_format.get()=='discord' or webhook_format.get()=='auto' and detected else 'generic'
        def active_fields():
            active=common|relevant.get(values['kind'].get(),set())
            if subtype()=='discord':active|={'discord_template'}
            if subtype()=='google_chat':active|={'google_chat_template'}
            if subtype()=='generic':active|={'webhook_template','token_env','hmac_env'}
            return active
        fields=[('name','Destination name',d['id']),('id','Internal destination ID',''),('kind','Destination type','webhook'),('scope','Delivery scope','shared'),('enabled','Enable destination',False),('url','Webhook / transcription URL',''),('host','FTP host',''),('port','FTP port',21),('username','FTP username',''),('directory','FTP remote directory','/dispatch'),('password_env','FTP password environment variable',''),('token_env','API token environment variable',''),('hmac_env','Webhook signing key environment variable',''),('file_field','Transcription audio form field','file'),('text_field','Transcription result text field','text'),('daily_limit','Daily transcription submission limit',100),('timeout','Script timeout seconds',30),('protect_recording','Protect pending recordings',True),('include_transcript','Include transcript in webhook',False)]
        values={}
        webhook_format=form.field('Webhook message format',d.get('webhook_format','auto'),['auto','generic','discord','google_chat'],True)
        uploads={'Do not wait':''}
        uploads.update({item.get('name',item['id'])+' ('+item['id']+')':item['id'] for item in self.config['integrations'] if item['kind'] in ('ftp','ftps')})
        selected=next((label for label,key in uploads.items() if key==d.get('wait_for_ftp','')),'Do not wait')
        wait_for_ftp=form.field('Wait for successful FTP upload',selected,list(uploads),True)
        fields += [('google_chat_template','Google Chat message template','{agency} - {time}')]
        fields += [('discord_template','Discord message template','{agency} - {time}')]
        fields += [('smtp_host','SMTP mail server',''),('smtp_port','SMTP port (STARTTLS 587 / SSL 465)',587),('smtp_security','SMTP encryption','starttls'),('smtp_username','SMTP username',''),('smtp_password_env','SMTP password environment variable',''),('email_from','Sender email address',''),('email_subject','Email subject prefix','Dispatch recording'),('email_max_mb','Maximum MP3 attachment size (MB)',15)]
        fields += [('webhook_template','Generic webhook message template (optional)',''),
                   ('email_subject_template','Email subject template (optional)',''),
                   ('email_body_template','Email body template (optional)',''),
                   ('remote_filename_template','FTP remote filename template (optional)','')]
        for key,label,default in fields:
            options=['webhook','email','ftp','ftps','transcription','script'] if key=='kind' else ['shared','local'] if key=='scope' else ['starttls','ssl'] if key=='smtp_security' else None
            values[key]=form.multiline(label,d.get(key,default)) if key in ('webhook_template','email_body_template','google_chat_template') else form.field(label,d.get(key,default),options,options is not None or key=='id' and original is not None,masked=key in ('password_env','smtp_password_env'))
        # Separate widget: plaintext must never enter the serialized field list.
        password=form.field('FTP password','',masked=True)
        if 'password_b64' in d:
            section(('ftp','ftps'),lambda:form.note('An FTP password is already saved. The empty password box keeps it unchanged.'))
        password_changed=[False]
        password.trace_add('write',lambda *_:password_changed.__setitem__(0,True))
        ftp_panel=ttk.Frame(form.body)
        ftp_panel.grid(row=form.row,columnspan=2,sticky='ew',pady=8)
        form.row+=1
        ftp_result=tk.StringVar(value='Tests current form values without saving. Checks login and directory access; creates no files.')
        def test_ftp():
            import queue
            import threading
            from .ftp_check import check_destination
            snapshot={key:values[key].get() for key in ('kind','host','port','username','password_env','directory')}
            if password_changed[0]:
                snapshot['password_b64']=encode_password(password.get())
            elif 'password_b64' in d:
                snapshot['password_b64']=d['password_b64']
            replies=queue.Queue()
            test_button.configure(state='disabled')
            ftp_result.set('Testing connection, login and directory access…')
            threading.Thread(target=lambda:replies.put(check_destination(snapshot)),daemon=True).start()
            def poll():
                if not form.win.winfo_exists():return
                try:success,message=replies.get_nowait()
                except queue.Empty:
                    form.win.after(100,poll)
                    return
                ftp_result.set(message+' Result applies to the values used when Test was clicked.')
                test_button.configure(state='normal')
            form.win.after(100,poll)
        test_button=ttk.Button(ftp_panel,text='Test FTP connection',command=lambda:self.safe(test_ftp))
        test_button.pack(anchor='w')
        ttk.Label(ftp_panel,textvariable=ftp_result,wraplength=680).pack(anchor='w',pady=(4,0))
        section(('ftp','ftps'),lambda:form.note('FTP password: enter your actual password. Saved as Base64 in this computer\'s settings, not encrypted. Leave unchanged to keep a saved password; enter a new value to replace it. Saved FTP passwords are omitted from settings exports. The environment-variable field is an optional legacy alternative.'))
        section(('ftp','ftps','email','transcription'),lambda:form.note('This destination runs when recording completes. Enable external audio sharing for its agencies.'))
        section(('discord',),lambda:form.note('Webhook format: auto recognizes Discord webhook URLs. Discord uses the complete channel webhook URL, with its embedded token; no bearer token is needed. Notifications are text-only. Forum channels need a thread_id in the URL.'))
        section(('google_chat','discord','generic','ftp','ftps','email'),lambda:form.note('Message placeholders: {agency}, {agencies}, {date}, {time}, {site}, {event_type}, {event_id}, {recording_id}, {filename}, {filename_url}. Filename includes .mp3 and is empty until recording completes. Use {filename_url} in download links to encode spaces and special characters. Optional templates left blank keep existing behavior. Use {{ and }} for literal braces.'))
        section(('google_chat','discord','generic'),lambda:form.note('Webhooks also support {transcript} when sharing is allowed.'))
        section(('ftp','ftps'),lambda:form.note('Uploads go directly into the configured FTP directory. Leave the remote filename template blank to keep the recording filename.'))
        section(('google_chat',),lambda:form.note('Google Chat: paste the complete incoming webhook URL from your Chat space, including key and token. No separate API token is needed. This secret URL is saved in local settings. Text and HTTPS recording links only; no MP3 attachment. See Help & how to: Google Chat setup.'))
        def preview_google_chat():
            from .integrations import webhook_payload
            sample=dict(type='recording_complete',agencies=['Example agency'],site=self.config['site'],filename='Example_agency_2026-10-10_a7f29c.mp3',text='Example dispatch transcript.')
            payload=webhook_payload(dict(webhook_format='google_chat',google_chat_template=values['google_chat_template'].get(),include_transcript=values['include_transcript'].get()),sample)
            self.text_dialog('Google Chat message preview (not sent)',payload['text'])
        section(('google_chat',),lambda:form.button('Preview Google Chat message',lambda:self.safe(preview_google_chat)))
        def preview_discord():
            import time
            from .integrations import webhook_payload
            sample=dict(at=time.time(),agencies=[self.config['tones'][0]['agency']] if self.config['tones'] else ['Example agency'],site=self.config['site'],id='example-event',recording_id='example-recording',type='recording_complete',filename='Example_2026-09-10_14-30-00_a7f29c.mp3',text='Example dispatch transcript.')
            payload=webhook_payload(dict(webhook_format='discord',discord_template=values['discord_template'].get(),include_transcript=values['include_transcript'].get()),sample)
            self.text_dialog('Discord message preview (not sent)',payload['content'])
        section(('discord',),lambda:form.button('Preview Discord message',lambda:self.safe(preview_discord)))
        def preview_templates():
            from .message_templates import render
            sample=dict(type='recording_complete',agencies=['Example agency'],site=self.config['site'],filename='Example_2026-09-10_14-30-00_a7f29c.mp3',recording_id='example-recording')
            kind=values['kind'].get()
            keys={'webhook':['webhook_template'],'email':['email_subject_template','email_body_template'],'ftp':['remote_filename_template'],'ftps':['remote_filename_template']}.get(kind,[])
            output=[key+':\n'+render(values[key].get(),sample) for key in keys if values[key].get().strip()]
            self.text_dialog('Template preview (not sent)','\n\n'.join(output) or 'No optional template entered. Existing destination behavior will be used.')
        section(('generic','email','ftp','ftps'),lambda:form.button('Preview optional templates',lambda:self.safe(preview_templates)))
        recipients=section(('email',),lambda:form.rows('Email recipients (one plain email address per item)',d.get('recipients',[])))
        section(('email',),lambda:form.note('Email attaches the completed MP3. Select Recording complete only and allow external audio sharing on each agency. SMTP credentials use environment variables; a provider may require an app password. Each recipient receives a separate message.'))
        triggers={key:form.field(label,key in d.get('triggers',['recording_complete'])) for key,label in [('activation','Trigger: tone detected'),('recording_complete','Trigger: recording complete'),('transcript_complete','Trigger: transcript complete')]}
        form.note('Agency filter: check the agencies to include. Leave all unchecked for every agency.')
        tones={t['id']:form.field(t['agency'],t['id'] in d.get('tone_ids',[])) for t in self.config['tones']}
        provider=section(('transcription',),lambda:form.rows('Transcription provider form fields',d.get('fields',{}),True))
        headers=section(('generic',),lambda:form.rows('HTTP header → secret environment variable',d.get('header_env',{}),True))
        argv=list(d.get('argv',[]))
        script_file=form.field('Script file',d.get('script_file',''))
        from tkinter import filedialog
        def browse_script():
            path=filedialog.askopenfilename(parent=form.win,title='Choose script file',filetypes=[('Script files','*.bat *.cmd *.sh *.command'),('All files','*.*')])
            if path:script_file.set(path)
        browse=ttk.Button(form.body,text='Browse…',command=browse_script)
        browse.grid(row=form.controls[str(script_file)][1].grid_info()['row'],column=2,padx=4)
        form.controls[str(script_file)]+= (browse,)
        if argv and not d.get('script_file'):
            section(('script',),lambda:form.note('An existing command and its arguments are preserved while Script file is empty. Choose a file to replace that command.'))
        section(('script',),lambda:form.note('Choose a .bat/.cmd file on Windows or an executable script with a #! interpreter declaration on Linux/macOS. The completed MP3 filename is passed as the first argument automatically. Choosing or saving a file does not run it.'))
        def show_relevant_fields(*_):
            kind=values['kind'].get()
            ftp_panel.grid() if kind in ('ftp','ftps') else ftp_panel.grid_remove()
            for widget in form.controls[str(password)]:
                widget.grid() if kind in ('ftp','ftps') else widget.grid_remove()
            active=active_fields()
            for key,var in values.items():
                for widget in form.controls[str(var)]:
                    widget.grid() if key in active else widget.grid_remove()
            for widget in form.controls[str(webhook_format)]:
                widget.grid() if kind=='webhook' else widget.grid_remove()
            for widget in form.controls[str(wait_for_ftp)]:
                widget.grid() if kind=='webhook' else widget.grid_remove()
            for widget in form.controls[str(script_file)]:
                widget.grid() if kind=='script' else widget.grid_remove()
            for allowed,widgets in sections:
                for widget in widgets:
                    widget.grid() if subtype() in allowed else widget.grid_remove()
            for key,var in triggers.items():
                visible=kind in ('webhook','script')
                for widget in form.controls[str(var)]:
                    widget.grid() if visible else widget.grid_remove()
        values['kind'].trace_add('write',show_relevant_fields)
        values['url'].trace_add('write',show_relevant_fields)
        webhook_format.trace_add('write',show_relevant_fields)
        show_relevant_fields()
        def save():
            kind=values['kind'].get()
            active=active_fields()
            result={key:type(default)(values[key].get()) for key,label,default in fields if key in active}
            if kind=='webhook':
                result['webhook_format']=webhook_format.get()
                result['wait_for_ftp']=uploads[wait_for_ftp.get()]
                if subtype()=='generic':result['header_env']=dict(headers)
            if kind=='email':result['recipients']=list(recipients)
            if kind=='transcription':result['fields']=dict(provider)
            if kind=='script':
                if script_file.get().strip():result['script_file']=script_file.get().strip()
                elif argv:result['argv']=list(argv)
                else:raise ValueError('Choose a script file')
            if kind in ('ftp','ftps'):
                if password_changed[0]:
                    result['password_b64']=encode_password(password.get())
                    result.pop('password_env',None)
                elif 'password_b64' in d:result['password_b64']=d['password_b64']
            result.update(triggers=[k for k,v in triggers.items() if v.get()] if kind in ('webhook','script') else ['recording_complete'],tone_ids=[k for k,v in tones.items() if v.get()])
            if not result['name'].strip(): raise ValueError('Enter a destination name')
            result['name'] = result['name'].strip()
            c=copy.deepcopy(self.config)
            if original: c['integrations']=[result if x['id']==original['id'] else x for x in c['integrations']]
            else: c['integrations'].append(result)
            self.apply(c); refresh()
        form.save(save,'Save destination')
