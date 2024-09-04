# -*- coding: utf-8 -*-
# Implements Usx2Usfm and Usx2Usfm_Frame, which are the controller and frame
# for operating the usx2usfm.py script.
# GUI interface for converting USX files to USFM

from tkinter import *
from tkinter import ttk
from tkinter import font
from tkinter import filedialog
from idlelib.tooltip import Hovertip
import os
import g_util
import g_step

stepname = 'Usx2Usfm'   # equals the main class name in this module

class Usx2Usfm(g_step.Step):
    def __init__(self, mainframe, mainapp):
        super().__init__(mainframe, mainapp, stepname, "Convert USX to USFM")
        self.frame = Usx2Usfm_Frame(parent=mainframe, controller=self)
        self.frame.grid(row=1, column=0, sticky="nsew")

    def name(self):
        return stepname

    def onExecute(self, values):
        self.enablebutton(2, False)
        count = 1
        if not values['filename']:
            count = g_util.count_files(values['usx_dir'], ".usx")
        self.mainapp.execute_script("usx2usfm", count)
        self.frame.clear_messages()
    def onNext(self):
        copyparms = {'source_dir': self.values['usfm_dir']}
        self.mainapp.step_next(copyparms)

    # Called by the main app.
    def onScriptEnd(self, status: str):
        if not status:
            status = "The conversion is done."
        self.frame.show_progress(status)
        self.frame.onScriptEnd()
        self.enablebutton(2, True)
                
class Usx2Usfm_Frame(g_step.Step_Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        self.filename = StringVar()
        self.usx_dir = StringVar()
        self.usfm_dir = StringVar()
        self.notes = BooleanVar(value = False)
        for var in (self.usx_dir, self.usfm_dir):
            var.trace_add("write", self._onChangeEntry)
        for col in [3,4]:
            self.columnconfigure(col, weight=1)   # keep column 1 from expanding

        usx_dir_label = ttk.Label(self, text="Location of .usx files:", width=20)
        usx_dir_label.grid(row=3, column=1, sticky=W, pady=2)
        usx_dir_entry = ttk.Entry(self, width=42, textvariable=self.usx_dir)
        usx_dir_entry.grid(row=3, column=2, columnspan=3, sticky=W)
        usx_dir_Tip = Hovertip(usx_dir_entry, hover_delay=1000,
                text="Folder containing the files to be converted")
        usx_dir_find = ttk.Button(self, text="...", width=2, command=self._onFindSrcDir)
        usx_dir_find.grid(row=3, column=4, sticky=W, padx=5)

        file_label = ttk.Label(self, text="File name:", width=20)
        file_label.grid(row=4, column=1, sticky=W, pady=2)
        file_entry = ttk.Entry(self, width=20, textvariable=self.filename)
        file_entry.grid(row=4, column=2, sticky=W)
        file_Tip = Hovertip(file_entry, hover_delay=500,
             text="Leave filename blank to convert all .usx files in the folder.")
        file_find = ttk.Button(self, text="...", width=2, command=self._onFindFile)
        file_find.grid(row=4, column=3, sticky=W, padx=8)

        usfm_dir_label = ttk.Label(self, text="Location for .usfm files:", width=21)
        usfm_dir_label.grid(row=5, column=1, sticky=W, pady=2)
        usfm_dir_entry = ttk.Entry(self, width=42, textvariable=self.usfm_dir)
        usfm_dir_entry.grid(row=5, column=2, columnspan=3, sticky=W)
        usfm_dir_Tip = Hovertip(usfm_dir_entry, hover_delay=1000,
                text="Folder for the new usfm files. The folder will be created if it doesn't exist.")
        usfm_dir_find = ttk.Button(self, text="...", width=2, command=self._onFindTargetDir)
        usfm_dir_find.grid(row=5, column=4, sticky=W, padx=5)

        notes_checkbox = ttk.Checkbutton(self, text=r'Convert notes', variable=self.notes,
                                             onvalue=True, offvalue=False)
        notes_checkbox.grid(row=6, column=1, sticky=W)
        notes_Tip = Hovertip(notes_checkbox, hover_delay=500,
             text=r"Convert cross references and footnotes. NOT IMPLEMENTED CURRENTLY.")

        usx_dir_entry.focus()

    # Called when the frame is first activated. Populate the initial values.
    def show_values(self, values):
        self.values = values
        self.filename.set(values.get('filename', fallback=""))
        self.usx_dir.set(values.get('usx_dir', fallback=""))
        self.usfm_dir.set(values.get('usfm_dir', fallback = ""))
        self.notes.set(values.get('notes', fallback = False))

        # Create buttons
        self.controller.showbutton(1, "<<<", cmd=self._onBack)
        self.controller.showbutton(2, "CONVERT", tip="Run the conversion script now.", cmd=self._onExecute)
        self.controller.showbutton(3, "Usx folder",
                                   tip="Open the folder containing the files to be converted.", cmd=self._onOpenTextDir)
        self.controller.showbutton(4, "Usfm folder", cmd=self._onOpenTargetDir)
        self.controller.showbutton(5, ">>>", tip="Verify USFM", cmd=self._onSkip)
        self._set_button_status()

        self.clear_show("This process converts Unified Scripture XML (USX) files to USFM. \
The process creates one USFM file per book, with \
standardized names, like 41-MAT.usfm.")
    
    # Caches the current parameters in self.values and calls the mainapp to save them in the config file.
    def _save_values(self):
        self.values['filename'] = self.filename.get()
        self.values['usx_dir'] = self.usx_dir.get()
        self.values['usfm_dir'] = self.usfm_dir.get()
        self.values['notes'] = str(self.notes.get())
        self.controller.mainapp.save_values(stepname, self.values)
        self._set_button_status()

    def _onFindSrcDir(self, *args):
        self.controller.askdir(self.usx_dir)
    def _onFindTargetDir(self, *args):
        self.controller.askdir(self.usfm_dir)
    def _onFindFile(self, *args):
        path = filedialog.askopenfilename(initialdir=self.usx_dir.get(), title = "Select .usx file",
                                           filetypes=[('USX file', '*.usx')])
        if path:
            self.filename.set(os.path.basename(path))
    def _onChangeEntry(self, *args):
        self._set_button_status()
    def _onOpenTextDir(self, *args):
        os.startfile(self.usx_dir.get())
    def _onOpenTargetDir(self, *args):
        self._save_values()
        os.startfile(self.values['usfm_dir'])
    def onScriptEnd(self):
        self.message_area['state'] = DISABLED   # prevents insertions to message area
        self.controller.showbutton(5, ">>>", tip="Verify USFM", cmd=self._onNext)

    def _set_button_status(self):
        good_sourcedir = os.path.isdir(self.usx_dir.get())
        okay = (good_sourcedir and self.usfm_dir.get())
        self.controller.enablebutton(2, okay)
        self.controller.enablebutton(3, good_sourcedir)
        self.controller.enablebutton(4, os.path.isdir(self.usfm_dir.get()))
