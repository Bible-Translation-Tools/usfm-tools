# -*- coding: utf-8 -*-
# GUI interface for USFM to USX file conversion.
#

from tkinter import *
from tkinter import ttk
from tkinter import font
from tkinter import filedialog
from idlelib.tooltip import Hovertip
import g_step
import os

stepname = 'Paratext2Usfm'   # equals the main class name in this module

class Paratext2Usfm(g_step.Step):
    def __init__(self, mainframe, mainapp):
        super().__init__(mainframe, mainapp, stepname, "Rename Paratext SFM files")
        self.frame = Paratext2Usfm_Frame(mainframe, self)
        self.frame.grid(row=1, column=0, sticky="nsew")

    def name(self):
        return stepname

    def onExecute(self, values):
        self.enablebutton(2, False)
        self.mainapp.execute_script("paratext2usfm", 1)
        self.frame.clear_messages()

    # Called by the main app.
    def onScriptEnd(self, status: str):
        if status:
            self.frame.show_progress(status)
        # self.frame.show_progress("\nConversion complete")
        self.frame.onScriptEnd()

class Paratext2Usfm_Frame(g_step.Step_Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        self.ptx_dir = StringVar()
        self.target_dir = StringVar()
        self.filename = StringVar()
        for var in (self.ptx_dir, self.target_dir, self.filename):
            var.trace_add("write", self._onChangeEntry)

        self.grid_columnconfigure(4, weight=1)
        self.grid_columnconfigure(5, weight=0)

        ptx_dir_label = ttk.Label(self, text="Paratext project folder with .SFM files:", width=25)
        ptx_dir_label.grid(row=3, column=1, sticky=W, pady=2)
        ptx_dir_entry = ttk.Entry(self, width=55, textvariable=self.ptx_dir)
        ptx_dir_entry.grid(row=3, column=2, columnspan=3, sticky=W)
        ptx_dir_find = ttk.Button(self, text="...", width=2, command=self._onFindPtxDir)
        ptx_dir_find.grid(row=3, column=5, sticky=W)

        target_dir_label = ttk.Label(self, text="Location for .usfm files:", width=25)
        target_dir_label.grid(row=4, column=1, sticky=W, pady=2)
        target_dir_entry = ttk.Entry(self, width=55, textvariable=self.target_dir)
        target_dir_entry.grid(row=4, column=2, columnspan=3, sticky=W)
        target_dir_Tip = Hovertip(target_dir_entry, hover_delay=1000,
                text="Folder for .usfm files. It will be created if it doesn't exist.")
        target_dir_find = ttk.Button(self, text="...", width=2, command=self._onFindTargetDir)
        target_dir_find.grid(row=4, column=5, sticky=W)

        file_label = ttk.Label(self, text="File name:", width=25)
        file_label.grid(row=5, column=1, sticky=W, pady=2)
        file_entry = ttk.Entry(self, width=19, textvariable=self.filename)
        file_entry.grid(row=5, column=2, sticky=W)
        file_Tip = Hovertip(file_entry, hover_delay=500,
             text="Leave filename blank to convert all .SFM files in the project.")
        file_find = ttk.Button(self, text="...", width=2, command=self._onFindFile)
        file_find.grid(row=5, column=3, sticky=W)
        
    def show_values(self, values):
        self.values = values
        self.ptx_dir.set(values.get('paratext_dir', fallback=""))
        self.target_dir.set(values.get('target_dir', fallback=""))
        self.filename.set(values.get('filename', fallback=""))

        # Create buttons
        self.controller.showbutton(1, "<<<", cmd=self._onBack)
        self.controller.showbutton(2, "CONVERT", tip="Copy SFM files, rename, and correct line endings.",
                                   cmd=self._onExecute)
        self.controller.showbutton(3, "Ptx folder",
                                   tip="Open the paratext project folder.", cmd=self._onOpenPtxDir)
        self.controller.showbutton(4, "Usfm folder", cmd=self._onOpenTargetDir)
        self.controller.hidebutton(5)
        self._set_button_status()

    def onScriptEnd(self):
        self.message_area['state'] = DISABLED   # prevents insertions to message area
        self._set_button_status()

    # Copies current values from GUI into self.values dict, and calls mainapp to save
    # them to the configuration file.
    def _save_values(self):
        self.values['paratext_dir'] = self.ptx_dir.get()
        self.values['target_dir'] = self.target_dir.get()
        self.values['filename'] = self.filename.get()
        self.controller.mainapp.save_values(stepname, self.values)
        self._set_button_status()

    def _onFindPtxDir(self, *args):
        if not self.ptx_dir.get() and os.name == 'nt':
            ptxdir = os.path.expanduser("~/Documents/ParatextProjects/.")
            if not os.path.isdir(ptxdir):
                ptxdir = ""
            self.ptx_dir.set(ptxdir)
        self.controller.askdir(self.ptx_dir)
    def _onOpenPtxDir(self, *args):
        os.startfile(self.ptx_dir.get())

    def _onFindTargetDir(self, *args):
        self.controller.askdir(self.target_dir)
    def _onOpenTargetDir(self, *args):
        os.startfile(self.target_dir.get())

    def _onFindFile(self, *args):
        path = filedialog.askopenfilename(initialdir=self.ptx_dir.get(), title = "Select file",
                                           filetypes=[('Usfm file', '*.SFM')])
        if path:
            self.filename.set(os.path.basename(path))
        
    def _onChangeEntry(self, *args):
        self._set_button_status()

    def _set_button_status(self):
        ptx_ok = os.path.isdir(self.ptx_dir.get())
        self.controller.enablebutton(3, ptx_ok)

        target_dir = self.target_dir.get()
        self.controller.enablebutton(4, os.path.isdir(target_dir))

        if ptx_ok and target_dir and self.filename.get():
            path = os.path.join(self.ptx_dir.get(), self.filename.get())
            ptx_ok = os.path.isfile(path)
        self.controller.enablebutton(2, ptx_ok and target_dir)
