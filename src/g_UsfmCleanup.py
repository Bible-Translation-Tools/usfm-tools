# -*- coding: utf-8 -*-
# GUI interface for automated USFM file cleanup
#

# from tkinter import *
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

stepname = 'UsfmCleanup'   # equals the main class name in this module

class UsfmCleanup(g_step.Step):
    def __init__(self, mainframe, mainapp):
        super().__init__(mainframe, mainapp, stepname, "USFM Cleanup")
        self.frame = UsfmCleanup_Frame(mainframe, self)
        self.frame.grid(row=1, column=0, sticky="nsew")
        self.executed = False

    def name(self):
        return stepname

    def onNext(self):
        if self.executed:
            super().onNext('language_code', 'work_dir', 'filename', 'compare_dir')
        else:
            super().onNext()
        self.executed = False

    def onExecute(self):
        self.enablebutton(2, False)
        count = 1
        if not self.getOption('filename'):
            count = g_util.count_files(self.getOption('work_dir'), ".*sfm$")
        self.mainapp.execute_script("usfm_cleanup", count)
        self.frame.clear_messages()
        self.executed = True

    # Temporary function, until "source_dir" is fully retired.
    def getWorkDir(self):
        workdir = self.getOption('work_dir')
        if not workdir:
            workdir = self.getOption('source_dir')
        return workdir

    # Runs the revertChanges script to revert usfm_cleanup changes.
    def revertChanges(self):
        sec = {'work_dir': self.getWorkDir(),
               'backupExt': ".usfm.orig",
               'correctExt': ".usfm"}
        self.mainapp.save_values('RevertChanges', sec)
        self.mainapp.execute_script("revertChanges", 1)
        self.frame.clear_messages()

    def executeInventoryLabels(self):
        self.mainapp.execute_script("inventory_chapter_labels", 0)
        self.frame.clear_messages()

