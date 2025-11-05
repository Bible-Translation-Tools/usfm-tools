# -*- coding: utf-8 -*-
# Implements Plaintext2Usfm and Plaintext2Usfm_Frame, which are the controller and frame
# for operating the plaintxt2usfm.py script.
# GUI interface for merging BTTW text files and converting to USFM

from tkinter import ttk
from tkinter import StringVar, W, DISABLED
from tkinter import filedialog
from idlelib.tooltip import Hovertip
import os
import g_util
import g_step

stepname = 'Plaintext2Usfm'   # equals the main class name in this module

class Plaintext2Usfm(g_step.Step):
    def __init__(self, mainframe, mainapp):
        super().__init__(mainframe, mainapp, stepname, "Convert plain text to USFM")
        self.frame = Plaintext2Usfm_Frame(parent=mainframe, controller=self)
        self.frame.grid(row=1, column=0, sticky="nsew")

    def name(self):
        return stepname

    def onExecute(self, values):
        self.enablebutton(2, False)
        count = 1
        if not values['filename']:
            count = g_util.count_files(values['source_dir'], ".*txt$")
        self.mainapp.execute_script("plaintext2usfm", count)
        self.frame.clear_messages()
    def onNext(self):
        self.frame._save_values()   # only needed until 'target_dir' is retired
        super().onNext('work_dir')

    # Called by the main app.
    def onScriptEnd(self, status: str):
        if not status:
            status = f"The conversion is done.\nAdvance to USFM verification and cleanup."
        self.frame.show_progress(status)
        self.frame.onScriptEnd()
        self.enablebutton(2, True)

class Plaintext2Usfm_Frame(g_step.Step_Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        self.filename = StringVar()
        self.source_dir = StringVar()
        self.work_dir = StringVar()
        for var in (self.source_dir, self.work_dir):
            var.trace_add("write", self._onChangeEntry)
        for col in [3,4]:
            self.columnconfigure(col, weight=1)   # keep column 1 from expanding

        source_dir_label = ttk.Label(self, text="Location of text files:", width=20)
        source_dir_label.grid(row=3, column=1, sticky=W, pady=2)
        source_dir_entry = ttk.Entry(self, width=42, textvariable=self.source_dir)
        source_dir_entry.grid(row=3, column=2, columnspan=3, sticky=W)
        src_dir_Tip = Hovertip(source_dir_entry, hover_delay=1000,
                text="Folder containing the files to be converted")
        src_dir_find = ttk.Button(self, text="...", width=2, command=self._onFindSrcDir)
        src_dir_find.grid(row=3, column=4, sticky=W, padx=5)

        file_label = ttk.Label(self, text="File name:", width=20)
        file_label.grid(row=4, column=1, sticky=W, pady=2)
        file_entry = ttk.Entry(self, width=20, textvariable=self.filename)
        file_entry.grid(row=4, column=2, sticky=W)
        file_Tip = Hovertip(file_entry, hover_delay=500,
             text="Leave filename blank to convert all .txt files in the folder.")
        file_find = ttk.Button(self, text="...", width=2, command=self._onFindFile)
        file_find.grid(row=4, column=3, sticky=W, padx=8)

        work_dir_label = ttk.Label(self, text="Location for .usfm files:", width=21)
        work_dir_label.grid(row=5, column=1, sticky=W, pady=2)
        work_dir_entry = ttk.Entry(self, width=42, textvariable=self.work_dir)
        work_dir_entry.grid(row=5, column=2, columnspan=3, sticky=W)
        work_dir_Tip = Hovertip(work_dir_entry, hover_delay=1000,
                text="Folder for the new usfm files. The folder will be created if it doesn't exist.")
        work_dir_find = ttk.Button(self, text="...", width=2, command=self._onFindWorkDir)
        work_dir_find.grid(row=5, column=4, sticky=W, padx=5)

        source_dir_entry.focus()

    # Temporary function, until "target_dir" is fully retired.
    def getWorkDirConfigValue(self):
        workdir = self.values.get('work_dir', fallback="")
        if not workdir:
            self.values.get('target_dir', fallback="")  # the old name
        return workdir

    # Called when the frame is first activated. Populate the initial values.
    def show_values(self, values):
        self.values = values
        self.filename.set(values['filename'])
        self.source_dir.set(values['source_dir'])
        self.work_dir.set( self.getWorkDirConfigValue())

        # Create buttons
        self.controller.showbutton(1, "<<<", self._onBack)
        self.controller.showbutton(2, "CONVERT", self._onExecute, tip="Run the conversion script now.")
        self.controller.showbutton(3, "Source folder", self._onOpenTextDir,
                                   tip="Open the folder containing the files to be converted.")
        self.controller.showbutton(4, "Usfm folder", self._onOpenWorkDir)
        self.controller.showbutton(5, ">>>", self._onSkip, tip="Verify USFM")
        self._set_button_status()

        self.clear_show("This process converts Scripture text files to USFM. \
To be converted, the text files must meet these conditions:\n\
  * Each file contains a single book of the Bible.\n\
  * No extraneous text (e.g. from Word headers and footers).\n\
  * Any sections must be premarked with \\s.\n\
  * File names must be like XXX.txt or NN-XXX.txt, where XXX=book id and NN is the book number.\n\
  * UTF-8 encoding is required.\n\
  * The first line of each file contains the book title, no longer than 40 characters.\n\
  * Alternatively, the book title is marked by \\mt or \\h, anywhere prior to chapter 1.\n\
  * Chapter and verse numbers in Arabic numerals (0-9).\n\n\
The process creates one USFM file per book, with \
standardized names, like 41-MAT.usfm. \
The resulting USFM file(s) need to be verified and probably cleaned up a bit.")

    # Caches the current parameters in self.values and calls the mainapp to save them in the config file.
    def _save_values(self):
        self.values['filename'] = self.filename.get()
        self.values['source_dir'] = self.source_dir.get()
        self.values['work_dir'] = self.work_dir.get()
        self.controller.mainapp.save_values(stepname, self.values)
        self._set_button_status()

    def _onFindSrcDir(self, *args):
        self.controller.askdir(self.source_dir)
    def _onFindWorkDir(self, *args):
        self.controller.askdir(self.work_dir)
    def _onFindFile(self, *args):
        path = filedialog.askopenfilename(initialdir=self.source_dir.get(), title = "Select text file with Scripture text",
                                           filetypes=[('Text file', '*.txt')])
        if path:
            self.filename.set(os.path.basename(path))
    def _onChangeEntry(self, *args):
        self._set_button_status()
    def _onOpenTextDir(self, *args):
        os.startfile(self.source_dir.get())
    def _onOpenWorkDir(self, *args):
        # self._save_values()
        os.startfile(self.work_dir.get())
    def onScriptEnd(self):
        self.message_area['state'] = DISABLED   # prevents insertions to message area
        self.controller.showbutton(5, ">>>", self._onNext, tip="Verify USFM")

    def _set_button_status(self):
        good_sourcedir = os.path.isdir(self.source_dir.get())
        okay = (good_sourcedir and self.work_dir.get())
        self.controller.enablebutton(2, okay)
        self.controller.enablebutton(3, good_sourcedir)
        self.controller.enablebutton(4, os.path.isdir(self.work_dir.get()))
