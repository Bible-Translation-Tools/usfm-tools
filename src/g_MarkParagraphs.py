# -*- coding: utf-8 -*-
# GUI interface for marking paragraphs
#

from tkinter import ttk
from tkinter import font
from tkinter import StringVar, BooleanVar, W, DISABLED
from idlelib.tooltip import Hovertip
import g_util
import g_step
import os
import time
from projectinfo import ProjectInfo
from manifestyaml import ManifestYaml

stepname = 'MarkParagraphs'   # equals the main class name in this module

class MarkParagraphs(g_step.Step):
    def __init__(self, mainframe, mainapp):
        super().__init__(mainframe, mainapp, stepname, "Mark paragraphs and poetry")
        self.frame = MarkParagraphs_Frame(mainframe, self)
        self.frame.grid(row=1, column=0, sticky="nsew")

    def name(self):
        return stepname

    def onExecute(self, values):
        self.enablebutton(2, False)
        self.enablebutton(3, False)
        self.values = values
        count = 1
        if not values['filename']:
            count = g_util.count_files(values['source_dir'], ".*sfm$")
        self.script = "mark_paragraphs"
        self.mainapp.execute_script(self.script, count*2)
        self.frame.clear_messages()

    # Runs the revertChanges script to revert mark_paragraphs changes.
    def revertChanges(self):
        sec = {'source_dir': self.values['source_dir'],
               'backupExt': ".usfmorig",
               'correctExt': ".usfm"}
        self.mainapp.save_values('RevertChanges', sec)
        self.script = "revertChanges"
        self.mainapp.execute_script(self.script, 1)
        self.frame.clear_messages()

    def onNext(self):
        super().onNext('source_dir')

    # Called by the mainapp.
    def onScriptEnd(self, status):
        if status:
            self.frame.show_progress(status)
        nIssues = 0
        if self.script == "mark_paragraphs":
            issuespath = os.path.join(self.values['source_dir'], "issues.txt")
            if os.path.exists(issuespath) and time.time() - os.path.getmtime(issuespath) < 10:     # issues.txt is recent
                nIssues = 1
            else:
                msg = "No issues reported."
                self.frame.show_progress(msg)
        self.enablebutton(2, True)
        self.enablebutton(3, True)
        self.enablebutton(4, True)
        self.enablebutton(5, True)
        self.frame.onScriptEnd(nIssues)