class UsfmCleanup_Frame(g_step.Step_Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.changingVars = False

        self.language_code = StringVar()
        self.work_dir = StringVar()
        self.filename = StringVar()
        self.compare_dir = StringVar()
        self.std_titles = StringVar()
        self.enable = [BooleanVar(value = False) for i in range(9)]

        language_code_label = ttk.Label(self, text="Language code:", width=20)
        language_code_label.grid(row=3, column=1, sticky="wen", pady=2)
        language_code_entry = ttk.Entry(self, width=18, textvariable=self.language_code)
        language_code_entry.grid(row=3, column=2, sticky=W)
        std_titles_label = ttk.Label(self, text="Standard chapter title:", width=20)
        std_titles_label.grid(row=3, column=3, sticky=E)
        std_titles_entry = ttk.Entry(self, width=18, textvariable=self.std_titles)
        std_titles_entry.grid(row=3, column=4, sticky=W)
        std_title_Tip = Hovertip(std_titles_entry, hover_delay=500,
             text="Leave blank if unknown.")
        std_titles_helper = ttk.Button(self, text="...", width=2, command=self._onInventoryLabels)
        std_titles_helper.grid(row=3, column=5, sticky=W)
        helper_Tip = Hovertip(std_titles_helper, hover_delay=500,
            text="Inventory existing chapter labels")

        work_dir_label = ttk.Label(self, text="Location of .usfm files:", width=20)
        work_dir_label.grid(row=4, column=1, sticky=W, pady=2)
        self.work_dir_entry = ttk.Entry(self, width=44, textvariable=self.work_dir)
        self.work_dir_entry.grid(row=4, column=2, columnspan=3, sticky=W)
        src_dir_find = ttk.Button(self, text="...", width=2, command=self._onFindWorkDir)
        src_dir_find.grid(row=4, column=4, sticky=W)

        file_label = ttk.Label(self, text="File name:", width=20)
        file_label.grid(row=5, column=1, sticky=W, pady=2)
        self.file_entry = ttk.Entry(self, width=22, textvariable=self.filename)
        self.file_entry.grid(row=5, column=2, sticky=W)
        file_Tip = Hovertip(self.file_entry, hover_delay=500,
             text="Leave filename blank to clean all .usfm files in the folder.")
        file_find = ttk.Button(self, text="...", width=2, command=self._onFindFile)
        file_find.grid(row=5, column=3, sticky=W)


        compare_dir_label = ttk.Label(self, text="Source text folder:", width=20)
        compare_dir_label.grid(row=6, column=1, sticky=W, pady=2)
        compare_dir_entry = ttk.Entry(self, width=41, textvariable=self.compare_dir)
        compare_dir_entry.grid(row=6, column=2, columnspan=3, sticky=W)
        cmp_Tip = Hovertip(compare_dir_entry, hover_delay=500,
             text="The source text used for this translation. (Optional but recommended)")
        cmp_dir_find = ttk.Button(self, text="...", width=2, command=self._onFindCmpDir)
        cmp_dir_find.grid(row=6, column=4, sticky=W)

        subheadingFont = font.Font(size=10, slant='italic')     # normal size is 9
        enable_label = ttk.Label(self, text="Optional fixes:",
                                 font=subheadingFont)
        enable_label.grid(row=10, column=1, columnspan=2, sticky=W, pady=(4,2))
        helper_Tip = Hovertip(enable_label, hover_delay=500,
            text="Enable these fixes in addition to the standard ones.")

        # enable1_checkbox = ttk.Checkbutton(self, text='Spaces', variable=self.enable[1],
        #                                      onvalue=True, offvalue=False)
        # enable1_checkbox.grid(row=11, column=1, sticky=W)
        # enable1_Tip = Hovertip(enable1_checkbox, hover_delay=500,
        #      text="Add spaces between comma/period/colon and a letter (recommended for most languages).")

        enable2_checkbox = ttk.Checkbutton(self, text='Punctuation', variable=self.enable[2],
                                             onvalue=True, offvalue=False)
        enable2_checkbox.grid(row=11, column=1, sticky=W)
        enable2_Tip = Hovertip(enable2_checkbox, hover_delay=500,
             text="Fix double periods, doubled angle brackets, other \"safe\" substitutions (recommended for most languages).")

        self.enable3_checkbox = ttk.Checkbutton(self, text='Promote dbl quotes', variable=self.enable[3],
                                             onvalue=True, offvalue=False)
        self.enable3_checkbox.grid(row=11, column=2, sticky=W)
        enable3_Tip = Hovertip(self.enable3_checkbox, hover_delay=500,
             text="Promote straight double quotes to curly quotes.")

        self.enable4_checkbox = ttk.Checkbutton(self, text='Promote quotes', variable=self.enable[4],
                                             onvalue=True, offvalue=False)
        self.enable4_checkbox.grid(row=11, column=3, sticky=W)
        enable4_Tip = Hovertip(self.enable4_checkbox, hover_delay=500,
             text="Promote single and double straight quotes to curly quotes, except word-medial.")
        self.grid_columnconfigure(2, minsize=16, weight=1)
        self.grid_columnconfigure(3, minsize=16, weight=2)
        self.grid_columnconfigure(4, minsize=16, weight=3)

        # enable5_checkbox = ttk.Checkbutton(self, text='Capitalization', variable=self.enable[5],
        #                                      onvalue=True, offvalue=False)
        # enable5_checkbox.grid(row=11, column=2, sticky=W)
        # enable5_Tip = Hovertip(enable5_checkbox, hover_delay=500,
        #      text="Enforce capitalization of the first word in sentences, disregarding footnotes.")

        # enable6_checkbox = ttk.Checkbutton(self, text='\s5 markers', variable=self.enable[6],
        #                                      onvalue=True, offvalue=False)
        # enable6_checkbox.grid(row=12, column=2, sticky=W)
        # enable6_Tip = Hovertip(enable6_checkbox, hover_delay=500,
        #      text="Remove \s5 markers (recommended for all text except GLs).")

        enable7_checkbox = ttk.Checkbutton(self, text='Section titles', variable=self.enable[7],
                                           onvalue=True, offvalue=False)
        enable7_checkbox.grid(row=11, column=4, sticky=W)
        enable7_Tip = Hovertip(enable7_checkbox, hover_delay=500,
              text="Mark recognizable section titles with \\s. Disable this option if no section headings exist.")

        # self.enable8_checkbox = ttk.Checkbutton(self, text='Chapter labels', variable=self.enable[8],
        #                                      onvalue=True, offvalue=False)
        # self.enable8_checkbox.grid(row=12, column=4, sticky=W)
        # enable8_Tip = Hovertip(self.enable8_checkbox, hover_delay=500,
        #      text="Standardize chapter labels.")
        # self.enable8_checkbox.state(['disabled'])

    # Temporary function, until "source_dir" is fully retired.
    def getWorkDirConfigValue(self):
        workdir = self.getOption('work_dir')
        if not workdir:
            workdir = self.getOption('source_dir')  # the old name
        return workdir

    def show_values(self):
        code = self.getOption('language_code')
        dir = self.getWorkDirConfigValue()
        self.language_code.set(code)
        self.work_dir.set(dir)
        self.filename.set(self.getOption('filename'))
        self.std_titles.set(self.getOption('standard_chapter_title'))
        self.set_language_fields(code, dir)     # this may overwrite chapter title
        for i in range(len(self.enable)):
            configvalue = f"enable{i}"
            self.enable[i].set(self.getBooleanOption(configvalue))

        # Create buttons
        self.controller.showbutton(1, "<<<", self._onBack, tip="Verify USFM")
        self.controller.showbutton(2, "CLEAN", self._onExecute)     # no tip since we bind the <Enter> event
        self.controller.bindButtonEvent(2, "<Enter>", self._onCheckInputs)
        self.controller.showbutton(3, "Work folder", self._onOpenWorkDir)
        self.controller.showbutton(4, "Undo", self._onUndo, tip="Restore any and all .usfm.orig backup files.")
        # self.controller.bindButtonEvent(4, "<Enter>", self._onCheckInputs)
        self.controller.showbutton(5, ">>>", self._onNext, tip="Next step")

        self.language_code.trace_add("write", self._onChangeLanguage)
        self.work_dir.trace_add("write", self._onChangeWorkDir)
        self.filename.trace_add("write", self._set_button_status)
        self.compare_dir.trace_add("write", self._set_button_status)
        self.enable[3].trace_add("write", self._onChangeQuotes)
        self.enable[4].trace_add("write", self._onChangeQuotes)
        self._set_button_status()

    # Called when Step is activated, and when the source dir or language code changes.
    # Sets compare_dir, based on existence of project info, if any.
    # May set standard chapter title, based on project info, if any.
    def set_language_fields(self, code, dir):
        projectInfo = None
        if dir and code:
            projectInfo = ProjectInfo(dir, code)
            cmp = projectInfo.getSourceDir()
            if not cmp:
                # cmp = self._getCompareValue(dir, code, "")
                if not projectInfo.getMainSource():
                    projectInfo.useManifest(docreate=False)
                if mainsrc := projectInfo.getMainSource():
                    cmp = f"(locate folder containing {mainsrc['language_id']}_{mainsrc['resource_id']}, vrsn ~{mainsrc['version']})"
                    if "nspecified" in cmp or "nknown" in cmp:
                        cmp = ""
                else:
                    cmp = ""
        else:
            cmp = ""
        self.compare_dir.set(cmp)   # calls _set_button_status() implicitly
        self.clear_show("")     # clears the previous source text hints, if any

        if projectInfo:
            title = projectInfo.getStandardChapterTitle()
            self.std_titles.set(title)

    def onScriptEnd(self):
        self.message_area['state'] = DISABLED   # prevents insertions to message area
        self.controller.enablebutton(2, self.cleanup_ready)
        nChanged = g_util.count_files(self.work_dir.get(), r".*\.usfm\.orig$")
        self.controller.enablebutton(4, nChanged > 0)
        self.controller.enablebutton(5, True)

    def _onChangeQuotes(self, *args):
        if promote_all := self.enable[4].get():    # promote all straight quotes
            self.enable[3].set(True)
        self.enable3_checkbox.state(['disabled'] if promote_all else ['!disabled'])
        if not self.enable[3].get():
            self.enable[4].set(False)

    # Returns the entered values as a dict.
    def get_entered_values(self):
        values = {}
        values['language_code'] = self.language_code.get()
        values['work_dir'] = self.work_dir.get()
        values['filename'] = self.filename.get()
        value = self.compare_dir.get()
        values['compare_dir'] = "" if value.startswith("(locate") else value
        values['standard_chapter_title'] = self.std_titles.get()
        for si in [2,3,4,7]:
            configvalue = f"enable{si}"
            values[configvalue] = str(self.enable[si].get())
        values['enable1'] = "True" # Spaces
        values['enable5'] = "True" # Capitalization
        values['enable6'] = "True" # \s5 markers
        values['enable8'] = "True" if self.std_titles.get() else "False"
        return values

    # Returns a list of incomplete or incorrect inputs.
    # Used by _onExecute().
    # Is also called before values are saved to configuration files.
    # Is also called when the mouse hovers over the Verify button.
    def invalidInputs(self, *args):
        objections = []
        code = self.language_code.get()
        dir = self.work_dir.get()
        cmp = self.compare_dir.get()
        namedfile = self.filename.get()

        if not code:
            objections.append("Language code is required.")
        if not dir:
            objections.append("Usfm file folder must be specified.")
        if dir and not os.path.isdir(dir):
            objections.append(f"{dir} is not a valid folder.")
        if dir and namedfile:
            filepath = os.path.join(dir, namedfile)
            if not os.path.isfile(filepath):
                objections.append(f"{filepath} is not a valid file")
        if cmp and not os.path.isdir(cmp):
            objections.append(f"Source text folder is invalid.")
        if cmp and cmp == dir:
            objections.append(f"The usfm file folder ({dir})\n  can't be the same as its Source text folder.")

        if not objections:  # Only do this check if all other checks pass
            my = ManifestYaml()
            my.load(dir)
            if mycode := my.getLanguageId():
                if mycode != code:
                    objections.append(f"Language code doesn't match manifest at {dir}")
                    objections.append(f"{code} vs. {mycode}")
        return objections

    def save_project_info(self):
        projectInfo = None
        compare_dir = self.compare_dir.get()
        if compare_dir and not compare_dir.startswith("(locate"):
            projectInfo = ProjectInfo(self.work_dir.get(), self.language_code.get())
            projectInfo.setSourceDir(compare_dir)
            projectInfo.save()

        std_titles = self.std_titles.get()
        if not projectInfo:
            projectInfo = ProjectInfo(self.work_dir.get(), self.language_code.get())
        if std_titles != projectInfo.getStandardChapterTitle():
            projectInfo.setStandardChapterTitle(std_titles)
            projectInfo.save()

    def _onFindWorkDir(self, *args):
        self.controller.askdir(self.work_dir)
    def _onFindFile(self, *args):
        path = filedialog.askopenfilename(initialdir=self.work_dir.get(), title = "Select usfm file",
                                           filetypes=[('Usfm file', '*.usfm')])
        if path:
            self.filename.set(os.path.basename(path))

    # Executes a script that inventories the existing chapter labels
    def _onInventoryLabels(self, *args):
        self._save_values()
        self.controller.executeInventoryLabels()

    # Called when the language code changes.
    def _onChangeLanguage(self, *args):
        code = self.language_code.get()
        if code:
            self.set_language_fields(code, self.work_dir.get())
        else:
            self.std_titles.set("")
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
            else:
                self.set_language_fields(language_code, dir)
        self.changingVars = False
        self._set_button_status()

    def _onOpenWorkDir(self, *args):
        os.startfile(self.work_dir.get())

    def _onFindCmpDir(self, *args):
        hints = self._list_sources()
        if hints:
            hints = "Locate the folder, for one of these source texts:\n" + hints
            self.clear_show(hints)
        self.controller.askdir(self.compare_dir)

    # Returns a string properly formatted for showing the known sources texts
    # for this translation, and how frequently each was used.
    def _list_sources(self):
        workdir = self.work_dir.get()
        code = self.language_code.get()
        sourcehints = []
        if os.path.isdir(workdir) and code:
            pi = ProjectInfo(workdir, code)
            for src in pi.getSources():
                sourcehints.append(f"  {src['language_id']}_{src['resource_id']}, vrsn ~{src['version']} was used for {src['count']} book(s).")
        return "\n".join(sourcehints)

    def _onUndo(self, *args):
        self._save_values()
        self.controller.revertChanges()
        self.controller.enablebutton(4, False)

    def _set_button_status(self, *args):
        if not self.changingVars:
            good_workdir = os.path.isdir( self.work_dir.get() )
            self.controller.enablebutton(3, good_workdir)

            self.cleanup_ready = not self.invalidInputs()
            self.controller.enablebutton(2, self.cleanup_ready)
            self.controller.enablebutton(4, self.cleanup_ready)
