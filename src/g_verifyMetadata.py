# -*- coding: utf-8 -*-
# GUI interface for verifying manifest.yaml file and readiness of resource container.
#

from tkinter import ttk
from tkinter import StringVar, BooleanVar, W, DISABLED
from idlelib.tooltip import Hovertip
import g_step
import os

stepname = 'VerifyMetadata'   # equals the main class name in this module

class VerifyMetadata(g_step.Step):
    def __init__(self, mainframe, mainapp):
        super().__init__(mainframe, mainapp, stepname, "Verify metadata")
        self.frame = VerifyMetadata_Frame(mainframe, self)
        self.frame.grid(row=1, column=0, sticky="nsew")
        self.executed = False

    def name(self):
        return stepname

    def onBack(self):
        if self.executed:
            super().onBack('work_dir')
        else:
            super().onBack()
        self.executed = False

    def onNext(self):
        if self.executed:
            super().onNext('work_dir')
        else:
            super().onNext()
        self.executed = False

    def onExecute(self):
        self.enablebutton(2, False)
        self.enablebutton(5, False)
        self.mainapp.execute_script("verifyMetadata", 2)
        self.frame.clear_messages()
        self.executed = True

class VerifyMetadata_Frame(g_step.Step_Frame):
    def __init__(self, parent, controller):
        super().__init__(parent,controller)

        self.work_dir = StringVar()
        self.work_dir.trace_add("write", self._set_button_status)
        self.bibletype = BooleanVar(value = True)
        for col in (3,5):
            self.columnconfigure(col, weight=1)   # keep columns 1,4 from expanding

        work_dir_label = ttk.Label(self, text="Location of resource: ")
        work_dir_label.grid(row=4, column=1, sticky=W, pady=2)
        self.work_dir_entry = ttk.Entry(self, width=45, textvariable=self.work_dir)
        self.work_dir_entry.grid(row=4, column=2, sticky=W)
        file_Tip = Hovertip(self.work_dir_entry, hover_delay=500,
             text="Folder where manifest.yaml and other files to be submitted reside")
        src_dir_find = ttk.Button(self, text="...", width=2, command=self._onFindSrcDir)
        src_dir_find.grid(row=4, column=3, sticky=W, padx=5)

        bibletype_checkbox = ttk.Checkbutton(self, text='Bible', variable=self.bibletype,
                                             onvalue=True, offvalue=False)
        bibletype_checkbox.grid(row=5, column=1, sticky=W)
        bibletype_Tip = Hovertip(bibletype_checkbox, hover_delay=500,
             text="Is the resource a Bible or Bible portion (as opposed to OBS, Notes, etc)?")

        self.message_area['wrap'] = "none"
        xs = ttk.Scrollbar(self, orient = 'horizontal', command = self.message_area.xview)
        xs.grid(row=89, column = 1, columnspan=4, sticky = 'ew')
        self.message_area['xscrollcommand'] = xs.set

    # Temporary function, until "source_dir" is fully retired.
    def getWorkDirConfigValue(self):
        workdir = self.getOption('work_dir')
        if not workdir:
            workdir = self.getOption('source_dir')  # the old name
        return workdir

    def show_values(self):
        self.work_dir.set( self.getWorkDirConfigValue())
        self.bibletype.set(self.getBooleanOption('bibletype'))

        # Create buttons
        self.controller.showbutton(1, "<<<", self._onBack, tip="Previous step")
        self.controller.showbutton(2, "VERIFY", self._onExecute, tip="Verify readiness of manifest.yaml and the whole resource.")
        self.controller.bindButtonEvent(2, "<Enter>", self._onCheckInputs)
        self.controller.showbutton(3, "Open manifest", self._onOpenManifest, tip="Opens manifest.yaml in your default editor")
        self.controller.showbutton(4, "Open folder", self._onOpenWorkDir, tip="Opens the resource folder")
        self.controller.hidebutton(5)
        self._set_button_status()

    def onScriptEnd(self):
        self.message_area['state'] = DISABLED   # prevents insertions to message area
        self.controller.enablebutton(2, True)
        self.controller.enablebutton(5, True)

    def get_entered_values(self):
        values = {}
        values['work_dir'] = self.work_dir.get()
        values['bibletype'] = str(self.bibletype.get())
        return values

    # Returns a list of incomplete or incorrect inputs.
    # Used by _onExecute().
    # Is also called before values are saved to configuration files.
    def invalidInputs(self):
        objections = []
        dir = self.work_dir.get()
        if not dir or not os.path.isdir(dir) or dir.endswith('.'):
            objections.append("Invalid location.")
        return objections

    def _onFindSrcDir(self, *args):
        self.controller.askdir(self.work_dir)

    def _onOpenManifest(self, *args):
        self._save_values()
        path = os.path.join(self.work_dir.get(), "manifest.yaml")
        os.startfile(path)
    def _onOpenWorkDir(self, *args):
        self._save_values()
        os.startfile(self.work_dir.get())

    def _set_button_status(self, *args):
        valid = not self.invalidInputs()
        self.controller.enablebutton(2, valid)
        self.controller.enablebutton(4, valid)
        workdir = self.work_dir.get()
        self.controller.enablebutton(3, valid and os.path.isfile(os.path.join(workdir, "manifest.yaml")))
