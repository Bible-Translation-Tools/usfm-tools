# -*- coding: utf-8 -*-
# GUI interface for USFM file verification
#

from tkinter import ttk
from tkinter import font
from tkinter import filedialog
from tkinter import StringVar, BooleanVar, W, E, DISABLED
from idlelib.tooltip import Hovertip
import g_util
import g_step
import os
import time
from projectinfo import ProjectInfo
from manifestyaml import ManifestYaml

stepname = 'VerifyUSFM'   # equals the main class name in this module

class VerifyUSFM(g_step.Step):
    def __init__(self, mainframe, mainapp):
        super().__init__(mainframe, mainapp, stepname, "Verify USFM")
        self.frame = VerifyUSFM_Frame(mainframe, self)
        self.frame.grid(row=1, column=0, sticky="nsew")
        self.executed = False

    def name(self):
        return stepname

    def onNext(self):
        if self.executed:
            super().onNext('source_dir', 'filename', 'standard_chapter_title')
        else:
            super().onNext()
        self.executed = False

    def onExecute(self, values):
        self.enablebutton(2, False)
        self.enablebutton(3, False)
        # self.values = values    # redundant, they were the same dict to begin with
        count = 1
        if not values['filename']:
            count = g_util.count_files(values['source_dir'], ".*sfm$")
        self.mainapp.execute_script("verifyUSFM", count)
        self.frame.clear_messages()
        self.executed = True

    def executeInventoryLabels(self):
        self.mainapp.execute_script("inventory_chapter_labels", 0)
        self.frame.clear_messages()

