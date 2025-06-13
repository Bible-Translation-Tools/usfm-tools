# -*- coding: utf-8 -*-
# GUI interface for verifying manifest.yaml file and readiness of resource container.
#

from tkinter import *
from tkinter import ttk
from tkinter import font
from idlelib.tooltip import Hovertip
import g_util
import g_step
import os
import subprocess
import time

stepname = 'VerifyManifest'   # equals the main class name in this module

class VerifyManifest(g_step.Step):
    def __init__(self, mainframe, mainapp):
        super().__init__(mainframe, mainapp, stepname, "Verify manifest.yaml")
        self.frame = VerifyManifest_Frame(mainframe, self)
        self.frame.grid(row=1, column=0, sticky="nsew")

    def name(self):
        return stepname

    def onExecute(self, values):
        self.enablebutton(2, False)
        # self.values = values
        self.mainapp.execute_script("verifyManifest", 1)
        self.frame.clear_messages()

class VerifyManifest_Frame(g_step.Step_Frame):
    def __init__(self, parent, controller):
        super().__init__(parent,controller)

        self.source_dir = StringVar()
        self.source_dir.trace_add("write", self._onChangeEntry)
        self.bibletype = BooleanVar(value = True)
        self.expectAscii = BooleanVar(value = False)
        for col in (3,5):
            self.columnconfigure(col, weight=1)   # keep columns 1,4 from expanding

        source_dir_label = ttk.Label(self, text="Location of resource: ")
        source_dir_label.grid(row=4, column=1, sticky=W, pady=2)
        self.source_dir_entry = ttk.Entry(self, width=45, textvariable=self.source_dir)
        self.source_dir_entry.grid(row=4, column=2, sticky=W)
        file_Tip = Hovertip(self.source_dir_entry, hover_delay=500,
             text="Folder where manifest.yaml and other files to be submitted reside")
        src_dir_find = ttk.Button(self, text="...", width=2, command=self._onFindSrcDir)
        src_dir_find.grid(row=4, column=3, sticky=W, padx=5)

        bibletype_checkbox = ttk.Checkbutton(self, text='Bible', variable=self.bibletype,
                                             onvalue=True, offvalue=False)
        bibletype_checkbox.grid(row=5, column=1, sticky=W)
        bibletype_Tip = Hovertip(bibletype_checkbox, hover_delay=500,
             text="Is the resource a Bible or Bible portion (as opposed to OBS, Notes, etc)?")

        expectAscii_checkbox = ttk.Checkbutton(self, text='Expect ASCII', variable=self.expectAscii,
                                             onvalue=True, offvalue=False)
        expectAscii_checkbox.grid(row=5, column=2, sticky=W)
        expectAscii_Tip = Hovertip(expectAscii_checkbox, hover_delay=500,
             text=r"Suppress warnings about ASCII book titles, etc")

        self.message_area['wrap'] = "none"
        xs = ttk.Scrollbar(self, orient = 'horizontal', command = self.message_area.xview)
        xs.grid(row=89, column = 1, columnspan=4, sticky = 'ew')
        self.message_area['xscrollcommand'] = xs.set

    def show_values(self, values):
        self.values = values
        self.source_dir.set(values.get('source_dir', fallback = ""))
        self.bibletype.set(values.get('bibletype', fallback = True))
        self.expectAscii.set(values.get('expectascii', fallback = False))

        # Create buttons
        self.controller.showbutton(1, "<<<", self._onBack, tip="Previous step")
        self.controller.showbutton(2, "VERIFY", self._onExecute, tip="Verify readiness of manifest.yaml and the whole resource.")
        self.controller.showbutton(3, "Open manifest", self._onOpenManifest, tip="Opens manifest.yaml in your default editor")
        self.controller.showbutton(4, "Open folder", self._onOpenSourceDir, tip="Opens the resource folder")
        self.controller.hidebutton(5)
        self._set_button_status()

    def onScriptEnd(self):
        self.message_area['state'] = DISABLED   # prevents insertions to message area
        self.controller.enablebutton(2, True)

    def _save_values(self):
        self.values['source_dir'] = self.source_dir.get()
        self.values['bibletype'] = str(self.bibletype.get())
        self.values['expectascii'] = str(self.expectAscii.get())
        self.controller.mainapp.save_values(stepname, self.values)
        self._set_button_status()

    def _onFindSrcDir(self, *args):
        self.controller.askdir(self.source_dir)
    def _onChangeEntry(self, *args):
        self._set_button_status()

    def _onOpenManifest(self, *args):
        self._save_values()
        path = os.path.join(self.values['source_dir'], "manifest.yaml")
        os.startfile(path)
    def _onOpenSourceDir(self, *args):
        self._save_values()
        os.startfile(self.values['source_dir'])

    def _set_button_status(self):
        self.controller.enablebutton(2, os.path.isdir(self.source_dir.get()))