class MarkParagraphs_Frame(g_step.Step_Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.changingVars = False

        self.language_code = StringVar()  # Unused by mark_paragephs.py, but used here for proving other inputs
        self.source_dir = StringVar()
        self.model_dir = StringVar()
        self.filename = StringVar()
        self.copy_nb = BooleanVar(value = False)
        self.remove_s5 = BooleanVar(value = True)
        # self.s5_only = BooleanVar(value = False)
        self.s5_to_p = BooleanVar(value = False)
        self.mark_every_verse = BooleanVar(value = False)
        # self.punctuate = BooleanVar(value = True)
        self.columnconfigure(3, weight=1)   # keep column 1 from expanding
        self.columnconfigure(4, minsize=115)

        language_code_label = ttk.Label(self, text="Language code:", width=20)
        language_code_label.grid(row=3, column=1, sticky="wen", pady=2)
        language_code_entry = ttk.Entry(self, width=18, textvariable=self.language_code)
        language_code_entry.grid(row=3, column=2, sticky=W)
        source_dir_label = ttk.Label(self, text="Location of files\n to be marked:", width=15)
        source_dir_label.grid(row=4, column=1, sticky=W, pady=2)
        self.source_dir_entry = ttk.Entry(self, width=43, textvariable=self.source_dir)
        self.source_dir_entry.grid(row=4, column=2, columnspan=3, sticky=W)
        src_dir_find = ttk.Button(self, text="...", width=2, command=self._onFindSrcDir)
        src_dir_find.grid(row=4, column=4, sticky=W)

        model_dir_label = ttk.Label(self, text="Location of model files:", width=21)
        model_dir_label.grid(row=5, column=1, sticky="ew", pady=2)
        self.model_dir_entry = ttk.Entry(self, width=43, textvariable=self.model_dir)
        self.model_dir_entry.grid(row=5, column=2, columnspan=3, sticky=W)
        model_dir__Tip = Hovertip(self.model_dir_entry, hover_delay=500,
             text="Folder containing USFM files with well marked paragraphs, e.g. English UDB folder")
        model_dir_find = ttk.Button(self, text="...", width=2, command=self._onFindModelDir)
        model_dir_find.grid(row=5, column=4, sticky=W)

        file_label = ttk.Label(self, text="File name:", width=20)
        file_label.grid(row=6, column=1, sticky=W, pady=2)
        self.file_entry = ttk.Entry(self, width=18, textvariable=self.filename)
        self.file_entry.grid(row=6, column=2, sticky=W)
        file_Tip = Hovertip(self.file_entry, hover_delay=500,
             text="Leave filename blank to mark all .usfm files in the folder.")
        file_find = ttk.Button(self, text="...", width=2, command=self._onFindFile)
        file_find.grid(row=6, column=3, sticky=W, padx=5)

        subheadingFont = font.Font(size=10, slant='italic')     # normal size is 9
        enable_label = ttk.Label(self, text="Options:", font=subheadingFont)
        enable_label.grid(row=7, column=1, sticky=W, pady=(4,2))

        copy_nb_checkbox = ttk.Checkbutton(self, text=r'Copy \m, nb and b', variable=self.copy_nb,
                                             onvalue=True, offvalue=False)
        copy_nb_checkbox.grid(row=8, column=1, sticky=W)
        copy_nb_Tip = Hovertip(copy_nb_checkbox, hover_delay=500,
             text=r"Copy \m, \nb and \b markers from model text? (Not usually recommended)")

        self.remove_s5_checkbox = ttk.Checkbutton(self, text=r'Eliminate \s5', variable=self.remove_s5,
                                             onvalue=True, offvalue=False)
        self.remove_s5_checkbox.grid(row=8, column=2, sticky=W)
        remove_s5_Tip = Hovertip(self.remove_s5_checkbox, hover_delay=500,
             text=r"No \s5 in target text. (Always recommended except for GLs)")

        # self.s5_only_checkbox = ttk.Checkbutton(self, text='\\s5 only',
        #                                               variable=self.s5_only, onvalue=True, offvalue=False)
        # self.s5_only_checkbox.grid(row=8, column=3, sticky=W)
        # s5_only_Tip = Hovertip(self.s5_only_checkbox, hover_delay=500,
        #      text="Mark chunks only, not paragraphs.")

        self.s5_to_p_checkbox = ttk.Checkbutton(self, text='\\s5 --> \\p', variable=self.s5_to_p,
                                             onvalue=True, offvalue=False)
        self.s5_to_p_checkbox.grid(row=8, column=3, sticky=W)
        s5_to_p_Tip = Hovertip(self.s5_to_p_checkbox, hover_delay=500,
             text="Make each chunk a paragaph.")

        mark_every_verse_checkbox = ttk.Checkbutton(self, text='Mark every verse',
                                                      variable=self.mark_every_verse, onvalue=True, offvalue=False)
        mark_every_verse_checkbox.grid(row=8, column=4, sticky=W)
        mark_every_verse_checkbox.state(['disabled'])
        mark_every_verse_Tip = Hovertip(mark_every_verse_checkbox, hover_delay=500,
             text=r"(Future) Insert \m before every verse that isn't preceded by \p.")

        # punctuate_checkbox = ttk.Checkbutton(self, text='Punctuate',
        #                                     variable=self.punctuate, onvalue=True, offvalue=False)
        # punctuate_checkbox.grid(row=9, column=1, sticky=W)
        # punctuate_Tip = Hovertip(punctuate_checkbox, hover_delay=500,
        #      text="Add missing end-of-paragraph punctuation (match model text).")

        self.clear_show("This process can copy chunk markers, and paragraph and poetry markers from \
a model text to the file(s) that you specify. If paragraphs are sufficiently marked in your text already, \
and you don't need the \\s5 markers copied over, \
then you don't need to run this process.")

    def show_values(self, values):
        self.values = values
        code = values.get('language_code', fallback="")
        dir = values.get('source_dir', fallback="")
        self.source_dir.set(dir)
        # model_dir = values.get('model_dir', fallback="")
        self.language_code.set(code)
        if not code:
            self.set_language_code(dir)
        self.set_model_dir(code, dir)
        self.filename.set(values.get('filename', fallback=""))
        self.copy_nb.set(values.get('copy_nb', fallback=False))
        self.remove_s5.set(values.get('removeS5markers', fallback=True))
        # self.s5_only.set(values.get('s5_only', fallback=False))
        self.s5_to_p.set(values.get('s5_to_p', fallback=False))
        self.mark_every_verse.set(values.get('mark_every_verse', fallback=False))
        # self.punctuate.set(values.get('punctuate', fallback=True))

        # Create buttons
        self.controller.showbutton(1, "<<<", self._onBack, tip="Verify usfm")
        self.controller.showbutton(2, "MARK", self._onExecute, tip="Mark paragraphs now.")
        self.controller.bindButtonEvent(2, "<Enter>", self._onCheckInputs)
        self.controller.showbutton(3, "Open issues file", self._onOpenIssues,
                                   tip="Open the issues file (which may be from the previous step).")
        self.controller.showbutton(4, "Undo", self._onUndo,
                                   tip="Restore any and all .usfmorig backup files in the folder.")
        self.controller.enablebutton(4, False)
        self.controller.showbutton(5, ">>>", self._onNext, tip="Verify manifest")
        self._set_button_status()
        self.language_code.trace_add("write", self._onChangeLanguage)
        self.source_dir.trace_add("write", self._onChangeSourceDir)
        self.model_dir.trace_add("write", self._set_button_status)
        self.filename.trace_add("write", self._set_button_status)

    # May be called when Step is activated, and when the source dir changes.
    def set_language_code(self, dir):
        if os.path.isdir(dir):
            my = ManifestYaml()
            my.load(dir)
            code = my.getLanguageId()
            if code != self.language_code.get():
                self.language_code.set(code)    # this will invoke _onChangeLanguage()

    # Called when Step is activated, and when the language code changes.
    # Sets model_dir, based on existence of project info, if any.
    def set_model_dir(self, code, dir):
        if code and dir:
            projectInfo = ProjectInfo(dir, code)    # info is in parent of dir
            model_dir = projectInfo.getSourceDir()
            if not model_dir:
                if not projectInfo.getMainSource() : # and os.path.isdir(dir):
                    projectInfo.useManifest(docreate=False)
                if mainsrc := projectInfo.getMainSource():
                    model_dir = f"(locate folder containing {mainsrc['language_id']}_{mainsrc['resource_id']}, vrsn ~{mainsrc['version']})"
                    if "nspecified" in model_dir or "nknown" in model_dir:
                        model_dir = ""
        else:
            model_dir = ""
        self.model_dir.set(model_dir)

    def onScriptEnd(self, nIssues):
        # issuespath = os.path.join(self.values['source_dir'], "issues.txt")
        if nIssues > 0:
            self.message_area.insert('end', "Now issues.txt contains the list of issues encountered in marking paragraphs.\n")
            self.message_area.insert('end', "Resolve as appropriate.\n")
            self.message_area.see('end')
        self.message_area['state'] = DISABLED   # prevents insertions to message area

    # Called when the language code changes.
    def _onChangeLanguage(self, *args):
        code = self.language_code.get()
        if code:
            dir = self.source_dir.get()
            self.set_model_dir(code, dir)
            # invokes _set_button_status() implicitly
        else:
            self._set_button_status()

    def _onChangeSourceDir(self, *args):
        self.changingVars = True
        dir = self.source_dir.get()
        if os.path.isdir(dir):
            self.set_language_code(dir)
        self.changingVars = False
        self._set_button_status()

    # Called by base class on Back, Next, Skip and Execute
    def _save_values(self):
        if not self.invalidInputs():
            self.values['language_code'] = self.language_code.get()
            self.values['source_dir'] = self.source_dir.get()
            self.values['model_dir'] = self.model_dir.get()
            self.values['filename'] = self.filename.get()
            self.values['copy_nb'] = str(self.copy_nb.get())
            self.values['removeS5markers'] = str(self.remove_s5.get())
            # self.values['s5_only'] = str(self.s5_only.get())
            self.values['s5_to_p'] = str(self.s5_to_p.get())
            self.values['mark_every_verse'] = str(self.mark_every_verse.get())
            # self.values['punctuate'] = str(self.punctuate.get())
            self.controller.mainapp.save_values(stepname, self.values)

            projectInfo = ProjectInfo(self.source_dir.get(), self.language_code.get())
            projectInfo.setSourceDir(self.model_dir.get())
            projectInfo.save()

    # Returns a list of incomplete or incorrect inputs.
    # Used by _onExecute().
    # Is also called before values are saved to configuration files.
    def invalidInputs(self):
        objections = []
        code = self.language_code.get()
        dir = self.source_dir.get()
        model_dir = self.model_dir.get()
        namedfile = self.filename.get()

        if not code:
            objections.append("Language code is required.")
        if not dir or not model_dir:
            objections.append("Specify locations of files.")
        if dir and not os.path.isdir(dir):
            objections.append(f"{dir} is not a valid folder.")
        if model_dir and not os.path.isdir(model_dir):
            objections.append(f"Model text folder ({model_dir}) is invalid.")
        if namedfile:
            filepath = os.path.join(dir, namedfile)
            if not os.path.isfile(filepath):
                objections.append(f"{filepath} is not a valid file.")
        if model_dir == dir:
            objections.append("The two file folders can't be the same.")
        return objections

    def _onFindModelDir(self, *args):
        hints = self._list_sources()
        if hints:
            hints = "Locate the folder, for one of these source texts:\n" + hints
            self.clear_show(hints)
        self.controller.askdir(self.model_dir)
    # Returns a string properly formatted for showing the known sources texts
    # for this translation, and how frequently each was used.
    def _list_sources(self):
        workdir = self.source_dir.get()
        code = self.language_code.get()
        sourcehints = []
        if os.path.isdir(workdir) and code:
            pi = ProjectInfo(workdir, code)
            for src in pi.getSources():
                sourcehints.append(f"  {src['language_id']}_{src['resource_id']}, vrsn ~{src['version']} was used for {src['count']} book(s).")
        return "\n".join(sourcehints)

    def _onFindSrcDir(self, *args):
        self.controller.askdir(self.source_dir)
    def _onFindFile(self, *args):
        self.controller.askusfmfile(self.source_dir, self.filename)

    def _onOpenIssues(self, *args):
        self._save_values()
        path = os.path.join(self.values['source_dir'], "issues.txt")
        os.startfile(path)

    def _onUndo(self, *args):
        self._save_values()
        self.controller.revertChanges()
        self.controller.enablebutton(4, False)

    def _set_button_status(self, *args):
        if not self.changingVars:
            good_source = os.path.isdir(self.source_dir.get())
            self.controller.enablebutton(4, good_source)
            self.controller.enablebutton(2, len(self.invalidInputs()) == 0)
