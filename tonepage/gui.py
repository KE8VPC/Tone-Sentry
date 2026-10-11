from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from importlib.resources import files
from tkinter import ttk, filedialog, messagebox

from .config import load_config, save_config, validate
from .engine import Engine
from .importer import import_other_application
from .forms import FriendlyForms
from .appearance import Appearance
from . import __version__

BG, PANEL, TEXT, MUTED, ACCENT = "#eef2f6", "#ffffff", "#15283e", "#627187", "#c95818"


def open_file(path):
    if os.name == "nt":
        os.startfile(str(path))
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])


class Application(FriendlyForms):
    def __init__(self, root, home):
        self.root, self.home = root, home
        self.startup_timer = None
        if os.name == 'nt':
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('MikeBeam.TonePageDetect')
        self.history_feedback = tk.StringVar(master=root,value='')
        self.config = load_config(home)
        self.auto_gain = tk.BooleanVar(master=root,value=self.config['input'].get('auto_gain',False))
        self.meter_feedback = tk.StringVar(master=root,value='')
        from .playback import Player
        self.player = Player()
        self.engine = Engine(home, self.config)
        self.engine.live_playback_allowed = self.player.is_idle
        self.engine.start_workers()
        self.root.title("Tone Sentry · Receiver console")
        self.root.geometry(f"{min(1100,root.winfo_screenwidth()-40)}x{min(740,root.winfo_screenheight()-100)}")
        self.root.minsize(880, 460)
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10), padding=(6, 4), background=PANEL, foreground=TEXT)
        style.configure('Header.TButton',font=('Segoe UI',9),padding=(4,5),width=0)
        style.configure('Monitor.Header.TButton',background=ACCENT,foreground='white')
        style.map('Monitor.Header.TButton',background=[('active','#a44612')],foreground=[('!disabled','white')])
        style.configure("Accent.TButton", background=ACCENT, foreground="white")
        style.map("Accent.TButton", background=[("active", "#a44612")])
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=26, background=PANEL, fieldbackground=PANEL, foreground=TEXT, borderwidth=0)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#e3eaf1", foreground=TEXT, padding=4)
        style.map("Treeview", background=[("selected", "#d4e7ef")], foreground=[("selected", TEXT)])
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", padding=(4, 6), font=("Segoe UI", 9))
        style.configure("Horizontal.TProgressbar", background="#158578", troughcolor="#d9e4ea")
        header = tk.Frame(root, bg=TEXT, padx=12, pady=8)
        header.pack(fill="x")
        brand = tk.Frame(header,bg=TEXT)
        brand.pack(side='left')
        brand_title=tk.Frame(brand,bg=TEXT)
        brand_title.pack(anchor='w')
        title_label=tk.Label(brand_title,text='TONE SENTRY',bg=TEXT,fg='white',font=('Segoe UI',16,'bold'))
        title_label.grid(row=0,column=0,sticky='w')
        creator_label=tk.Label(brand_title,text='Created by: Mike Beam',bg=TEXT,fg='#afc3d7',font=('Segoe UI',9))
        creator_label.grid(row=0,column=1,sticky='w',padx=(10,0))
        tk.Label(brand,text='PAGING MONITOR & TONE DISCOVERY',bg=TEXT,fg='#afc3d7',font=('Segoe UI',8)).pack(anchor='w')
        self.header_actions=tk.Frame(header,bg=TEXT)
        self.header_actions.pack(side='right')
        self.header_buttons=[]
        for full,short,fn in [('Help & how to','Help',self.show_help),('Run safe demo','Safe demo',self.demo),
                              ('Replay WAV…','Replay',self.replay),('Start monitoring','Start radio',self.toggle),
                              ('Playback device…','Output',lambda:self.safe(self.playback_settings))]:
            button=ttk.Button(self.header_actions,text=full,command=fn,style='Header.TButton')
            button.pack(side='left',padx=(4,0))
            self.header_buttons.append((button,full,short))
        self.start_button=self.header_buttons[3][0]
        self.start_button.configure(style='Monitor.Header.TButton')
        self.compact_header=False
        def fit_header(event=None):
            from tkinter import font
            measure=font.Font(root=root,font=('Segoe UI',9))
            compact_actions=sum(measure.measure(short)+24 for _,_,short in self.header_buttons)
            inline_brand=title_label.winfo_reqwidth()+creator_label.winfo_reqwidth()+10
            if header.winfo_width()<compact_actions+inline_brand+32:
                creator_label.grid_configure(row=1,column=0,columnspan=2,padx=0)
            else:
                creator_label.grid_configure(row=0,column=1,columnspan=1,padx=(10,0))
            required=sum(measure.measure(full)+24 for _,full,_ in self.header_buttons)+brand.winfo_reqwidth()+32
            self.compact_header=header.winfo_width()<required
            for button,full,short in self.header_buttons:
                button.configure(text=short if self.compact_header else full)
            self.update_monitor_label()
        header.bind('<Configure>',fit_header)
        top = ttk.Frame(root, padding=(12, 4))
        top.pack(fill="x")
        self.site_label=ttk.Label(top,text=self.config['site'],font=('Segoe UI',11,'bold'),width=24)
        self.site_label.pack(side='left')
        self.playback_status=ttk.Label(top,text=self.player.status,anchor='e')
        self.playback_status.pack(side='right',fill='x',expand=True)
        root.bind("<F1>", lambda _: self.show_help())
        self.tabs = ttk.Notebook(root)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=(0, 6))
        self.pages = {}
        for label in ("Overview", "Tone library", "Discover Tones", "Recordings", "Deliveries", "Receivers", "Scheduler", "Settings", "About"):
            page = ttk.Frame(self.tabs, padding=10)
            self.tabs.add(page, text=label)
            self.pages[label] = page
        self.build_overview()
        self.build_tones()
        self.build_recordings()
        self.build_jobs()
        self.build_receivers()
        self.build_settings()
        self.build_scheduler()
        self.build_discovery()
        self.build_about()
        footer = ttk.Frame(root, padding=(12, 0, 12, 4))
        footer.pack(side='bottom', fill="x", before=self.tabs)
        self.status = ttk.Label(footer, text="Ready · monitoring starts only when requested", foreground=MUTED)
        self.status.pack(side="left")
        ttk.Label(footer, text=__version__+"  •  DEVELOPMENT EDITION", foreground=MUTED, font=("Segoe UI", 9)).pack(side="right")
        self.appearance = Appearance(root, self.config.get('ui', {}).get('theme', 'Light'))
        self.refresh_tones()
        self.refresh()
        self.refresh_meter()
        from .web_setup import initialize
        initialize(self)

    def web_settings(self):
        from .web_setup import settings_dialog
        settings_dialog(self)

    def save_startup_monitoring(self):
        enabled = bool(self.startup_monitoring.get())
        updated = copy.deepcopy(self.config)
        updated.setdefault('ui', {})['start_monitoring'] = enabled
        try:
            save_config(self.home, updated)
        except Exception:
            self.startup_monitoring.set(self.config.get('ui',{}).get('start_monitoring',False))
            raise
        self.config = updated
        with self.engine.settings_lock:
            for config in (self.engine.config, self.engine.delivery_config, self.engine.pending_settings):
                if config is not None:
                    config.setdefault('ui', {})['start_monitoring'] = enabled

    def schedule_startup_monitoring(self):
        if self.startup_timer is None and self.config.get('ui',{}).get('start_monitoring',False):
            self.startup_timer = self.root.after_idle(self.startup_monitor)

    def startup_monitor(self):
        self.startup_timer = None
        if (self.config.get('ui',{}).get('start_monitoring',False)
                and not self.engine.running and not self.engine.replay_safe):
            self.safe(self.engine.start)

    def update_monitor_label(self):
        self.start_button.configure(text=('Stop radio' if self.engine.running else 'Start radio') if self.compact_header else ('Stop monitoring' if self.engine.running else 'Start monitoring'))

    def open_audio_folder(self):
        from .storage_paths import audio_root
        open_file(audio_root(self.home))

    def set_input_gain(self, gain):
        self.auto_gain.set(False)
        self.config['input']['auto_gain'] = False
        self.engine.config['input']['auto_gain'] = False
        self.config['input']['gain'] = gain
        self.engine.config['input']['gain'] = gain
        if self.gain_save_timer: self.root.after_cancel(self.gain_save_timer)
        self.gain_save_timer = self.root.after(400, self.save_live_gain)

    def set_auto_gain(self):
        enabled=self.auto_gain.get()
        if not enabled and self.config['input'].get('auto_gain') and self.engine.running:
            self.config['input']['gain']=self.engine.gain_control.applied
            self.engine.config['input']['gain']=self.engine.gain_control.applied
        self.config['input']['auto_gain']=enabled
        self.engine.config['input']['auto_gain']=enabled
        self.save_live_gain()

    def save_live_gain(self):
        if self.gain_save_timer: self.root.after_cancel(self.gain_save_timer)
        self.gain_save_timer = None
        def save():
            with self.engine.settings_lock:
                if self.engine.pending_settings:
                    for key in ('gain','auto_gain'):
                        self.engine.pending_settings['input'][key]=self.config['input'][key]
            save_config(self.home,self.config)
            self.meter_feedback.set('Saved · '+('Auto' if self.auto_gain.get() else 'Manual'))
        self.safe(save)

    def refresh_meter(self):
        import time
        gain = self.engine.gain_control.applied if self.config['input'].get('auto_gain') and self.engine.running else self.config['input']['gain']
        for meter in (self.meter,self.discovery_meter):
            meter.gain = gain
            meter.display(self.engine.peak_level if self.engine.running else 0., self.engine.running and time.monotonic()<self.engine.overload_until)
        self.playback_status.configure(text=self.engine.live_audio.status or self.player.status)
        self.root.after(80,self.refresh_meter)

    def clear_history(self, table, completed=False, mode=None):
        label = (mode or 'completed')+' deliveries' if table=='jobs' else 'deleted recording entries' if table=='recordings' else 'activity history' if table=='events' else 'candidate history'
        if not messagebox.askyesno('Clear history', 'Clear '+label+' from view? Recordings and pending work are preserved.',parent=self.root): return
        count = self.engine.store.clear_history(table, completed, mode)
        self.history_feedback.set(f'Cleared {count} entries')

    def change_theme(self, theme):
        updated = copy.deepcopy(self.config)
        updated.setdefault('ui', {})['theme'] = theme
        validate(updated)
        save_config(self.home, updated)
        self.config.setdefault('ui', {})['theme'] = theme
        self.engine.config.setdefault('ui', {})['theme'] = theme
        self.appearance.apply(theme)

    def build_about(self):
        p = self.scrollable_page(self.pages['About'])
        self.heading(p, 'Tone Sentry', 'Paging Monitor & Tone Discovery')
        ttk.Label(p, text='Created By:  Mike Beam', font=('Segoe UI', 16, 'bold')).pack(anchor='w', pady=(0, 12))
        ttk.Label(p, text='Version '+__version__+' · Unrestricted development edition').pack(anchor='w', pady=6)
        ttk.Label(p, text='All current features are available. Registration does not restrict reception or recording in this development release.', wraplength=850).pack(anchor='w', pady=6)
        ttk.Label(p, text='Tone Sentry is an updated and capable pager tone detection system, inspired by FD Tone Notify and 2 Tone Detect.\n\nThis release is an operational beta provided for testing and evaluation. Support is limited, and functionality and reliability remain subject to ongoing validation.\n\nThe operator is responsible for proper configuration and use and assumes all risks associated with improper use of the software.', foreground=MUTED, wraplength=740, justify='left').pack(anchor='w', pady=12)
        ttk.Button(p, text='Help & how to', command=self.show_help).pack(anchor='w', pady=8)
        ttk.Button(p, text='Third-party acknowledgments', command=lambda:self.text_dialog('Third-party acknowledgments', files('tonepage').joinpath('resources/third-party.md').read_text(encoding='utf-8'))).pack(anchor='w', pady=8)
        from .licensing import public_keys, status
        registered = status(self.home)
        self.registration_status = ttk.Label(p, text=('Registered to '+registered['licensed_to']) if registered else 'Registration: unrestricted development edition')
        self.registration_status.pack(anchor='w', pady=(18, 8))
        row = ttk.Frame(p)
        row.pack(fill='x')
        self.registration_key = tk.StringVar()
        ttk.Entry(row, textvariable=self.registration_key, show='•', width=60).pack(side='left', padx=(0, 12))
        ttk.Button(row, text='Activate full version', command=lambda:self.safe(self.activate_registration), state='normal' if public_keys() else 'disabled').pack(side='left')
        ttk.Label(p, text='Offline signed-key support is included. Publisher key setup is pending; activation is not required for this build.', wraplength=850).pack(anchor='w', pady=8)

    def activate_registration(self):
        from .licensing import activate
        data = activate(self.home, self.registration_key.get())
        self.registration_key.set('')
        self.registration_status.configure(text='Registered to '+data['licensed_to']+' · Full edition')

    def heading(self, parent, title, subtitle):
        ttk.Label(parent, text=title, font=("Segoe UI", 14, "bold")).pack(anchor="w")
        description=ttk.Label(parent, text=subtitle, foreground=MUTED, wraplength=900)
        description.pack(fill='x', pady=(2, 6))
        parent.bind('<Configure>',lambda e:description.configure(wraplength=max(200,e.width-20)),add='+')

    def table(self, parent, columns, widths):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)
        tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
        for col, width in zip(columns, widths):
            tree.heading(col, text=col)
            tree.column(col, width=width, minwidth=60)
        scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        horizontal=ttk.Scrollbar(frame,orient='horizontal',command=tree.xview)
        horizontal.pack(side='bottom',fill='x')
        tree.configure(xscrollcommand=horizontal.set)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        return tree

    def scrollable_page(self, parent):
        """Keep controls and a usable list reachable in smaller windows."""
        canvas=tk.Canvas(parent,highlightthickness=0,takefocus=True)
        scrollbar=ttk.Scrollbar(parent,command=canvas.yview)
        scrollbar.pack(side='right',fill='y')
        canvas.pack(fill='both',expand=True)
        canvas.configure(yscrollcommand=scrollbar.set)
        body=ttk.Frame(canvas)
        item=canvas.create_window(0,0,window=body,anchor='nw')
        def layout(event=None):
            canvas.itemconfigure(item,width=canvas.winfo_width(),height=max(canvas.winfo_height(),body.winfo_reqheight()))
            canvas.configure(scrollregion=canvas.bbox('all'))
        canvas.bind('<Configure>',layout)
        body.bind('<Configure>',layout)
        def wheel(event):
            widget=event.widget
            if isinstance(widget,ttk.Treeview):return
            while widget is not None and widget is not canvas:
                widget=getattr(widget,'master',None)
            if widget is canvas:
                if event.num in (4,5):amount=-1 if event.num==4 else 1
                else:amount=-1 if event.delta>0 else 1
                canvas.yview_scroll(amount*3,'units')
                return 'break'
        self.root.bind('<MouseWheel>',wheel,add='+')
        self.root.bind('<Button-4>',wheel,add='+')
        self.root.bind('<Button-5>',wheel,add='+')
        canvas.bind('<Next>',lambda _:canvas.yview_scroll(1,'pages'))
        canvas.bind('<Prior>',lambda _:canvas.yview_scroll(-1,'pages'))
        return body

    def build_overview(self):
        p = self.scrollable_page(self.pages["Overview"])
        ttk.Label(p,text='Receiver activity',font=('Segoe UI',14,'bold')).pack(anchor='w',pady=(0,4))
        cards = tk.Frame(p, bg=BG)
        cards.pack(fill="x", pady=(0, 4))
        self.card_values = {}
        card_widgets=[]
        for title,label in (("RECEIVER","Receiver"),("ENABLED TONE SETS","Enabled tones"),("RECORDINGS","Recordings"),("PENDING ACTIONS","Pending actions")):
            card = tk.Frame(cards, bg=PANEL, padx=6, pady=4, highlightbackground="#dce4ed", highlightthickness=1)
            tk.Label(card,text=label+':',bg=PANEL,fg=MUTED,font=('Segoe UI',10)).pack(side='left')
            value=tk.Label(card,text='—',bg=PANEL,fg=TEXT,font=('Segoe UI',11,'bold'))
            value.pack(side='left',padx=(5,0))
            self.card_values[title]=value
            card_widgets.append(card)
        def fit_cards(event=None):
            columns=4 if sum(card.winfo_reqwidth()+6 for card in card_widgets)<=cards.winfo_width() else 2
            for i in range(4):cards.columnconfigure(i,weight=1 if i<columns else 0,minsize=0)
            for i,card in enumerate(card_widgets):
                card.grid(row=i//columns,column=i%columns,sticky='ew',padx=(0,6 if i%columns<columns-1 else 0),pady=(0,2))
        cards.bind('<Configure>',fit_cards)
        self.root.after_idle(fit_cards)
        from .level_meter import LevelMeter
        self.gain_save_timer = None
        meter_row=ttk.Frame(p);meter_row.pack(fill='x',pady=(0,4))
        meter_row.columnconfigure(0,weight=1,uniform='meter')
        meter_row.columnconfigure(1,weight=1,uniform='meter')
        self.meter=LevelMeter(meter_row,self.config['input']['gain'],self.set_input_gain)
        self.meter.canvas.configure(width=1)
        self.meter.grid(row=0,column=0,sticky='ew',padx=(0,8))
        controls=ttk.Frame(meter_row);controls.grid(row=0,column=1,sticky='w')
        self.meter.add_controls(self.auto_gain,self.set_auto_gain,self.save_live_gain,self.meter_feedback,parent=controls)
        self.meter.controls.bind('<Configure>',lambda e:self.meter.caption.configure(wraplength=max(100,e.width-4)))
        actions = ttk.Frame(p)
        actions.pack(fill="x", pady=(0, 4))
        ttk.Button(actions, text="▶ Play recording", command=self.play_event).pack(side="left")
        ttk.Button(actions, text="Stop playback", command=self.stop_playback).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="ⓘ JSON details", command=self.show_event).pack(side="left", padx=8)
        self.pause_button=ttk.Button(actions,text='Pause detections',command=lambda:self.safe(lambda:self.engine.pause_detection(not self.engine.detection_paused)))
        self.pause_button.pack(side='left')
        ttk.Button(actions,text='Clear all',command=lambda:self.clear_history('events')).pack(side='right')
        self.history_result = ttk.Label(actions,textvariable=self.history_feedback)
        self.history_result.pack(side='right',padx=8)
        self.events_tree = self.table(p, ("Time (local)", "Event", "Agency / detail", "Classification"), (100, 160, 510, 170))
        self.events_tree.bind("<Double-1>", lambda _: self.show_event())

    def build_tones(self):
        p = self.pages["Tone library"]
        self.heading(p, "Agency tone library", "Two-tone sequential and single long-tone paging. Frequencies are in Hz; timing is in seconds.")
        bar = ttk.Frame(p)
        bar.pack(fill="x", pady=(0, 12))
        for text, fn in (("Add tone set", lambda: self.edit_tone()), ("Edit selected", self.edit_selected), ("Remove selected", self.remove_tone), ("Import other application…", self.import_config), ("Tone reference…", self.tone_reference)):
            ttk.Button(bar, text=text, command=fn).pack(side="left", padx=(0, 8))
        self.tones_tree = self.table(p, ("Agency", "Type", "A / long", "B", "Minimum A / B", "Repeat window", "Enabled"), (260, 100, 90, 90, 150, 120, 80))
        self.tones_tree.bind("<Double-1>", lambda _: self.edit_selected())

    def build_recordings(self):
        p = self.pages["Recordings"]
        self.heading(p, "Dispatch recordings", "MP3 masters, source agencies, and transcripts. Replays never send external actions.")
        bar = ttk.Frame(p)
        bar.pack(fill="x", pady=(0, 12))
        for text, fn in (("▶ Play recording", self.play), ("Stop playback", self.stop_playback), ("ⓘ JSON details", self.recording_detail), ("Open recording folder", self.open_audio_folder)):
            ttk.Button(bar, text=text, command=fn).pack(side="left", padx=(0, 8))
        ttk.Button(bar, text='Clear deleted', command=lambda:self.clear_history('recordings',mode='deleted')).pack(side='right')
        ttk.Label(p, textvariable=self.history_feedback).pack(anchor='w')
        self.recordings_tree = self.table(p, ("Start (local)", "Agencies", "Duration", "Status", "File"), (130, 310, 90, 100, 300))
        self.recordings_tree.bind("<Double-1>", lambda _: self.recording_detail())

    def build_jobs(self):
        p = self.pages["Deliveries"]
        self.heading(p, "Durable delivery queue", "Retries survive restarts. Retrying an ambiguous script may repeat its external effects. Cancel releases retention protection.")
        bar = ttk.Frame(p)
        bar.pack(fill="x", pady=(0, 12))
        retry=ttk.Menubutton(bar,text='Retry selected')
        retry.pack(side='left')
        retry_menu=tk.Menu(retry,tearoff=False)
        retry_menu.add_command(label='Use original delivery settings',command=lambda:self.change_job('pending'))
        retry_menu.add_command(label='Use currently saved destination settings…',command=lambda:self.safe(self.retry_saved_settings))
        retry_menu.add_separator()
        retry_menu.add_command(label='View delivery details / related upload…',command=lambda:self.safe(self.delivery_detail))
        retry.configure(menu=retry_menu)
        ttk.Button(bar, text="Cancel selected", command=lambda: self.change_job("cancelled")).pack(side="left", padx=8)
        ttk.Button(bar,text='Details',command=lambda:self.safe(self.delivery_detail)).pack(side='left')
        ttk.Button(bar,text='Clear completed',command=lambda:self.clear_history('jobs',True)).pack(side='right')
        ttk.Button(bar,text='Clear cancelled',command=lambda:self.clear_history('jobs',mode='cancelled')).pack(side='right')
        ttk.Button(bar,text='Clear all',command=lambda:self.clear_history('jobs',mode='all')).pack(side='right')
        ttk.Label(bar,textvariable=self.history_feedback).pack(side='right',padx=8)
        self.jobs_tree = self.table(p, ("Queued (local)", "Action", "Destination", "Status", "Attempts", "Recording filename", "Last result"), (145, 85, 130, 115, 65, 330, 250))
        self.jobs_tree.bind('<Double-1>',lambda _:self.safe(self.delivery_detail))

    def build_receivers(self):
        p = self.pages["Receivers"]
        self.heading(p, "Receiver coordination", "Standalone reception works offline. Enroll remote receivers with the same group, coverage name, and tone IDs.")
        ttk.Button(p, text="Configure receiver connection…", command=self.connection_settings).pack(anchor="w", pady=(0, 12))
        self.receiver_text = tk.Text(p, bg=PANEL, fg=TEXT, font=("Segoe UI", 11), relief="flat", padx=20, pady=20, wrap="word")
        self.receiver_text.pack(fill="both", expand=True)



    def apply(self, config):
        validate(config)
        connection_change = config['coordination'] != self.engine.config['coordination'] or config['instance_id'] != self.engine.config['instance_id']
        if connection_change:
            if self.engine.running or self.engine.store.rows("SELECT id FROM jobs WHERE status='running'"):
                raise ValueError('Stop monitoring and wait for background jobs before changing receiver coordination/identity')
            self.engine.close()
            save_config(self.home, config)
            self.engine = Engine(self.home, config, self.engine.store)
            self.engine.live_playback_allowed = self.player.is_idle
            self.engine.start_workers()
        else:
            self.engine.request_settings(config,lambda c:save_config(self.home,c))
        self.config = config
        self.site_label.configure(text=config["site"])
        self.meter.gain = config['input']['gain']
        self.auto_gain.set(config['input'].get('auto_gain',False))
        self.refresh_tones()
        self.reset_editor()

    def safe(self, fn):
        try:
            fn()
        except Exception as e:
            messagebox.showerror("Tone Sentry", str(e), parent=self.root)


    def export_config(self):
        from .ftp_credentials import export_settings
        path = filedialog.asksaveasfilename(defaultextension=".json", initialfile="tonepage-settings.json")
        if path:
            Path(path).write_text(json.dumps(export_settings(self.config), indent=2), encoding="utf-8")

    def import_settings(self):
        from .settings_import import prepare_import, apply_import
        from .forms import Form
        if self.engine.running:
            raise ValueError('Stop monitoring or replay before importing settings')
        path=filedialog.askopenfilename(title='Import Tone Sentry settings',filetypes=[('Settings files','*.json'),('All files','*.*')])
        if not path:return
        original=copy.deepcopy(self.config)
        candidate,report=prepare_import(path,original)
        form=Form(self,'Review settings import')
        form.note(report)
        def apply_reviewed():
            if self.config!=original:
                raise ValueError('Settings changed while this preview was open. Close it and import the file again.')
            if self.engine.running or self.engine.store.rows("SELECT id FROM jobs WHERE status='running'"):
                raise ValueError('Stop monitoring and wait for active deliveries before applying the import')
            backup=apply_import(self.home,original,candidate,self.apply)
            messagebox.showinfo('Settings imported','Settings imported. Review destinations and re-enter FTP passwords before enabling deliveries.\n\nBackup: '+str(backup),parent=self.root)
        form.save(apply_reviewed,'Apply import')

    def refresh_tones(self):
        self.tones_tree.delete(*self.tones_tree.get_children())
        for t in self.config["tones"]:
            self.tones_tree.insert("", "end", iid=t["id"], values=(t["agency"], "Two tone" if t["kind"] == "two" else "Long tone", t["a_hz"], t.get("b_hz", "—"), f"{t['a_min']} / {t.get('b_min', '—')}", f"{t['duplicate_seconds']} s", "Yes" if t["enabled"] else "No"))

    def edit_selected(self):
        selection = self.tones_tree.selection()
        if selection:
            self.edit_tone(next(t for t in self.config["tones"] if t["id"] == selection[0]))

    def remove_tone(self):
        selected = self.tones_tree.selection()
        if selected:
            c = copy.deepcopy(self.config)
            c["tones"] = [t for t in c["tones"] if t["id"] != selected[0]]
            self.safe(lambda: self.apply(c))


    def import_config(self):
        path = filedialog.askopenfilename(filetypes=[("Other application settings", "*.cfg *.ini *.json"), ("All files", "*")])
        if not path:
            return
        def action():
            c, notes = import_other_application(Path(path), self.config)
            self.text_dialog("Import preview", "\n".join(f"{t['agency']}: {t['a_hz']} / {t.get('b_hz', 'long tone')} Hz" for t in c["tones"])+"\n\n"+"\n".join(notes), lambda: self.apply(c))
        self.safe(action)

    def text_dialog(self, title, text, apply=None):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("820x580")
        area = tk.Text(win, wrap="word", padx=20, pady=20, font=("Consolas", 10), bg=PANEL, fg=TEXT)
        area.pack(fill="both", expand=True)
        area.insert("1.0", text)
        area.configure(state="disabled")
        if apply:
            def do_apply():
                self.safe(lambda: (apply(), win.destroy()))
            ttk.Button(win, text="Apply imported tone sets", command=do_apply).pack(anchor="e", padx=20, pady=10)
        return win


    def connection_settings(self):
        win = tk.Toplevel(self.root)
        win.title("Receiver connection")
        body = ttk.Frame(win, padding=20)
        body.pack(fill="both", expand=True)
        enabled = tk.BooleanVar(value=self.config["coordination"]["enabled"])
        ttk.Checkbutton(body, text="Enable coordinated reception", variable=enabled).grid(row=0, columnspan=2, sticky="w", pady=(0, 12))
        variables = {}
        for row, (key, label) in enumerate((("url", "Coordinator URL (HTTPS remotely)"), ("group", "Receiver group"), ("coverage", "Paging system / coverage group"), ("token_env", "Token environment variable")), 1):
            ttk.Label(body, text=label).grid(row=row, column=0, sticky="w", padx=(0, 16), pady=6)
            var = tk.StringVar(value=self.config["coordination"][key])
            variables[key] = var
            ttk.Entry(body, textvariable=var, width=54).grid(row=row, column=1)
        ttk.Label(body, text="Every node records locally. Shared notifications wait during outages.\nUse matching tone IDs on the coordinator and receivers.\nEnabling enrollment permits recordings to be copied into your trusted receiver-group archive.", wraplength=600).grid(row=5, columnspan=2, sticky="w", pady=16)
        def save():
            def action():
                c = copy.deepcopy(self.config)
                c["coordination"].update({k: v.get().strip() for k, v in variables.items()})
                c["coordination"]["enabled"] = enabled.get()
                self.apply(c)
                win.destroy()
            self.safe(action)
        ttk.Button(body, text="Save connection", style="Accent.TButton", command=save).grid(row=6, column=1, sticky="e")

    def manage_integrations(self):
        win = tk.Toplevel(self.root)
        win.title("Integrations")
        win.geometry("850x510")
        body = ttk.Frame(win, padding=20)
        body.pack(fill="both", expand=True)
        self.heading(body, "Destinations & actions", "Enable each destination explicitly. Audio/transcript sharing must also be enabled on the relevant tone sets.")
        from .sharing_feedback import blocked_agencies
        sharing_label=ttk.Label(body,wraplength=680)
        sharing_label.pack(fill='x',pady=(0,6))
        def review_sharing():
            from .forms import Form
            panel=Form(self,'Review tone sharing')
            panel.note('These enabled tone sets match an enabled destination requiring external sharing, but their sharing permission is off. Review each tone; nothing is enabled automatically. Close and reopen this list after saving changes.')
            for tone in blocked_agencies(self.config):
                panel.button(tone['agency'],lambda t=tone:self.edit_tone(t))
        ttk.Button(body,text='Review tone sharing…',command=lambda:self.safe(review_sharing)).pack(anchor='w',pady=(0,8))
        bar = ttk.Frame(body)
        bar.pack(fill="x", pady=(0, 12))
        tree = self.table(body, ("Name", "Type", "Scope", "Enabled"), (230, 150, 120, 100))
        def refresh():
            tree.delete(*tree.get_children())
            blocked=blocked_agencies(self.config)
            sharing_label.configure(text=('External sharing is OFF for: '+', '.join(t['agency'] for t in blocked)+'. Matching audio/transcript deliveries will be skipped.') if blocked else 'No configured tone-sharing permission conflicts found.')
            for d in self.config["integrations"]:
                tree.insert("", "end", iid=d["id"], values=(d.get("name") or d["id"], d["kind"], d.get("scope", "shared"), "Yes" if d.get("enabled") else "No"))
        def edit():
            if tree.selection():
                self.edit_integration(next(d for d in self.config["integrations"] if d["id"] == tree.selection()[0]), refresh)
        def remove():
            if tree.selection():
                c = copy.deepcopy(self.config)
                c["integrations"] = [d for d in c["integrations"] if d["id"] != tree.selection()[0]]
                self.safe(lambda: (self.apply(c), refresh()))
        ttk.Button(bar, text="Add destination", command=lambda: self.edit_integration(None, refresh)).pack(side="left")
        ttk.Button(bar, text="Edit selected", command=edit).pack(side="left", padx=8)
        ttk.Button(bar, text="Remove selected", command=remove).pack(side="left")
        tree.bind("<Double-1>", lambda _: edit())
        refresh()



    def toggle(self):
        self.safe(self.engine.stop if self.engine.running else self.engine.start)

    def replay_path(self, path):
        if self.engine.running:
            raise ValueError("Stop monitoring before replay")
        self.engine.stop_event.clear()
        self.engine.running = True
        def work():
            try:
                self.engine.replay(Path(path))
            except Exception as e:
                error = str(e)
                self.root.after(0, lambda: messagebox.showerror("Replay", error))
            finally:
                self.engine.running = False
        threading.Thread(target=work, daemon=True).start()

    def replay(self):
        path = filedialog.askopenfilename(filetypes=[("16-bit PCM WAV", "*.wav")])
        if path:
            self.safe(lambda: self.replay_path(path))

    def demo(self):
        def action():
            from .demo import write_demo
            self.replay_path(write_demo(self.home / "demo.wav", self.config))
        self.safe(action)

    def selected_recording(self):
        ids = self.recordings_tree.selection()
        rows = self.engine.store.rows("SELECT * FROM recordings WHERE id=?", (ids[0],)) if ids else []
        return rows[0] if rows else None

    def stop_playback(self):
        self.player.stop()
        self.engine.live_audio.stop()

    def play(self):
        self.play_recording_row(self.selected_recording())

    def play_recording_row(self, row):
        def action():
            if not row or row['status'] != 'complete' or not row['path'] or not Path(row['path']).is_file():
                raise ValueError('No completed audio is available for this selection. It may still be recording, have been purged, or be an event without audio.')
            if not self.engine.live_audio.stop(wait=True):
                raise ValueError('Live audio output is still stopping. Try playback again shortly.')
            self.player.play(Path(row['path']),copy.deepcopy(self.config))
        self.safe(action)

    def play_event(self):
        ids = self.events_tree.selection()
        events = self.engine.store.rows('SELECT data FROM events WHERE id=?', (ids[0],)) if ids else []
        event = json.loads(events[0]['data']) if events else {}
        rows = self.engine.store.rows('SELECT * FROM recordings WHERE id=?', (event.get('recording_id'),))
        self.play_recording_row(rows[0] if rows else None)

    def recording_detail(self):
        row = self.selected_recording()
        if row:
            transcripts = self.engine.store.rows("SELECT text FROM transcripts WHERE recording_id=?", (row["id"],))
            data = dict(recording=json.loads(row['data']), status=row['status'], transcripts=[t['text'] for t in transcripts])
            self.text_dialog("Recording details", json.dumps(data, indent=2))

    def show_event(self):
        ids = self.events_tree.selection()
        if ids:
            rows = self.engine.store.rows("SELECT data FROM events WHERE id=?", (ids[0],))
            if rows:
                self.text_dialog("Event details", json.dumps(json.loads(rows[0]["data"]), indent=2))

    def change_job(self, status):
        ids = self.jobs_tree.selection()
        if ids:
            with self.engine.store.transaction() as db:
                db.execute("UPDATE jobs SET status=?,due=0,attempts=0 WHERE id=? AND status NOT IN ('running','done')", (status, ids[0]))

    def delivery_detail(self,job_id=None):
        from .delivery_status import display_status,related_upload
        from .message_templates import filename_for
        from .forms import Form
        if job_id is None:
            selected=self.jobs_tree.selection()
            if not selected:return
            job_id=selected[0]
        rows=self.engine.store.rows('SELECT * FROM jobs WHERE id=?',(job_id,))
        if not rows:raise ValueError('Delivery no longer exists')
        row=rows[0];payload=json.loads(row['payload'])
        destination=payload.get('destination',{})
        name=next((d.get('name',d['id']) for d in self.config['integrations'] if d['id']==destination.get('id')),destination.get('name',destination.get('id','Local engine')))
        form=Form(self,'Delivery details')
        form.note('Destination: '+name+'\nAction: '+row['kind']+'\nStatus: '+display_status(self.engine.store,row)+'\nAttempts: '+str(row['attempts'])+'\nRecording: '+(filename_for(payload.get('event',{})) or 'Not available')+'\nLast result: '+(row['error'] or 'No error recorded'))
        if row['kind']=='webhook' and destination.get('wait_for_ftp'):
            upload=related_upload(self.engine.store,row)
            if upload:
                form.note('Related FTP upload: '+display_status(self.engine.store,upload))
                form.button('Open related upload',lambda:self.safe(lambda:self.delivery_detail(upload['id'])))
            else:form.note('The required upload was not queued. Check its enabled state, scope, tone filter and sharing permission.')
            form.note('If the upload failed, retry it first. Once it is completed, retry this notification. Ready to retry requires an operator action; Ready to send proceeds automatically.')
        def refresh():
            form.win.destroy()
            self.delivery_detail(job_id)
        form.button('Refresh details',lambda:self.safe(refresh))
        ttk.Button(form.footer,text='Close',command=form.win.destroy).pack(side='right')

    def retry_saved_settings(self):
        from .delivery_retry import refreshed_payload,retry_with_settings
        ids=self.jobs_tree.selection()
        if not ids:return
        rows=self.engine.store.rows('SELECT * FROM jobs WHERE id=?',(ids[0],))
        if not rows:raise ValueError('Delivery no longer exists')
        reviewed=copy.deepcopy(self.config)
        payload=refreshed_payload(dict(rows[0]),reviewed)
        destination=payload['destination']
        text=('Retry this delivery using the currently saved settings for '+destination.get('name',destination['id'])+'?\n\n'
              'This uses its saved credentials, server address and message template. The recording and delivery ID stay the same. Unsaved form edits are not included. The previous attempt may already have reached the destination.')
        if rows[0]['kind']=='script':text+='\n\nThis executes the configured script again and can repeat its effects.'
        if not messagebox.askyesno('Retry with saved settings',text,parent=self.root):return
        if reviewed!=self.config:raise ValueError('Settings changed during review; try again')
        retry_with_settings(self.engine.store,ids[0],reviewed)
        self.history_feedback.set('Delivery queued using saved destination settings.')

    def update_table(self, tree, items):
        selection = tree.selection()
        existing = set(tree.get_children())
        for iid, values in items:
            if iid in existing:
                tree.item(iid, values=values)
                existing.remove(iid)
            else:
                tree.insert("", "end", iid=iid, values=values)
        for iid in existing:
            tree.delete(iid)
        for index, (iid, _) in enumerate(items):
            tree.move(iid, "", index)
        if selection and tree.exists(selection[0]):
            tree.selection_set(selection)

    def refresh(self):
        self.refresh_discovery()
        self.pause_button.configure(text='Resume detections' if self.engine.detection_paused else 'Pause detections')
        self.update_monitor_label()
        self.status.configure(text=('Detection paused · ' if self.engine.detection_paused else '')+self.engine.status+f"  ·  Dropped blocks: {self.engine.dropped}"+'  ·  '+self.engine.settings_status)

        store = self.engine.store
        self.card_values["RECEIVER"].configure(text="Paused" if self.engine.detection_paused else "Recording" if self.engine.active else "Listening" if self.engine.running else "Standby")
        self.card_values["ENABLED TONE SETS"].configure(text=sum(t["enabled"] for t in self.config["tones"]))
        self.card_values["RECORDINGS"].configure(text=store.rows("SELECT COUNT(*) n FROM recordings WHERE status='complete'")[0]["n"])
        self.card_values["PENDING ACTIONS"].configure(text=store.rows("SELECT COUNT(*) n FROM jobs WHERE status IN ('pending','running')")[0]["n"])
        events = []
        for row in store.visible_history("events", 100):
            d = json.loads(row["data"])
            classification = "Replay" if d.get("synthetic") else "Test" if d.get("test") else "Repeat" if d.get("duplicate") else ""
            events.append((row["id"], (datetime.fromtimestamp(row["at"]).strftime("%H:%M:%S"), row["type"].replace("_", " "), d.get('message') or ", ".join(d.get("agencies", [])) or d.get("destination", ""), classification)))
        self.update_table(self.events_tree, events)
        records = []
        for row in store.visible_history("recordings", 200):
            d = json.loads(row["data"])
            records.append((row["id"], (datetime.fromtimestamp(row["at"]).strftime("%m/%d %H:%M:%S"), ", ".join(d.get("agencies", [])), f"{(row['end'] or row['at'])-row['at']:.1f}s", row["status"], Path(row["path"]).name if row["path"] else "")))
        self.update_table(self.recordings_tree, records)
        jobs = []
        from .delivery_status import display_status
        from .message_templates import filename_for
        for row in store.visible_history("jobs", 200):
            d = json.loads(row["payload"])
            jobs.append((row["id"], (datetime.fromtimestamp(row['created']).strftime('%m/%d %H:%M:%S'),row["kind"], next((x.get("name") or x["id"] for x in self.config["integrations"] if x["id"]==d.get("destination",{}).get("id")), d.get("destination",{}).get("name") or d.get("destination",{}).get("id","Local engine")), display_status(store,row), row["attempts"],filename_for(d.get('event',{})), row["error"] or "")))
        self.update_table(self.jobs_tree, jobs)
        coord = self.config["coordination"]
        info = f"SITE: {self.config['site']}\nINSTANCE ID: {self.config['instance_id']}\nMODE: {'Coordinated receiver' if coord['enabled'] else 'Standalone'}\n"
        info += f"COORDINATOR STATUS: {self.engine.client.status if self.engine.client else 'Not enabled'}\n\nGROUP / COVERAGE\n{coord['group']} / {coord['coverage']}\n\n"
        info += "OUTAGE POLICY\nLocal reception continues. Shared deliveries wait for the coordinator.\n\nENROLLED RECEIVERS (last heartbeat snapshot)\n"
        roster = store.get("receiver_roster", [])
        if not roster:
            info += "No receiver roster received. Configure enrollment in Settings."
        for node in roster:
            info += f"\n{node['site']} · {node['state']} · {node['coverage']}\n  {node.get('health', {}).get('status', 'No audio status')} · clock offset {node['clock_offset']:+.1f}s\n"
        self.receiver_text.configure(state="normal")
        self.receiver_text.delete("1.0", "end")
        self.receiver_text.insert("1.0", info)
        self.receiver_text.configure(state="disabled")
        self.root.after(1000, self.refresh)

    def close(self):
        if hasattr(self, 'receiver_controller'):
            self.receiver_controller.close()
            if self.web_timer is not None:
                self.root.after_cancel(self.web_timer)
            self.web_console.stop()
        if self.startup_timer is not None:
            self.root.after_cancel(self.startup_timer)
            self.startup_timer = None
        self.player.close()
        if self.gain_save_timer: self.save_live_gain()
        self.engine.close()
        self.root.destroy()


def launch(home):
    root = tk.Tk()
    app = Application(root, home)
    app.schedule_startup_monitoring()
    root.mainloop()
