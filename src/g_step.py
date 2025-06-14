# -*- coding: utf-8 -*-
# Base class for graphical user interface classes for USFM steps.

from tkinter import ttk
from tkinter import filedialog
from tkinter import StringVar, DISABLED, NORMAL, Text
from abc import ABC
import os

class Step(ABC):
    def __init__(self, mainframe, mainapp, stepname, title):
        self.main_frame = mainframe
        self.mainapp = mainapp
        self.steptitle = title  # Descriptive, displayable title for the step
        self.buttons = mainapp.buttonsframe
        self.frame = None

    # Ensures that self.frame is non-null.
    def _frame(self):
        if not self.frame:  # should not occur
            self.frame = Step_Frame(self.main_frame, self.mainapp)
        return self.frame

    def name(self) -> str:
        return ""

    # Called by UsfmWizard.activate_step()
    def show(self, values):
        self.values = values
        self._frame().show_values(values)
        self._frame().tkraise()

    def title(self):
        return self.steptitle

    def onBack(self):
        self.mainapp.step_back()
    def onSkip(self):
        self.mainapp.step_next()
    # Advance to next step, defaulting the values of the named parameters, if any.
    def onNext(self, *parms):
        copyparms = {parm: self.values[parm] for parm in parms} if parms else {}
        self.mainapp.step_next(copyparms)

    # Default implementation, only for Steps that don't execute,. i.e. SelectProcess
    def onExecute(self):
        pass
    def showbutton(self, psn, text, cmd, tip=""):
        self.buttons.show(psn, text, cmd, tip)
    def hidebutton(self, *psns):
        for psn in psns:
            self.buttons.hide(psn)
    def enablebutton(self, psn, enable=True):
        if enable:
            self.buttons.enable(psn)
        else:
            self.buttons.disable(psn)
    # def buttonenabled(self, psn):
    #     return self.buttons.enabled(psn)
    def bindButtonEvent(self, psn, event, cmd):
        self.buttons.bind(psn, event, cmd)

    # Called by the main app.
    # Displays the specified string in the message area.
    def onScriptMessage(self, progress):
        self._frame().show_progress(progress)

    # Called by the main app.
    def onScriptEnd(self, status: str):
        if status:
            self._frame().show_progress(status)
        self._frame().onScriptEnd()

    # Prompts the user for a folder, using the parent of the specified default folder as the starting point.
    # Sets dirpath to the selected folder, or leaves it unchanged if the user cancels.
    def askdir(self, dirpath: StringVar, msg="Select Folder"):
        initdir = dirpath.get()
        if os.path.isdir(initdir):
            initdir = os.path.dirname(initdir)
        path = filedialog.askdirectory(initialdir=initdir, mustexist=False, title=msg)
        if path:
            dirpath.set(path)

    # Prompts the user to locate a usfm file in the specified source_dir.
    # Sets filename to the selected file, or leaves it unchanged if the user cancels.
    def askusfmfile(self, source_dir: StringVar, filename: StringVar):
        path = filedialog.askopenfilename(initialdir=source_dir.get(), title = "Select usfm file",
                                           filetypes=[('Usfm file', '*.usfm')])
        if path:
            filename.set(os.path.basename(path))

class Step_Frame(ttk.Frame, ABC):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.values = {}

        # Set up message area
        self.message_area = Text(self, height=10, width=30, wrap="word")
        self.message_area['borderwidth'] = 2
        self.message_area['relief'] = 'sunken'
        self.message_area['background'] = 'grey97'
        self.message_area.grid(row=88, column=1, columnspan=5, sticky='nsew', pady=6)
        self.rowconfigure(88, minsize=170, weight=1)  # let the message expand vertically
        ys = ttk.Scrollbar(self, orient = 'vertical', command = self.message_area.yview)
        ys.grid(column = 6, row = 88, sticky = 'ns')
        self.message_area['yscrollcommand'] = ys.set

    def show_values(self, values):
        raise NotImplementedError("show_values() not implemented")
    def _save_values(self):
        raise NotImplementedError("_save_values() not implemented")

    def show_progress(self, status):
        self.message_area.insert('end', status + '\n')
        self.message_area.see('end')

    # Clears all text in the message box and enable insertions.
    def clear_messages(self, *args):
        self.message_area['state'] = NORMAL   # enables insertions to message area
        self.message_area.delete('1.0', 'end')

    # Clears the message area and shows the specified message
    # Disables new insertions.
    def clear_show(self, message):
        self.clear_messages()
        self.message_area.insert('end', message)
        self.message_area['state'] = DISABLED

    # This function does thorough input validation prior to step execution, or any time.
    # It should be overridden by subclasses
    # The user may need this help in identifying certain incorrect input(s).
    def invalidInputs(self, *args):
        objections = []
        return objections
    # Displays any reasons why the current step cannot be executed.
    def _onCheckInputs(self, *args):
        objections = self.invalidInputs()
        if len(objections) > 0:
            self.controller.enablebutton(2, False)
            for objection in objections:
                self.message_area.insert('end', f"{objection}\n")

    def _onBack(self, *args):
        self._save_values()
        self.controller.onBack()
    def _onSkip(self, *args):
        self._save_values()
        self.controller.onSkip()
    def _onNext(self, *args):
        self._save_values()
        self.controller.onNext()
    def _onExecute(self, *args):
        objections = self.invalidInputs()
        if len(objections) == 0:
            self._save_values()
            self.controller.enablebutton(5, False)
            self.controller.onExecute(self.values)
        else:
            self.controller.enablebutton(2, False)
            for objection in objections:
                self.message_area.insert('end', f"{objection}\n")

    def onScriptEnd(self):
        self.controller.enablebutton(5, True)