class VerifyUSFM_Frame(g_step.Step_Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.changingVars = False

        self.language_code = StringVar()
        self.source_dir = StringVar()
        self.filename = StringVar()
        self.std_titles = StringVar()
        self.compare_dir = StringVar()
        self.language_code.trace_add("write", self._onChangeLanguage)
        self.source_dir.trace_add("write", self._onChangeSourceDir)
        self.filename.trace_add("write", self._set_button_status)
        self.compare_dir.trace_add("write", self._set_button_status)
        self.suppress = [BooleanVar(value = False) for i in range(13)]
        self.suppress[6].trace_add("write", self._onChangeQuotes)
        self.suppress[7].trace_add("write", self._onChangeQuotes)
        for col in [2,3,4]:
            self.columnconfigure(col, weight=1)   # keep column 1 from expanding
        # self.rowconfigure(88, minsize=170, weight=1)  # let the message expand vertically

        # language_code will be used for ProjectInfo soon in verifyUSFM.
        language_code_label = ttk.Label(self, text="Language code:", width=20)
        language_code_label.grid(row=3, column=1, sticky="wen", pady=2)
        language_code_entry = ttk.Entry(self, width=18, textvariable=self.language_code)
        language_code_entry.grid(row=3, column=2, sticky=W)
        std_titles_label = ttk.Label(self, text="Standard chapter title:", width=20)
        std_titles_label.grid(row=3, column=3, sticky=E)
        std_titles_entry = ttk.Entry(self, width=18, textvariable=self.std_titles)
        std_titles_entry.grid(row=3, column=4, sticky=W)
        std_titles_helper = ttk.Button(self, text="...", width=2, command=self._onInventoryLabels)
        std_titles_helper.grid(row=3, column=5, sticky=W)
        helper_Tip = Hovertip(std_titles_helper, hover_delay=500,
            text="Inventory existing chapter labels")

        source_dir_label = ttk.Label(self, text="Location of .usfm files:", width=20)
        source_dir_label.grid(row=4, column=1, sticky=W, pady=2)
        source_dir_entry = ttk.Entry(self, width=41, textvariable=self.source_dir)
        source_dir_entry.grid(row=4, column=2, columnspan=3, sticky=W)
        src_dir_find = ttk.Button(self, text="...", width=2, command=self._onFindSrcDir)
        src_dir_find.grid(row=4, column=4, sticky=W)
        file_label = ttk.Label(self, text="File name:", width=20)
        file_label.grid(row=5, column=1, sticky=W, pady=2)
        file_entry = ttk.Entry(self, width=20, textvariable=self.filename)
        file_entry.grid(row=5, column=2, columnspan=3, sticky=W)
        file_Tip = Hovertip(file_entry, hover_delay=500,
             text="Leave filename blank to verify all .usfm files in the folder.")
        file_find = ttk.Button(self, text="...", width=2, command=self._onFindFile)
        file_find.grid(row=5, column=3, sticky=W, padx=12)
        compare_dir_label = ttk.Label(self, text="Source text folder:", width=20)
        compare_dir_label.grid(row=6, column=1, sticky=W, pady=2)
        compare_dir_entry = ttk.Entry(self, width=41, textvariable=self.compare_dir)
        compare_dir_entry.grid(row=6, column=2, columnspan=3, sticky=W)
        cmp_Tip = Hovertip(compare_dir_entry, hover_delay=500,
             text="The source text used for this translation. (Optional but recommended)")
        cmp_dir_find = ttk.Button(self, text="...", width=2, command=self._onFindCmpDir)
        cmp_dir_find.grid(row=6, column=4, sticky=W)

        subheadingFont = font.Font(size=10, slant='italic')     # normal size is 9
        suppressions_label = ttk.Label(self, text="Suppress these warnings?", font=subheadingFont)
        suppressions_label.grid(row=10, column=1, columnspan=2, sticky=W, pady=(4,2))

        suppress1_checkbox = ttk.Checkbutton(self, text='Numbers', variable=self.suppress[1],
                                             onvalue=True, offvalue=False)
        suppress1_checkbox.grid(row=11, column=1, sticky=W)
        suppress1_Tip = Hovertip(suppress1_checkbox, hover_delay=500,
             text="Suppress all warnings about numbers. (possible verse number in verse, space in number, number prefix/suffix, etc.)")
        suppress2_checkbox = ttk.Checkbutton(self, text=r'No \p after \c', variable=self.suppress[2],
                                             onvalue=True, offvalue=False)
        suppress2_checkbox.grid(row=11, column=2, sticky=W)
        suppress2_Tip = Hovertip(suppress2_checkbox, hover_delay=500,
             text=r"Suppress warnings about missing paragraph marker before verse 1. (needed by PTX-Print)")
        suppress3_checkbox = ttk.Checkbutton(self, text=r'Punctuation', variable=self.suppress[3],
                                             onvalue=True, offvalue=False)
        suppress3_checkbox.grid(row=11, column=3, sticky=W)
        suppress3_Tip = Hovertip(suppress3_checkbox, hover_delay=500,
             text=r"Suppress most warnings about punctuation")
        suppress4_checkbox = ttk.Checkbutton(self, text=r'Useless markers', variable=self.suppress[4],
                                             onvalue=True, offvalue=False)
        suppress4_checkbox.grid(row=11, column=4, sticky=W)
        suppress4_Tip = Hovertip(suppress4_checkbox, hover_delay=500,
             text=r"Suppress warnings about invalid placement of paragraph/poetry markers")
        suppress5_checkbox = ttk.Checkbutton(self, text=r'Verse counts', variable=self.suppress[5],
                                             onvalue=True, offvalue=False)
        suppress5_checkbox.grid(row=12, column=1, sticky=W)
        suppress5_Tip = Hovertip(suppress5_checkbox, hover_delay=500,
             text=r"Suppress checks for verse counts")
        suppress6_checkbox = ttk.Checkbutton(self, text=r'Straight quotes', variable=self.suppress[6],
                                             onvalue=True, offvalue=False)
        suppress6_checkbox.grid(row=12, column=2, sticky=W)
        suppress6_Tip = Hovertip(suppress6_checkbox, hover_delay=500,
             text=r"Suppress warnings about straight double and single quotes")

        self.suppress7_checkbox = ttk.Checkbutton(self, text=r'Straight single quotes', variable=self.suppress[7],
                                             onvalue=True, offvalue=False)
        self.suppress7_checkbox.grid(row=12, column=3, sticky=W)
        suppress7_Tip = Hovertip(self.suppress7_checkbox, hover_delay=500,
             text=r"Suppress warnings about straight single quotes  (report straight double quotes only)")

        suppress8_checkbox = ttk.Checkbutton(self, text=r'Book titles', variable=self.suppress[8],
                                             onvalue=True, offvalue=False)
        suppress8_checkbox.grid(row=12, column=4, sticky=W)
        suppress8_Tip = Hovertip(suppress8_checkbox, hover_delay=500,
             text=r"Suppress warnings about UPPER CASE BOOK TITLES")

        suppress10_checkbox = ttk.Checkbutton(self, text=r'Capitalization', variable=self.suppress[10],
                                             onvalue=True, offvalue=False)
        suppress10_checkbox.grid(row=13, column=2, sticky=W)
        suppress10_Tip = Hovertip(suppress10_checkbox, hover_delay=500,
             text=r'Suppress "First word not capitalized" warnings; report totals only')

        suppress11_checkbox = ttk.Checkbutton(self, text=r'Paragraph termination', variable=self.suppress[11],
                                             onvalue=True, offvalue=False)
        suppress11_checkbox.grid(row=13, column=3, sticky=W)
        suppress11_Tip = Hovertip(suppress11_checkbox, hover_delay=500,
             text=r'Suppress "Punctuation missing at end of paragraph" warnings; report totals only')

        suppress12_checkbox = ttk.Checkbutton(self, text=r'Mixed-case words', variable=self.suppress[12],
                                             onvalue=True, offvalue=False)
        suppress12_checkbox.grid(row=13, column=4, sticky=W)

        self.message_area['wrap'] = "none"
        xs = ttk.Scrollbar(self, orient = 'horizontal', command = self.message_area.xview)
        xs.grid(row=89, column = 1, columnspan=4, sticky = 'ew')
        self.message_area['xscrollcommand'] = xs.set

    def show_values(self, values):
        self.changingVars = True
        self.values = values
        code = values.get('language_code', fallback="")
        dir = values.get('source_dir', fallback="")
        cmp = values.get('compare_dir', fallback="")
        self.language_code.set(code)
        self.source_dir.set(dir)
        self.compare_dir.set(cmp)
        if dir and code and not cmp:
            self.compare_dir.set( self._getCompareValue(dir, code, cmp) )
        self.filename.set(values.get('filename', fallback=""))
        self.std_titles.set(values.get('standard_chapter_title', fallback=""))
        for si in range(len(self.suppress)):
            configvalue = f"suppress{si}"
            self.suppress[si].set( values.get(configvalue, fallback = False))

        # Create buttons
        self.controller.showbutton(1, "<<<", tip="Previous step", cmd=self._onBack)
        self.controller.showbutton(2, "VERIFY", tip="Check the USFM files now.", cmd=self._onExecute)
        self.controller.showbutton(3, "Open issues.txt", tip="Open issues.txt file in your default editor",
                                   cmd=self._onOpenIssues)
        nextstep = self.controller.mainapp.nextstepname()
        if nextstep == "Usfm2Usx":
            tip = "Convert to resource container"
        else:
            tip = "Automated USFM file cleanup"
        self.controller.showbutton(5, ">>>", tip=tip, cmd=self._onNext)
        self.changingVars = False
        self._set_button_status()

    def _onExecute(self):
        objections = self._invalidInputs()
        if len(objections) == 0:
            self._save_values()
            self.controller.onExecute(self.values)
        else:
            for objection in objections:
                self.message_area.insert('end', f"{objection}\n")

    def onScriptEnd(self):
        issuespath = os.path.join(self.values['source_dir'], "issues.txt")
        exists = os.path.isfile(issuespath)
        self.controller.enablebutton(3, exists)
        self.controller.enablebutton(2, self.verify_ready)
        if exists:
            if time.time() - os.path.getmtime(issuespath) < 10:     # issues.txt is recent
                self.message_area.insert('end', "issues.txt contains the list of issues found.\n")
                self.message_area.insert('end', "Make corrections using your text editor, or go to\n  Next Step to do automated cleanup.\n")
                self.message_area.see('end')
        self.message_area['state'] = DISABLED   # prevents insertions to message area

    # Copies current values from GUI into self.values dict, and calls mainapp to save
    # them to the configuration file.
    def _save_values(self):
        self.values['language_code'] = self.language_code.get()
        self.values['source_dir'] = self.source_dir.get()
        self.values['filename'] = self.filename.get()
        value = self.compare_dir.get()
        self.values['compare_dir'] = "" if value.startswith("(locate") else value
        self.values['standard_chapter_title'] = self.std_titles.get()
        for si in range(len(self.suppress)):
            configvalue = f"suppress{si}"
            self.values[configvalue] = str(self.suppress[si].get())
        self.controller.mainapp.save_values(stepname, self.values)

    # This function does more thorough input validation than _set_button_status() does.
    # The user may need this help in identifying certain incorrect input(s).
    def _invalidInputs(self):
        objections = []
        code = self.language_code.get()
        dir = self.source_dir.get()
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
        return objections

    # Executes a script that inventories the existing chapter labels
    def _onInventoryLabels(self, *args):
        self._save_values()
        self.controller.executeInventoryLabels()

    def _onFindSrcDir(self, *args):
        self.controller.askdir(self.source_dir)
    def _onFindFile(self, *args):
        path = filedialog.askopenfilename(initialdir=self.source_dir.get(), title = "Select usfm file",
                                           filetypes=[('Usfm file', '*.usfm')])
        if path:
            self.filename.set(os.path.basename(path))

    def _onFindCmpDir(self, *args):
        dir = self.source_dir.get()
        code = self.language_code.get()
        msg = self._getCompareValue(dir, code, "")
        self.controller.askdir(self.compare_dir, msg)

    # Called when the language code changes.
    def _onChangeLanguage(self, *args):
        self.std_titles.set("")
        code = self.language_code.get()
        if code:
            dir = self.source_dir.get()
            cmp = self.compare_dir.get()
            self.compare_dir.set( self._getCompareValue(dir, code, cmp) )
            # invokes _set_button_status() implicitly
        else:
            self._set_button_status()

    def _onChangeSourceDir(self, *args):
        self.changingVars = True
        dir = self.source_dir.get()
        code = self.language_code.get()
        if os.path.isdir(dir):
            my = ManifestYaml()
            my.load(dir)
            code = my.getLanguageId()
            if code != self.language_code.get():
                self.language_code.set(code)    # this will invoke _onChangeLanguage()
        self.changingVars = False
        self._set_button_status()

    def _onChangeQuotes(self, *args):
        if suppress_all := self.suppress[6].get():    # suppress all straight quotes
            self.suppress[7].set(True)
        self.suppress7_checkbox.state(['disabled'] if suppress_all else ['!disabled'])
        if not self.suppress[7].get():
            self.suppress[6].set(False)

    def _onOpenIssues(self, *args):
        self._save_values()
        path = os.path.join(self.values['source_dir'], "issues.txt")
        os.startfile(path)
    # Opens usfm folder, or specific usfm file
    def _onOpenUsfm(self, *args):
        path = os.path.join(self.source_dir.get(), self.filename.get())
        os.startfile(path)

    def _set_button_status(self, *args):
        if not self.changingVars:
            good_code = self.language_code.get()
            good_dir = os.path.isdir(self.source_dir.get())
            good_cmp = not self.compare_dir.get() or os.path.isdir(self.compare_dir.get())
            namedfile = self.filename.get()
            good_subject = good_dir and not namedfile
            if good_dir and namedfile:
                filepath = os.path.join(self.source_dir.get(), namedfile)
                good_subject = os.path.isfile(filepath)
            self.verify_ready = good_code and good_subject and good_cmp
            self.controller.enablebutton(2, self.verify_ready)
            if good_dir:
                title = namedfile if namedfile and good_subject else "Work folder"
                self.controller.showbutton(4, title, tip=f"Open {title}", cmd=self._onOpenUsfm)
            else:
                self.controller.hidebutton(4)

            issuespath = os.path.join(self.source_dir.get(), "issues.txt")
            self.controller.enablebutton(3, os.path.isfile(issuespath))

    # Only called when the language code changes.
    # Returns the most reasonable new value for compare_dir,
    # based on existence of project info, if any.
    # The value returned may be a suggestion of the main source text, not necessarily a folder name.
    def _getCompareValue(self, dir, language_code, cmp):
        change_cmp = False
        if language_code and dir and os.path.isdir(dir):
            projectInfo = ProjectInfo(dir, language_code)
            projectInfo.useManifest()
            if not cmp or cmp.startswith("(locate"):
                change_cmp = True
            else:   # cmp is already set to a folder
                change_cmp = False
                cmpYaml = ManifestYaml()
                errors = cmpYaml.load(cmp)
                if not errors:
                    if not projectInfo.knownSource(cmpYaml.getLanguageId(), cmpYaml.getResourceId()):
                        change_cmp = True
        if change_cmp:
            if mainsrc := projectInfo.getMainSource():
                cmp = f"(locate folder containing {mainsrc['language_id']}_{mainsrc['resource_id']}, vrsn ~{mainsrc['version']})"
                if "nspecified" in cmp or "nknown" in cmp:
                    cmp = ""
            else:
                cmp = ""
        return cmp
