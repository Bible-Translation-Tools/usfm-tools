# -*- coding: utf-8 -*-
# Implements Txt2USFM and Text2USFM_Frame, which are the controller and frame
# for operating the txt2USFM.py script.
# GUI interface for merging BTTW text files and converting to USFM

from tkinter import ttk
from tkinter import StringVar, BooleanVar, W, DISABLED
from idlelib.tooltip import Hovertip
import os
import g_util
import g_step

stepname = 'Txt2USFM'   # equals the main class name in this module

class Txt2USFM(g_step.Step):
    def __init__(self, mainframe, mainapp):
        super().__init__(mainframe, mainapp, stepname, "Convert text files to USFM")
        self.frame = Text2USFM_Frame(parent=mainframe, controller=self)
        self.frame.grid(row=1, column=0, sticky="nsew")
        self.executed = False

    def name(self) -> str:
        return stepname

    def onExecute(self):
        self.enablebutton(2, False)
        pattern = self.getOption('language_code') + r"_[\w][\w][\w].*_reg|_ulb"
        count = g_util.count_folders(self.getOption('source_dir'), pattern)
        self.mainapp.execute_script("txt2USFM", count)
        self.frame.clear_messages()
        self.executed = True

    def onNext(self):
        if self.executed:
            super().onNext('language_code', 'work_dir')
        else:
            super().onNext()
        self.executed = False

    # Called by the main app.
    def onScriptEnd(self, status: str):
        if not status:  # the normal case
            if self.getBooleanOption('section_headings'):
                status = """
Regarding section titles:
This process attempted to identify section titles using various criteria. \
Some section titles may have been missed because they didn't meet all the critera. \
Other things that aren't really section titles may have been marked as section titles because they did meet the criteria. \
Therefore, it is necessary to manually verify section titles after this step.
"""
        if status:
            self.frame.show_progress(status)
        self.frame.onScriptEnd()

