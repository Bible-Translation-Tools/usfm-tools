# -*- coding: utf-8 -*-
# GUI interface for USFM to USX file conversion.
#

# from tkinter import *
from tkinter import ttk
from tkinter import font
from tkinter import StringVar, filedialog, W, N, DISABLED
from idlelib.tooltip import Hovertip
import g_util
import g_step
import os
import time

stepname = 'Usfm2Usx'   # equals the main class name in this module

class Usfm2Usx(g_step.Step):
    def __init__(self, mainframe, mainapp):
        super().__init__(mainframe, mainapp, stepname, "Generate resource container")
        self.frame = Usfm2Usx_Frame(mainframe, self)
        self.frame.grid(row=1, column=0, sticky="nsew")

    def name(self):
        return stepname

    def onExecute(self):
        self.enablebutton(2, False)
        count = 1
        if not self.getOption('filename'):
            count = g_util.count_files(self.getOption('work_dir'), ".*sfm$")
        self.mainapp.execute_script("usfm2usx", count)
        self.frame.clear_messages()

    # Called by the main app.
    def onScriptEnd(self, status: str):
        if status:
            self.frame.show_progress(status)
        msg = "\nIf the process completed successfully...\n" +\
            "Test one or more of the generated “resource containers” by using it as a source text in BTT-Writer."
        self.frame.show_progress(msg)
        self.frame.onScriptEnd()
        self.enablebutton(2, True)

