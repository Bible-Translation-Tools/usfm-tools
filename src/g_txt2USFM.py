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

    def name(self):
        return stepname

    def onExecute(self, values):
        self.enablebutton(2, False)
        self.values = values
        pattern = values['language_code'] + r"_[\w][\w][\w].*_reg|_ulb"
        count = g_util.count_folders(values['source_dir'], pattern)
        self.mainapp.execute_script("txt2USFM", count)
        self.frame.clear_messages()

    def onNext(self):
        copyparms = {'language_code': self.values['language_code'], 'source_dir': self.values['target_dir']}
        self.mainapp.step_next(copyparms)

    # Called by the main app.
    def onScriptEnd(self, status: str):
        if not status:  # the normal case
            if self.values.getboolean('section_headings', fallback = False):
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
        self.target_dir = StringVar()
        self.lang_cbname = self.language_code.trace_add("write", self._onChangeEntry)
        self.source_cbname = self.source_dir.trace_add("write", self._onChangeSourceDir)
        self.target_cbname = self.target_dir.trace_add("write", self._onChangeEntry)
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
        target_dir_Tip = Hovertip(source_dir_entry, hover_delay=1000,
                text="Folder containing the files to be converted")
        src_dir_find = ttk.Button(self, text="...", width=2, command=self._onFindSrcDir)
        src_dir_find.grid(row=4, column=4, sticky=W)

        target_dir_label = ttk.Label(self, text="Location for .usfm files:", width=21)
        target_dir_label.grid(row=5, column=1, sticky=W, pady=2)
        target_dir_entry = ttk.Entry(self, width=47, textvariable=self.target_dir)
        target_dir_entry.grid(row=5, column=2, columnspan=3, sticky=W)
        target_dir_Tip = Hovertip(target_dir_entry, hover_delay=1000,
                text="Folder for the new usfm files. The folder will be created if it doesn't exist.")
        target_dir_find = ttk.Button(self, text="...", width=2, command=self._onFindTargetDir)
        target_dir_find.grid(row=5, column=4, sticky=W)

        # text=r'Has section headings'
        headings_checkbox = ttk.Checkbutton(self, text=r'Has section headings', variable=self.headings,
                                             onvalue=True, offvalue=False)
        headings_checkbox.grid(row=6, column=1, sticky=W)
        headings_Tip = Hovertip(headings_checkbox, hover_delay=500,
                text="Does the translated text include section headings? (If you don't know, try it both ways and compare the results.)")
        headings_help = ttk.Button(self, text="...", width=2, command=self._onHelpHeadings)
        headings_help.grid(row=6, column=2, sticky=W)
        language_code_entry.focus()

    # Called when the frame is first activated. Populate the initial values.
    def show_values(self, values):
        self.language_code.trace_remove("write", self.lang_cbname)
        self.source_dir.trace_remove("write", self.source_cbname)
        self.target_dir.trace_remove("write", self.target_cbname)

        self.values = values
        self.language_code.set(values['language_code'])
        self.source_dir.set(values['source_dir'])
        self.target_dir.set(values['target_dir'])
        self.headings.set(values.get('section_headings', fallback = False))

        # Create buttons
        self.controller.showbutton(1, "<<<", self._onBack)
        self.controller.showbutton(2, "CONVERT", self._onExecute, tip="Run the conversion script now.")
        self.controller.bindButtonEvent(2, "<Enter>", self._onCheckInputs)
        self.controller.showbutton(3, "Source folder", self._onOpenTextDir,
                                   tip="Open the folder containing the files to be converted.")
        self.controller.showbutton(4, "Usfm folder", self._onOpenTargetDir)
        self.controller.showbutton(5, ">>>", self._onSkip, tip="Verify USFM")
        self.lang_cbname = self.language_code.trace_add("write", self._onChangeEntry)
        self.source_cbname = self.source_dir.trace_add("write", self._onChangeSourceDir)
        self.target_cbname = self.target_dir.trace_add("write", self._onChangeEntry)
        self._set_button_status()

    # Caches the current parameters in self.values and calls the mainapp to save them in the config file.
    def _save_values(self):
        if not self.invalidInputs():
            self.values['language_code'] = self.language_code.get()
            self.values['source_dir'] = self.source_dir.get()
            self.values['target_dir'] = self.target_dir.get()
            self.values['section_headings'] = str(self.headings.get())
            self.controller.mainapp.save_values(stepname, self.values)
            self._set_button_status()

    def _onFindSrcDir(self, *args):
        self.controller.askdir(self.source_dir)
    def _onFindTargetDir(self, *args):
        self.controller.askdir(self.target_dir)
    def _onChangeSourceDir(self, *args):
        self.language_code.set("")
        self._set_button_status()
    def _onChangeEntry(self, *args):
        self._set_button_status()
    def _onOpenTextDir(self, *args):
        os.startfile(self.source_dir.get())
    def _onOpenTargetDir(self, *args):
        self._save_values()
        os.startfile(self.values['target_dir'])

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
        target = self.target_dir.get()

        if not code:
            objections.append("Language code is required.")
        if not os.path.isdir(dir):
            objections.append(f"{dir} is not a valid folder.")
        target_parent = os.path.dirname(target)
        if not os.path.isdir(target_parent):
            objections.append(f"{target} cannot be created.")
        return objections

    def onScriptEnd(self):
        self.message_area['state'] = DISABLED   # prevents insertions to message area
        self.controller.enablebutton(2, len(self.invalidInputs()) == 0)
        self.controller.showbutton(5, ">>>", self._onNext, tip="Verify USFM")
        self._set_button_status()

    def _set_button_status(self):
        self.controller.enablebutton(2, len(self.invalidInputs()) == 0)
        self.controller.enablebutton(3, os.path.isdir(self.source_dir.get()))
        self.controller.enablebutton(4, os.path.isdir(self.target_dir.get()))
