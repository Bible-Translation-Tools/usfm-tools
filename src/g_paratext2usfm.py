# -*- coding: utf-8 -*-
# GUI interface for USFM to USX file conversion.
#

from tkinter import ttk
from tkinter import StringVar, W, DISABLED
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

    def onExecute(self):
        self.enablebutton(2, False)
        self.mainapp.execute_script("paratext2usfm", 1)
        self.frame.clear_messages()

class Paratext2Usfm_Frame(g_step.Step_Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        self.ptx_dir = StringVar()
        self.work_dir = StringVar()
        self.filename = StringVar()
        for var in (self.ptx_dir, self.work_dir, self.filename):
            var.trace_add("write", self._onChangeEntry)

        self.grid_columnconfigure(4, weight=1)
        self.grid_columnconfigure(5, weight=0)

        ptx_dir_label = ttk.Label(self, text="Paratext project folder with .SFM files:", width=25)
        ptx_dir_label.grid(row=3, column=1, sticky=W, pady=2)
        ptx_dir_entry = ttk.Entry(self, width=55, textvariable=self.ptx_dir)
        ptx_dir_entry.grid(row=3, column=2, columnspan=3, sticky=W)
        ptx_dir_find = ttk.Button(self, text="...", width=2, command=self._onFindPtxDir)
        ptx_dir_find.grid(row=3, column=5, sticky=W)

        work_dir_label = ttk.Label(self, text="Location for .usfm files:", width=25)
        work_dir_label.grid(row=4, column=1, sticky=W, pady=2)
        work_dir_entry = ttk.Entry(self, width=55, textvariable=self.work_dir)
        work_dir_entry.grid(row=4, column=2, columnspan=3, sticky=W)
        work_dir_Tip = Hovertip(work_dir_entry, hover_delay=1000,
                text="Folder for .usfm files. It will be created if it doesn't exist.")
        work_dir_find = ttk.Button(self, text="...", width=2, command=self._onFindWorkDir)
        work_dir_find.grid(row=4, column=5, sticky=W)

        file_label = ttk.Label(self, text="File name:", width=25)
        file_label.grid(row=5, column=1, sticky=W, pady=2)
        file_entry = ttk.Entry(self, width=19, textvariable=self.filename)
        file_entry.grid(row=5, column=2, sticky=W)
        file_Tip = Hovertip(file_entry, hover_delay=500,
             text="Leave filename blank to convert all .SFM files in the project.")
        file_find = ttk.Button(self, text="...", width=2, command=self._onFindFile)
        file_find.grid(row=5, column=3, sticky=W)

    # Temporary function, until "target_dir" is fully retired.
    def getWorkDirConfigValue(self):
        workdir = self.getOption('work_dir')
        if not workdir:
            workdir = self.getOption('target_dir')  # the old name
        return workdir

    def show_values(self):
        self.ptx_dir.set(self.getOption('paratext_dir'))
        self.work_dir.set(self.getWorkDirConfigValue())
        self.filename.set(self.getOption('filename'))

        # Create buttons
        self.controller.showbutton(1, "<<<", self._onBack)
        self.controller.showbutton(2, "CONVERT", self._onExecute, tip="Copy SFM files, rename, and correct line endings.")
        self.controller.showbutton(3, "Ptx folder", self._onOpenPtxDir, tip="Open the paratext project folder.")
        self.controller.showbutton(4, "Usfm folder", self._onOpenWorkDir)
        self.controller.hidebutton(5)
        self._set_button_status()

    def onScriptEnd(self):
        self.message_area['state'] = DISABLED   # prevents insertions to message area
        self._set_button_status()

    # Returns the current entered values in a dict.
    def get_entered_values(self):
        values = {}
        values['paratext_dir'] = self.ptx_dir.get()
        values['work_dir'] = self.work_dir.get()
        values['filename'] = self.filename.get()
        return values

    def _onFindPtxDir(self, *args):
        if not self.ptx_dir.get() and os.name == 'nt':
            ptxdir = os.path.expanduser("~/Documents/ParatextProjects/.")
            if not os.path.isdir(ptxdir):
                ptxdir = ""
            self.ptx_dir.set(ptxdir)
        self.controller.askdir(self.ptx_dir)
    def _onOpenPtxDir(self, *args):
        os.startfile(self.ptx_dir.get())

    def _onFindWorkDir(self, *args):
        self.controller.askdir(self.work_dir)
    def _onOpenWorkDir(self, *args):
        os.startfile(self.work_dir.get())

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

        work_dir = self.work_dir.get()
        self.controller.enablebutton(4, os.path.isdir(work_dir))

        if ptx_ok and work_dir and self.filename.get():
            path = os.path.join(self.ptx_dir.get(), self.filename.get())
            ptx_ok = os.path.isfile(path)
        self.controller.enablebutton(2, ptx_ok and work_dir)