class Usfm2Usx_Frame(g_step.Step_Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        self.language_code = StringVar()
        self.language_name = StringVar()
        self.direction = StringVar()
        self.bible_name = StringVar()
        self.bible_id = StringVar()
        self.pub_date = StringVar()
        self.license = StringVar()
        self.version = StringVar()
        self.work_dir = StringVar()
        self.filename = StringVar()
        self.rc_dir = StringVar()
        for var in (self.language_code, self.language_name, self.bible_id, self.pub_date,
                    self.license, self.version, self.work_dir, self.filename, self.rc_dir):
            var.trace_add("write", self._onChangeEntry)
        self.bible_name.trace_add("write", self._onChangeBible)

        self.grid_columnconfigure(4, weight=1)
        self.grid_columnconfigure(5, weight=0)

        language_code_label = ttk.Label(self, text="Language code:", width=20)
        language_code_label.grid(row=3, column=1, sticky="wen", pady=2)
        language_code_entry = ttk.Entry(self, width=20, textvariable=self.language_code)
        language_code_entry.grid(row=3, column=2, sticky=W)
        language_label = ttk.Label(self, text="Language name:", width=20)
        language_label.grid(row=4, column=1, sticky="wen", pady=2)
        language_entry = ttk.Entry(self, width=20, textvariable=self.language_name)
        language_entry.grid(row=4, column=2, sticky=W)

        subheadingFont = font.Font(size=10, slant='italic')     # normal size is 9
        direction_label = ttk.Label(self, text="Text direction:", font=subheadingFont)
        direction_label.grid(row=5, column=1, sticky="wen", pady=2)
        ltr_rb = ttk.Radiobutton(self, text='Left to right', variable=self.direction, value='ltr')
        ltr_rb.grid(row=6, column=1, sticky=N)
        rtl_rb = ttk.Radiobutton(self, text='Right to left', variable=self.direction, value='rtl')
        rtl_rb.grid(row=6, column=2, sticky=N)

        bible_name_label = ttk.Label(self, text="Bible name:", width=15)
        bible_name_label.grid(row=3, column=3, sticky="wen", pady=2)
        bible_name_entry = ttk.Entry(self, width=20, textvariable=self.bible_name)
        bible_name_entry.grid(row=3, column=4, sticky=W)
        bible_id_label = ttk.Label(self, text="Bible ID:", width=15)
        bible_id_label.grid(row=4, column=3, sticky="wen", pady=2)
        bible_id_entry = ttk.Entry(self, width=20, textvariable=self.bible_id)
        bible_id_entry.grid(row=4, column=4, sticky=W)

        date_label = ttk.Label(self, text="Publication date:", width=15)
        date_label.grid(row=5, column=3, sticky="wen", pady=2)
        date_entry = ttk.Entry(self, width=20, textvariable=self.pub_date)
        date_entry.grid(row=5, column=4, sticky=W)
        version_label = ttk.Label(self, text="Version:", width=15)
        version_label.grid(row=6, column=3, sticky="wen", pady=2)
        version_entry = ttk.Entry(self, width=20, textvariable=self.version)
        version_entry.grid(row=6, column=4, sticky=W)

        license_label = ttk.Label(self, text="License:", width=15)
        license_label.grid(row=7, column=3, sticky="wen", pady=2)
        license_entry = ttk.Entry(self, width=20, textvariable=self.license)
        license_entry.grid(row=7, column=4, sticky=W)

        work_dir_label = ttk.Label(self, text="Location of .usfm files:", width=20)
        work_dir_label.grid(row=8, column=1, sticky=W, pady=2)
        work_dir_entry = ttk.Entry(self, width=61, textvariable=self.work_dir)
        work_dir_entry.grid(row=8, column=2, columnspan=3, sticky=W)
        src_dir_find = ttk.Button(self, text="...", width=2, command=self._onFindSrcDir)
        src_dir_find.grid(row=8, column=5, sticky=W)

        file_label = ttk.Label(self, text="File name:", width=20)
        file_label.grid(row=9, column=1, sticky=W, pady=2)
        file_entry = ttk.Entry(self, width=19, textvariable=self.filename)
        file_entry.grid(row=9, column=2, sticky=W)
        file_Tip = Hovertip(file_entry, hover_delay=500,
             text="Leave filename blank to convert all .usfm files in the folder.")
        file_find = ttk.Button(self, text="...", width=2, command=self._onFindFile)
        file_find.grid(row=9, column=3, sticky=W)

        rc_dir_label = ttk.Label(self, text="RC folder:", width=20)
        rc_dir_label.grid(row=10, column=1, sticky=W, pady=2)
        rc_dir_entry = ttk.Entry(self, width=61, textvariable=self.rc_dir)
        rc_dir_entry.grid(row=10, column=2, columnspan=4, sticky=W)
        rc_dir_Tip = Hovertip(rc_dir_entry, hover_delay=500,
             text="BTT-Writer application data folder for Resource Containers")
        rc_dir_find = ttk.Button(self, text="...", width=2, command=self._onFindRcDir)
        rc_dir_find.grid(row=10, column=5, sticky=W)

    # Temporary function, until "source_dir" is fully retired.
    def getWorkDirConfigValue(self):
        workdir = self.getOption('work_dir')
        if not workdir:
            workdir = self.getOption('source_dir')  # the old name
        return workdir

    def show_values(self):
        self.language_code.set(self.getOption('language_code'))
        self.language_name.set(self.getOption('language_name'))
        self.direction.set(self.getOption('direction'))
        self.bible_name.set(self.getOption('bible_name'))
        self.bible_id.set(self.getOption('bible_id'))
        self.pub_date.set(self.getOption('pub_date'))
        self.license.set(self.getOption('license'))
        self.version.set(self.getOption('version'))
        self.work_dir.set( self.getWorkDirConfigValue() )
        self.filename.set(self.getOption('filename'))
        self.rc_dir.set(self.getOption('rc_dir'))

        # Create buttons
        self.controller.showbutton(1, "<<<", self._onBack, tip="Reverify original USFM file(s)")
        self.controller.showbutton(2, "CONVERT", self._onExecute,
                                   tip="Convert to USX now; overwrite existing .usx files, if any.")
        self.controller.hidebutton(3,4,5)
        self._set_button_status()

    def onScriptEnd(self):
        self.message_area['state'] = DISABLED   # prevents insertions to message area
        self.controller.enablebutton(5, True)

    # Returns the current entered values in a dict.
    def get_entered_values(self):
        values = {}
        values['language_code'] = self.language_code.get()
        values['language_name'] = self.language_name.get()
        values['bible_name'] = self.bible_name.get()
        values['bible_id'] = self.bible_id.get()
        values['direction'] = self.direction.get()
        values['pub_date'] = self.pub_date.get()
        values['license'] = self.license.get()
        values['version'] = self.version.get()
        values['work_dir'] = self.work_dir.get()
        values['filename'] = self.filename.get()
        values['rc_dir'] = self.rc_dir.get()
        return values

    def _onFindSrcDir(self, *args):
        self.controller.askdir(self.work_dir)
    def _onFindFile(self, *args):
        path = filedialog.askopenfilename(initialdir=self.work_dir.get(), title = "Select usfm file",
                                           filetypes=[('Usfm file', '*.usfm')])
        if path:
            self.filename.set(os.path.basename(path))

    def _onFindRcDir(self, *args):
        if not self.rc_dir.get() and os.name == 'nt':
            self.rc_dir.set(r"~\AppData\Local\BTT-Writer\library")
        self.controller.askdir(self.rc_dir)

    def _onChangeEntry(self, *args):
        self._set_button_status()
    # Called when the Bible name changes
    def _onChangeBible(self, *args):
        if len(self.bible_name.get()) > 3 and not self.bible_id:
            self.bible_id.set( self.bible_name.get().lower()[0:3] )
        self._set_button_status()

    def _set_button_status(self):
        dirs_ok = os.path.isdir(self.work_dir.get()) and os.path.isdir(self.rc_dir.get())
        if dirs_ok and self.filename.get():
            path = os.path.join(self.work_dir.get(), self.filename.get())
            dirs_ok = os.path.isfile(path)
        language_ok = self.language_code.get() and self.language_name.get()
        pubdetails_ok = self.bible_id.get() and self.bible_name.get() and\
                        self.pub_date.get() and self.license.get() and self.version.get()
        self.controller.enablebutton(2, dirs_ok and language_ok and pubdetails_ok)