class Text2USFM_Frame(g_step.Step_Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        self.language_code = StringVar()
        self.source_dir = StringVar()
        self.work_dir = StringVar()
        self.lang_cbname = self.language_code.trace_add("write", self._onChangeEntry)
        self.source_cbname = self.source_dir.trace_add("write", self._onChangeSourceDir)
        self.work_cbname = self.work_dir.trace_add("write", self._onChangeEntry)
        self.headings = BooleanVar(value = False)
        for col in [2,3]:
            self.columnconfigure(col, weight=1)   # keep column 1 from expanding
        self.columnconfigure(4, minsize=94)

        language_code_label = ttk.Label(self, text="Language code:", width=20)
        language_code_label.grid(row=3, column=1, sticky=W, pady=2)
        language_code_entry = ttk.Entry(self, width=20, textvariable=self.language_code)
        language_code_entry.grid(row=3, column=2, sticky=W)
        source_dir_label = ttk.Label(self, text="Location of text files:", width=20)
        source_dir_label.grid(row=4, column=1, sticky=W, pady=2)
        source_dir_entry = ttk.Entry(self, width=47, textvariable=self.source_dir)
        source_dir_entry.grid(row=4, column=2, columnspan=3, sticky=W)
        work_dir_Tip = Hovertip(source_dir_entry, hover_delay=500,
                text="Folder containing the files to be converted")
        src_dir_find = ttk.Button(self, text="...", width=2, command=self._onFindSrcDir)
        src_dir_find.grid(row=4, column=4, sticky=W)

        work_dir_label = ttk.Label(self, text="Location for .usfm files:", width=21)
        work_dir_label.grid(row=5, column=1, sticky=W, pady=2)
        work_dir_entry = ttk.Entry(self, width=47, textvariable=self.work_dir)
        work_dir_entry.grid(row=5, column=2, columnspan=3, sticky=W)
        work_dir_Tip = Hovertip(work_dir_entry, hover_delay=500,
                text="Folder for the new usfm files. The folder will be created if it doesn't exist.")
        work_dir_find = ttk.Button(self, text="...", width=2, command=self._onFindWorkDir)
        work_dir_find.grid(row=5, column=4, sticky=W)

        # text=r'Has section headings'
        headings_checkbox = ttk.Checkbutton(self, text=r'Has section headings', variable=self.headings,
                                             onvalue=True, offvalue=False)
        headings_checkbox.grid(row=6, column=1, sticky=W)
        headings_Tip = Hovertip(headings_checkbox, hover_delay=500,
                text="Does the translated text include section headings? (If you don't know, try it both ways and compare the results.)")
        headings_help = ttk.Button(self, text="...", width=2, command=self._onHelpHeadings)
        headings_help.grid(row=6, column=2, sticky=W)
        language_code_entry.focus()

    # Temporary function, until "target_dir" is fully retired.
    def getWorkDirConfigValue(self):
        workdir = self.getOption('work_dir')
        if not workdir:
            workdir = self.getOption('target_dir')
        return workdir

    # Called when the frame is first activated. Populate the initial values.
    def show_values(self):
        self.language_code.trace_remove("write", self.lang_cbname)
        self.source_dir.trace_remove("write", self.source_cbname)
        self.work_dir.trace_remove("write", self.work_cbname)

        self.language_code.set(self.getOption('language_code'))
        self.source_dir.set(self.getOption('source_dir'))
        self.work_dir.set( self.getWorkDirConfigValue() )
        # self.headings.set(values['section_headings'] if 'section_headings' in values else False)
        self.headings.set(self.getBooleanOption('section_headings'))

        # Create buttons
        self.controller.showbutton(1, "<<<", self._onBack, tip="Back")
        self.controller.showbutton(2, "CONVERT", self._onExecute)   # no tip since we bind the <Enter> event
        self.controller.bindButtonEvent(2, "<Enter>", self._onCheckInputs)
        self.controller.showbutton(3, "Source folder", self._onOpenTextDir,
                                   tip="Open the folder containing the files to be converted.")
        self.controller.showbutton(4, "Usfm folder", self._onOpenWorkDir)
        self.controller.showbutton(5, ">>>", self._onSkip, tip="Verify USFM")
        self.lang_cbname = self.language_code.trace_add("write", self._onChangeEntry)
        self.source_cbname = self.source_dir.trace_add("write", self._onChangeSourceDir)
        self.work_cbname = self.work_dir.trace_add("write", self._onChangeEntry)
        self._set_button_status()

    # Returns the current entered values in a dict.
    def get_entered_values(self):
        values = {}
        values['language_code'] = self.language_code.get()
        values['source_dir'] = self.source_dir.get()
        values['work_dir'] = self.work_dir.get()
        values['section_headings'] = str(self.headings.get())
        return values

    def _onFindSrcDir(self, *args):
        self.controller.askdir(self.source_dir)
    def _onFindWorkDir(self, *args):
        self.controller.askdir(self.work_dir)
    def _onChangeSourceDir(self, *args):
        self.language_code.set("")
        self._set_button_status()
    def _onChangeEntry(self, *args):
        self._set_button_status()
    def _onOpenTextDir(self, *args):
        os.startfile(self.source_dir.get())
    def _onOpenWorkDir(self, *args):
        os.startfile(self.work_dir.get())

    def _onHelpHeadings(self, *args):
        msg = "If you don't know whether the text contains section headings,\n\
run the conversion both ways and keep the better result.\n"
        self.clear_show(msg)

    # Returns a list of incomplete or incorrect inputs.
    # Used by _onExecute().
    # Is also called before values are saved to configuration files.
    # Is also called when the mouse hovers over the CONVERT button.
    def invalidInputs(self, *args):
        objections = []
        code = self.language_code.get()
        dir = self.source_dir.get()
        workdir = self.work_dir.get()

        if not code:
            objections.append("Language code is required.")
        if not os.path.isdir(dir):
            objections.append(f"{dir} is not a valid folder.")
        work_parent = os.path.dirname(workdir)
        if not os.path.isdir(work_parent):
            objections.append(f"{workdir} cannot be created.")
        return objections

    def onScriptEnd(self):
        self.message_area['state'] = DISABLED   # prevents insertions to message area
        self.controller.showbutton(5, ">>>", self._onNext, tip="Verify USFM")
        self._set_button_status()

    def _set_button_status(self):
        self.controller.enablebutton(2, len(self.invalidInputs()) == 0)
        self.controller.enablebutton(3, os.path.isdir(self.source_dir.get()))
        self.controller.enablebutton(4, os.path.isdir(self.work_dir.get()))
