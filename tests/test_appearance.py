import tkinter as tk
from tkinter import ttk
from tonepage.config import load_config
from tonepage.gui import Application


def test_theme_switch_preserves_running_engine_and_new_dialogs(tmp_path):
    root = tk.Tk(); root.withdraw()
    app = Application(root, tmp_path)
    try:
        engine = app.engine
        engine.running = True
        app.change_theme('Dark')
        assert app.engine is engine and engine.running
        assert load_config(tmp_path)['ui']['theme'] == 'Dark'
        assert root.cget('background') == '#111b29'
        app.text_dialog('Theme check', 'Readable JSON and help')
        win = next(w for w in root.winfo_children() if isinstance(w,tk.Toplevel))
        root.update()
        app.appearance.widgets(win)
        text = next(w for w in win.winfo_children() if isinstance(w,tk.Text))
        assert text.cget('background') == '#1c2a3c' and text.cget('foreground') == '#eef4fa'
        app.change_theme('Light')
        assert text.cget('background') == '#ffffff'
        assert app.engine is engine and engine.running
        def descendants(widget):
            for child in widget.winfo_children():
                yield child
                yield from descendants(child)
        assert any(isinstance(w,ttk.Label) and w.cget('text')=='Created By:  Mike Beam' for w in descendants(app.pages['About']))
    finally:
        app.engine.running = False
        app.close()
