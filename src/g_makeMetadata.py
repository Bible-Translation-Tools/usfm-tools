# -*- coding: utf-8 -*-
# GUI interface for makeMetadata.py script
#

from tkinter import ttk
from tkinter import font
from tkinter import filedialog
from tkinter import StringVar, BooleanVar, E, W, N, DISABLED
from idlelib.tooltip import Hovertip
import g_util
import g_step
import os
from projectinfo import ProjectInfo
from manifestyaml import ManifestYaml
from scripture_burrito import Burrito

stepname = 'MakeMetadata'   # equals the main class name in this module

class MakeMetadata(g_step.Step):
    def __init__(self, mainframe, mainapp):
        super().__init__(mainframe, mainapp, stepname, "Make Metadata")
        self.frame = MakeMetadata_Frame(mainframe, self)
        self.frame.grid(row=1, column=0, sticky="nsew")
        self.executed = False

    def name(self):
        return stepname

    def onNext(self):
        if self.executed:
            super().onNext('work_dir', 'language_code')
        else:
            super().onNext()
        self.executed = False

    def onExecute(self):
        self.enablebutton(2, False)
        self.mainapp.execute_script("makeMetadata", 2)
        self.frame.clear_messages()
        self.executed = True

class MakeMetadata_Frame(g_step.Step_Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.changingVars = False

        self.language_code = StringVar()
        self.language_name_en = StringVar()
        self.direction = StringVar()
        self.localized_name = StringVar()
        self.work_dir = StringVar()
        self.license_file = StringVar()
        self.license_type = StringVar()
        self.repo_owner = StringVar()
        self.repo_name = StringVar()

        language_code_label = ttk.Label(self, text="Language code:", width=20)
        language_code_label.grid(row=3, column=1, sticky="wen", pady=2)
        language_code_entry = ttk.Entry(self, width=18, textvariable=self.language_code)
        language_code_entry.grid(row=3, column=2, sticky=W)
        language_name_label = ttk.Label(self, text="Name:", width=20)
        language_name_label.grid(row=3, column=4, sticky=E)
        language_name_entry = ttk.Entry(self, width=21, textvariable=self.language_name_en)
        language_name_entry.grid(row=3, column=5, sticky=W)
        tip = Hovertip(language_name_entry, hover_delay=500, text="Language name (anglicized if possible)")

        ltr_rb = ttk.Radiobutton(self, text='Left-to-right', variable=self.direction, value='ltr')
        ltr_rb.grid(row=4, column=1, sticky=W)
        tip = Hovertip(ltr_rb, hover_delay=500, text="Language reads left to right")
        rtl_rb = ttk.Radiobutton(self, text='Right-to-left', variable=self.direction, value='rtl')
        rtl_rb.grid(row=4, column=2, sticky=W)
        tip = Hovertip(rtl_rb, hover_delay=500, text="Language reads right to left")

        local_name_label = ttk.Label(self, text="Localized name:", width=20)
        local_name_label.grid(row=4, column=4, sticky=E)
        local_name_entry = ttk.Entry(self, width=21, textvariable=self.localized_name)
        local_name_entry.grid(row=4, column=5, sticky=W)
        tip = Hovertip(local_name_entry, hover_delay=500, text="(Optional) name of language in its own script")

        work_dir_label = ttk.Label(self, text="Location of .usfm files:", width=20)
        work_dir_label.grid(row=5, column=1, sticky=W, pady=2)
        self.work_dir_entry = ttk.Entry(self, width=43, textvariable=self.work_dir)
        self.work_dir_entry.grid(row=5, column=2, columnspan=3, sticky=W)
        src_dir_find = ttk.Button(self, text="...", width=2, command=self._onFindWorkDir)
        src_dir_find.grid(row=5, column=5, sticky=W)

        license_file_label = ttk.Label(self, text="License file:", width=20)
        license_file_label.grid(row=6, column=1, sticky=W, pady=2)
        self.file_entry = ttk.Entry(self, width=18, textvariable=self.license_file)
        self.file_entry.grid(row=6, column=2, sticky=W)
        license_file_find = ttk.Button(self, text="...", width=2, command=self._onFindFile)
        license_file_find.grid(row=6, column=3, sticky=W)

        license_type_label = ttk.Label(self, text="License type:", width=20)
        license_type_label.grid(row=6, column=4, sticky=E, pady=2)
        self.license_type_entry = ttk.Entry(self, width=21, textvariable=self.license_type)
        self.license_type_entry.grid(row=6, column=5, sticky=W)

        repo_owner_label = ttk.Label(self, text="Repo owner:", width=20)
        repo_owner_label.grid(row=7, column=1, sticky=W, pady=2)
        repo_owner_entry = ttk.Entry(self, width=18, textvariable=self.repo_owner)
        repo_owner_entry.grid(row=7, column=2, sticky=W)
        tip = Hovertip(repo_owner_entry, hover_delay=500, text="Owner of WACS repo (usually Tech_Advance)")

        repo_name_label = ttk.Label(self, text="Repo name:", width=20)
        repo_name_label.grid(row=7, column=4, sticky=E, pady=2)
        repo_name_entry = ttk.Entry(self, width=21, textvariable=self.repo_name)
        repo_name_entry.grid(row=7, column=5, sticky=W)

        self.grid_columnconfigure(2, minsize=16, weight=1)
        # self.grid_columnconfigure(3, minsize=3, weight=2)
        self.grid_columnconfigure(4, minsize=12, weight=2)

    def show_values(self):
        self.changingVars = True
        self.language_code.set(self.getOption('language_code'))
        self.language_name_en.set(self.getOption('language_name'))
        direction = self.getOption('direction')
        self.direction.set(direction if direction else 'ltr')
        self.localized_name.set(self.getOption('localized_name'))
        self.work_dir.set(self.getOption('work_dir'))
        self.license_file.set(self.getOption('license_file'))
        license_type = self.getOption('license_type')
        self.license_type.set(license_type if license_type else 'CC-BY-SA 4.0')
        owner = self.getOption('repo_owner')
        self.repo_owner.set(owner if owner else 'Tech_Advance')
        repo = self.getOption('repo_name')
        self.repo_name.set(repo if repo else f"{self.language_code.get()}_reg")

        # Create buttons
        self.controller.showbutton(1, "<<<", self._onBack, tip="Verify USFM")
        self.controller.showbutton(2, "GO", self._onExecute)     # no tip since we bind the <Enter> event
        self.controller.bindButtonEvent(2, "<Enter>", self._onCheckInputs)
        self.controller.showbutton(3, "Work folder", self._onOpenWorkDir)
        self.controller.showbutton(4, "VERIFY", self._onVerifyMetadata, tip="Verify existing metadata files")
        self.controller.showbutton(5, ">>>", self._onNext, tip="Next step")

        self.language_code.trace_add("write", self._onChangeLanguage)
        self.language_name_en.trace_add("write", self._onChangeLanguageName)
        self.localized_name.trace_add("write", self._onChangeLanguageName)
        self.work_dir.trace_add("write", self._onChangeWorkDir)
        self.license_file.trace_add("write", self._set_button_status)
        self.license_type.trace_add("write", self._set_button_status)
        self.repo_owner.trace_add("write", self._set_button_status)
        self.repo_name.trace_add("write", self._set_button_status)
        self.changingVars = False
        self._set_button_status()

    def onScriptEnd(self):
        self.message_area['state'] = DISABLED   # prevents insertions to message area
        self.controller.enablebutton(2, True)
        self.controller.enablebutton(4, False)
        self.controller.enablebutton(5, True)

    # Returns the entered values as a dict.
    def get_entered_values(self):
        values = {}
        values['language_code'] = self.language_code.get()
        values['language_name_en'] = self.language_name_en.get()
        direction = self.direction.get()
        values['direction'] = direction if direction else 'ltr'
        values['localized_name'] = self.localized_name.get()
        values['work_dir'] = self.work_dir.get()
        values['license_file'] = self.license_file.get()
        values['license_type'] = self.license_type.get()
        values['repo_owner'] = self.repo_owner.get()
        values['repo_name'] = self.repo_name.get()
        return values

    # Returns a list of incomplete or incorrect inputs.
    # Used by _onExecute().
    # Is also called before values are saved to configuration files.
    # Is also called when the mouse hovers over the Verify button.
    def invalidInputs(self, *args):
        objections = []
        language_code = self.language_code.get()
        working_folder = self.work_dir.get()
        language_name = self.language_name_en.get()
        repo_owner = self.repo_owner.get()
        repo_name = self.repo_name.get()
        license_file = self.license_file.get()
        license_type = self.license_type.get()

        if not language_code:
            objections.append("Language code is required.")
        if not language_name:
            objections.append("Language name is required.")
        if not repo_owner or not repo_name:
            objections.append("Repository owner and name are required.")
        if not license_file or not license_type:
            objections.append("License file and type are required.")
        if working_folder:
            if not os.path.isdir(working_folder):
                objections.append(f"{working_folder} is not a valid folder.")
            elif g_util.count_files(working_folder, ".*sfm$") == 0:
                objections.append(f"{working_folder} does not contain any USFM files.")
        else:
            objections.append("Working folder is required.")

        if not objections:  # Only do this check if all other checks pass
            my = ManifestYaml()
            my.load(working_folder)
            if mycode := my.getLanguageId():
                if mycode != language_code:
                    objections.append(f"Language code {language_code} doesn't match existing manifest.yaml at {working_folder}")
            burrito = Burrito(working_folder)
            if burrito.load():
                if burrito.contents and burrito.getLanguageCode() != language_code:
                    objections.append(f"Language code {language_code} doesn't match existing metadata.json at {working_folder}")
        return objections

    def _onFindWorkDir(self, *args):
        self.controller.askdir(self.work_dir)
    def _onFindFile(self, *args):
        path = filedialog.askopenfilename(initialdir=self.work_dir.get(), title = "Select license file")
        if path:
            self.license_file.set(os.path.basename(path))

    # Called when the language code changes.
    def _onChangeLanguage(self, *args):
        code = self.language_code.get()
        if not code:
            self.language_name_en.set("")
            self.repo_name.set("")
        else:
            self.repo_name.set(f"{code}_reg")
            self._set_button_status()

    def _onChangeLanguageName(self, *args):
        language_name = self.language_name_en.get()
        if not language_name.isascii():
            self.clear_show(f"Warning: '{language_name}' is not entirely ASCII. Make sure this is the anglicized name.")
        self._set_button_status()

    def _onChangeWorkDir(self, *args):
        self.changingVars = True
        dir = self.work_dir.get()
        if os.path.isdir(dir):
            my = ManifestYaml()
            my.load(dir)
            language_code = my.getLanguageId()
            if language_code != self.language_code.get():   # to avoid xs callbacks
                self.language_code.set(language_code)       # will invoke _onChangeLanguage
        self.changingVars = False
        self._set_button_status()

    def _onOpenWorkDir(self, *args):
        os.startfile(self.work_dir.get())

    def _onVerifyMetadata(self, *args):
        self._save_values()
        # self.controller.revertChanges()
        # self.controller.enablebutton(4, False)

    def _set_button_status(self, *args):
        if not self.changingVars:
            good_workdir = os.path.isdir( self.work_dir.get() )
            self.controller.enablebutton(3, good_workdir)

            self.cleanup_ready = not self.invalidInputs()
            self.controller.enablebutton(2, self.cleanup_ready)
            self.controller.enablebutton(4, False)  # This function is not ready yet
