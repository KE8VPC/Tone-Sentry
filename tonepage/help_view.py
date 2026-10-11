"""Readable, navigable offline operator guide."""
import tkinter as tk
from tkinter import ttk
from importlib.resources import files


def show_help(root):
    win = tk.Toplevel(root)
    win.title('Help & how to use Tone Sentry')
    win.geometry(f'{min(1060,root.winfo_screenwidth()-60)}x{min(740,root.winfo_screenheight()-100)}')
    nav = ttk.Frame(win, padding=12)
    nav.pack(side='left',fill='y')
    ttk.Label(nav,text='Sections',font=('Segoe UI',12,'bold')).pack(anchor='w',pady=(0,8))
    listing=tk.Listbox(nav,width=25,font=('Segoe UI',11),exportselection=False)
    nav_scroll=ttk.Scrollbar(nav,command=listing.yview)
    nav_scroll.pack(side='right',fill='y')
    listing.configure(yscrollcommand=nav_scroll.set)
    listing.pack(side='left',fill='both',expand=True)
    scroll=ttk.Scrollbar(win)
    scroll.pack(side='right',fill='y')
    text=tk.Text(win,wrap='word',font=('Segoe UI',11),padx=20,pady=18,spacing1=4,spacing3=8,
                 yscrollcommand=scroll.set)
    text.pack(fill='both',expand=True)
    scroll.configure(command=text.yview)
    text.tag_configure('heading',font=('Segoe UI',13,'bold'),underline=True,spacing1=18,spacing3=10)
    marks=[]
    navigation={
        'TONE SENTRY — GETTING STARTED':'Quick start',
        'INSTALLATION AND DATA FOLDERS':'Install & data folders',
        'SHARED METERS AND AUTO GAIN':'Meters & auto gain',
        'RECORDING, STACKED PAGES & DUPLICATES':'Recording & repeats',
        'CHOOSING PLAYBACK SPEAKERS OR HEADPHONES':'Playback device',
        'AUDIO FILES AND HISTORY CONTROLS':'Files & history',
        'SHARED FILENAME AND MESSAGE TEMPLATES':'Message templates',
        'CUSTOM DISCORD MESSAGE FORMAT':'Discord message format',
        'EMAIL WITH MP3 ATTACHMENTS':'Email with MP3s',
        'TESTING AN FTP DESTINATION':'Test FTP connection',
        'MULTIPLE RECEIVERS ON ONE COMPUTER':'Multiple local receivers',
        'REGISTRATION — DEVELOPMENT EDITION':'Registration',
    }
    guide=files('tonepage').joinpath('resources/usage-guide.md').read_text(encoding='utf-8')
    for line in guide.splitlines():
        heading = bool(line.strip()) and len(line)<130 and line==line.upper() and any(c.isalpha() for c in line)
        if heading:
            mark='section'+str(len(marks))
            text.mark_set(mark,'end-1c');text.mark_gravity(mark,'left');marks.append(mark)
            listing.insert('end',navigation.get(line,line.title()))
        text.insert('end',line+'\n',('heading',) if heading else ())
    text.configure(state='disabled')
    def jump(_=None):
        if listing.curselection():text.see(marks[listing.curselection()[0]])
    listing.bind('<<ListboxSelect>>',jump)
    return win
