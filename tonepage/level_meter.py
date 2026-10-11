"""Live post-gain peak meter with an overlaid gain handle."""
import math
import tkinter as tk
from tkinter import ttk


def dbfs(peak):
    return max(-60., min(0., 20*math.log10(max(peak, .001))))


class LevelMeter(ttk.Frame):
    def __init__(self, parent, gain, changed):
        super().__init__(parent)
        self.changed = changed
        self.gain = float(gain)
        self.peak = 0.
        self.overload = False
        self.canvas = tk.Canvas(self, height=42, highlightthickness=0, takefocus=True)
        self.canvas.pack(fill='x')
        self.controls = ttk.Frame(self)
        self.controls.pack(fill='x')
        self.caption = ttk.Label(self.controls,font=('Segoe UI',9))
        self.caption.pack(side='left')
        self.canvas.bind('<Configure>', lambda _:self.draw())
        self.canvas.bind('<Button-1>', self.drag)
        self.canvas.bind('<B1-Motion>', self.drag)
        self.canvas.bind('<Left>', lambda _:self.set_gain(max(.01,self.gain/1.05)))
        self.canvas.bind('<Right>', lambda _:self.set_gain(min(100,self.gain*1.05)))
        self.draw()

    def add_controls(self,auto_var,auto_changed,save,feedback,parent=None):
        row=ttk.Frame(parent if parent is not None else self.controls)
        row.pack(side='top' if parent is not None else 'right',fill='x')
        ttk.Button(row,text='Reset gain',command=lambda:self.set_gain(1.)).pack(side='left',padx=(0,4))
        ttk.Checkbutton(row,text='Auto gain',variable=auto_var,command=auto_changed).pack(side='left')
        if parent is not None:
            ttk.Button(row,text='Save meter',command=save).pack(side='left',padx=(6,0))
            ttk.Label(parent,textvariable=feedback).pack(anchor='w')
        else:
            ttk.Button(row,text='Save meter settings',command=save).pack(side='left',padx=10)
            ttk.Label(row,textvariable=feedback).pack(side='left')

    def set_gain(self, gain):
        self.gain = round(max(.01,min(100,gain)),4)
        self.changed(self.gain)
        self.draw()

    def drag(self, event):
        self.canvas.focus_set()
        ratio = max(0,min(1,(event.x-8)/max(1,self.canvas.winfo_width()-16)))
        self.set_gain(10**(ratio*4-2))

    def display(self, peak, overload):
        self.peak, self.overload = peak, overload
        self.draw()

    def draw(self):
        c = self.canvas
        c.delete('all')
        width = max(80,c.winfo_width())-16
        fraction = (dbfs(self.peak)+60)/60
        for lo,hi,color,dim in [(0,.8,'#218447','#284737'),(.8,.95,'#d49b16','#665b35'),(.95,1,'#d53030','#663535')]:
            c.create_rectangle(8+lo*width,9,8+hi*width,31,fill=dim,outline='')
            if fraction>lo:
                c.create_rectangle(8+lo*width,9,8+min(hi,fraction)*width,31,fill=color,outline='')
        position = 8+fraction*width
        c.create_line(position,8,position,33,fill='white',width=3)
        handle = 8+(math.log10(max(.01,self.gain))+2)/4*width
        c.create_polygon(handle-7,3,handle+7,3,handle+7,35,handle,40,handle-7,35,fill='#c95818',outline='white',width=2,tags='gain_handle')
        state = 'CLIPPING — lower input' if self.overload else 'HIGH' if dbfs(self.peak)>=-3 else 'Approaching limit' if dbfs(self.peak)>=-12 else 'Normal' if self.peak>.001 else 'Quiet'
        self.caption.configure(text=f'Input gain {self.gain:.2f}× · Peak {dbfs(self.peak):.1f} dBFS · {state}')
