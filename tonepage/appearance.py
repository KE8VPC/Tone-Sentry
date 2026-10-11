"""Persistent appearance, independent of receiver and delivery lifecycles."""
import os
import tkinter as tk
from tkinter import ttk
from importlib.resources import files

PALETTES = {
    'Light': dict(bg='#eef2f6', panel='#ffffff', text='#15283e', muted='#627187', border='#dce4ed', selected='#d4e7ef', heading='#e3eaf1'),
    'Dark': dict(bg='#111b29', panel='#1c2a3c', text='#eef4fa', muted='#a8bad0', border='#40546b', selected='#325773', heading='#25384e'),
}


class Appearance:
    def __init__(self, root, theme):
        self.root = root
        self.theme = theme
        self.icon = tk.PhotoImage(master=root, file=str(files('tonepage').joinpath('resources/app-icon.png')))
        self.icon_path = str(files('tonepage').joinpath('resources/app-icon.ico'))
        root.iconphoto(True, self.icon)
        self.set_icon(root)
        root.bind('<Map>', self.mapped, add='+')
        self.apply(theme)

    def set_icon(self, window):
        if os.name == 'nt':
            # Explicitly set this window, as well as the default for future dialogs.
            window.iconbitmap(self.icon_path, default=self.icon_path)
        else:
            window.iconphoto(False, self.icon)

    def mapped(self, event):
        self.widgets(event.widget)
        if isinstance(event.widget, (tk.Tk, tk.Toplevel)):
            self.set_icon(event.widget)

    def apply(self, theme):
        self.theme = theme
        p = PALETTES[theme]
        style = ttk.Style(self.root)
        style.configure('.', background=p['bg'], foreground=p['text'], fieldbackground=p['panel'],
                        bordercolor=p['border'], lightcolor=p['border'], darkcolor=p['border'],
                        selectbackground=p['selected'], selectforeground=p['text'], insertcolor=p['text'])
        style.configure('TCombobox', arrowcolor=p['text'])
        style.configure('TSpinbox', arrowcolor=p['text'])
        for name in ('TFrame', 'TLabel', 'TCheckbutton', 'TRadiobutton', 'TNotebook'):
            style.configure(name, background=p['bg'], foreground=p['text'])
        for name in ('TButton', 'TEntry', 'TSpinbox', 'TCombobox', 'Treeview'):
            style.configure(name, background=p['panel'], fieldbackground=p['panel'], foreground=p['text'])
            style.map(name, foreground=[('disabled', p['muted']), ('selected', p['text'])],
                      fieldbackground=[('readonly', p['panel']), ('disabled', p['bg'])],
                      background=[('selected', p['selected']), ('active', p['heading']), ('disabled', p['bg'])])
        style.configure('Treeview.Heading', background=p['heading'], foreground=p['text'])
        style.map('Treeview.Heading', background=[('active', p['selected'])])
        style.configure('TNotebook.Tab', background=p['heading'], foreground=p['muted'], padding=(4, 6))
        style.map('TNotebook.Tab', background=[('selected', p['panel']), ('active', p['selected'])], foreground=[('selected', p['text'])],padding=[('selected',(4,6)),('!selected',(4,6))])
        for name in ('TCheckbutton', 'TRadiobutton'):
            style.map(name, background=[('active', p['heading'])], foreground=[('disabled', p['muted'])],
                      indicatorbackground=[('selected', '#c95818'), ('!selected', p['panel'])])
        style.configure('Accent.TButton', background='#c95818', foreground='white')
        style.map('Accent.TButton', background=[('active', '#a44612')], foreground=[('disabled', p['muted']), ('!disabled', 'white')])
        style.configure('Horizontal.TProgressbar', troughcolor=p['heading'])
        for key, value in [('background', p['panel']), ('foreground', p['text']), ('selectBackground', p['selected']), ('selectForeground', p['text'])]:
            self.root.option_add('*TCombobox*Listbox.'+key, value)
        self.widgets(self.root)

    def widgets(self, widget):
        p = PALETTES[self.theme]
        if not isinstance(widget, ttk.Widget):
            options = widget.keys()
            if not hasattr(widget, '_appearance_roles'):
                roles = {}
                original = {v: k for k, v in PALETTES['Light'].items()}
                for key in ('background', 'foreground', 'highlightbackground'):
                    if key in options:
                        value = str(widget.cget(key))
                        # The navy product header deliberately stays navy in both themes.
                        if key == 'background' and value == '#15283e':
                            continue
                        if value in original:
                            roles[key] = original[value]
                if isinstance(widget, (tk.Tk, tk.Toplevel, tk.Canvas)):
                    roles['background'] = 'bg'
                if isinstance(widget, (tk.Text, tk.Listbox, tk.Entry, tk.Menu)):
                    roles.update(background='panel', foreground='text')
                    for key, role in [('insertbackground','text'), ('selectbackground','selected'), ('selectforeground','text'), ('disabledforeground','muted'), ('activebackground','selected'), ('activeforeground','text')]:
                        if key in options: roles[key] = role
                widget._appearance_roles = roles
            widget.configure(**{key:p[role] for key,role in widget._appearance_roles.items()})
        elif isinstance(widget, ttk.Label) and str(widget.cget('foreground')) in ('#627187', '#a8bad0'):
            widget.configure(foreground=p['muted'])
        for child in widget.winfo_children():
            self.widgets(child)
