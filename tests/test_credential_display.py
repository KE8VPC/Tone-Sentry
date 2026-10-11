import tkinter as tk
from tkinter import ttk
from tonepage.gui import Application


def test_password_reference_fields_are_masked_and_values_preserved(tmp_path):
    root=tk.Tk();root.withdraw();app=Application(root,tmp_path)
    def descendants(widget):
        for child in widget.winfo_children():
            yield child
            yield from descendants(child)
    try:
        original=dict(id='ftp-display',kind='ftp',enabled=False,host='example.invalid',
                      password_env='TEST_FTP_SECRET',smtp_password_env='TEST_SMTP_SECRET')
        app.edit_integration(original,lambda:None)
        win=next(w for w in root.winfo_children() if isinstance(w,tk.Toplevel))
        for label_text,expected in [('FTP password environment variable','TEST_FTP_SECRET'),
                                    ('SMTP password environment variable','TEST_SMTP_SECRET')]:
            label=next(w for w in descendants(win) if isinstance(w,ttk.Label) and w.cget('text')==label_text)
            entry=next(w for w in label.master.winfo_children() if isinstance(w,ttk.Entry)
                       and str(w.cget('textvariable')) and w.get()==expected)
            assert entry.cget('show')=='*'
            entry.delete(0,'end');entry.insert(0,expected+'_EDITED')
            assert entry.get()==expected+'_EDITED' and entry.cget('show')=='*'
        assert original['password_env']=='TEST_FTP_SECRET'
        assert not app.config['integrations']
    finally:app.close()
