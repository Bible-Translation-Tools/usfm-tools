# -*- coding: utf-8 -*-
# Wizard style, GUI interface for USFM file processing
#

import configmanager
import tkinter
from tkinter import *
from tkinter import ttk
from tkinter import font
from tkinter import messagebox
from idlelib.tooltip import Hovertip
import os
import re
import sys
import time
import threading
import g_selectProcess
import g_txt2USFM
import g_verifyUSFM
import g_UsfmCleanup
import g_MarkParagraphs
import g_paratext2usfm
import g_plaintext2usfm
import g_verifyManifest
import g_usfm2usx
import g_usx2usfm
import g_word2text
from txt2USFM import main
from verifyUSFM import main
from inventory_chapter_labels import main
from usfm_cleanup import main
from mark_paragraphs import main
from paratext2usfm import main
from plaintext2usfm import main
from revertChanges import main
from usfm2usx import main
from usx2usfm import main
from verifyManifest import main
from word2text import main

app_version = "1.3.1"

class UsfmWizard(tkinter.Tk):
    def __init__(self):
        super().__init__()

        self.title('USFM Wizard')
        self.config = configmanager.ToolsConfigManager()
        mainframe = Frame(self, height=550, width=840)
        mainframe.grid(column=0, row=0, sticky="nsew")
        
        self.titleframe = Title_Frame(parent=mainframe)
        self.titleframe.grid(row=0, column=0, sticky="nsew")
        self.buttonsframe = Buttons_Frame(parent=mainframe)
        self.buttonsframe.grid(row=100, column=0, sticky="nsew")
        self._build_steps(mainframe)

        self.process = 'SelectProcess'
        self.stepstack = [self.steps['SelectProcess']]
        self.activate_step(self.stepstack[-1])
        self.bind('<<ScriptMessage>>', self.onScriptMessage)
        self.bind('<<ScriptProgress>>', self.onScriptProgress)
        self.bind('<<ScriptEnd>>', self.onScriptEnd)
        self.progress_lock = threading.Lock()
        self.bind('<Enter>', self.normalize_window)
        self.n = 0

    def _build_steps(self, mainframe):
        self.steps = {}
        for S in (g_selectProcess, g_txt2USFM, g_verifyUSFM, g_UsfmCleanup, g_MarkParagraphs,
                  g_verifyManifest, g_plaintext2usfm, g_usfm2usx, g_word2text, g_paratext2usfm,
                  g_usx2usfm):
            stepclass = getattr(sys.modules[S.__name__], S.stepname)
            step = stepclass(mainframe, mainapp=self)   # create an instance of the class
            self.steps[step.name()] = step
        for child in self.winfo_children():
            child.grid_configure(padx=(25,15), pady=5)

    # This function turns off the -topmost attribute so that other windows can overlay this one.
    def normalize_window(self, *args):
        self.attributes("-topmost", False)
        self.unbind("<Enter>")

    def execute_script(self, module, count):
        if count > 0:
            self.titleframe.start_progress(count)
        self.titleframe.tkraise()
        self.progress = ""
        self.current_script_module = sys.modules[module]
        target = getattr(self.current_script_module, "main")
        self.thread = threading.Thread(target=target, args=(self, ))
        self.thread.start()
        self.titleframe.increment_progress(0)

    def onScriptMessage(self, event):
        with self.progress_lock:
            copystr = self.progress
            self.progress = ""
        if copystr:
            self.stepstack[-1].onScriptMessage(copystr)

    def onScriptProgress(self, event):
        self.onScriptMessage(event)
        self.titleframe.increment_progress()

    def onScriptEnd(self, event):
        time.sleep(0.2)     # show completeness this much longer before removing progress bar
        self.thread.join()
        with self.progress_lock:
            copystr = self.progress
            self.progress = ""
        self.stepstack[-1].onScriptEnd(copystr)
        self.titleframe.stop_progress()

    def set_process(self, selection):
        self.process = selection

    # Activates the previous step
    def step_back(self):
        self.stepstack.pop()
        self.activate_step( self.stepstack[-1] )

    # Returns the name of the next step in the current process
    def nextstepname(self):
        gotostep = None
        match self.stepstack[-1].name():
            case 'MarkParagraphs':
                gotostep = 'VerifyManifest'
            case 'SelectProcess':
                if self.process == 'Usfm2Usx':
                    gotostep = 'VerifyUSFM'
                else:
                    gotostep = self.process
            case 'Txt2USFM':
                gotostep = 'VerifyUSFM'
            case 'Word2text':
                gotostep = 'Plaintext2Usfm'
            case 'Plaintext2Usfm':
                gotostep = 'VerifyUSFM'
            case 'UsfmCleanup':
                gotostep = 'MarkParagraphs'
            case 'Usx2Usfm':
                gotostep = 'VerifyUSFM'
            case 'VerifyUSFM':
                if self.process == 'Usfm2Usx':
                    gotostep = 'Usfm2Usx'
                elif self.process == 'Usx2Usfm':
                    gotostep = 'MarkParagraphs'
                else:
                    gotostep = 'UsfmCleanup'
        return gotostep

    # Activates the next step, based the current process and what step we just finished.
    def step_next(self, copyparms=None):
        nextstep = self.steps[self.nextstepname()]
        self.stepstack.append(nextstep)
        self.activate_step(nextstep, copyparms)

    def activate_step(self, step, copyparms=None):
        self.titleframe.step_label['text'] = step.title()
        section = self.config.get_section(step.name())
        if copyparms:
            for parm in copyparms:
                section[parm] = copyparms[parm]
            self.config.write_section(step.name(), section)
        self.stepstack[-1].show(section)

    # Called by one of the GUI modules.
    # Saves the specified values in the config file.
    def save_values(self, stepname, values):
        self.config.write_section(stepname, values)

# The Title_Frame implements a Label for step titles, and a Progressbar for step executions.
# These go on row 1 of the main UsfmWizard Frame.
class Title_Frame(Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.step_label = ttk.Label(self, font='TKHeadingFont')
        self.step_label.grid(row=1, column=1, padx=(0,25))
        self.progressbar = ttk.Progressbar(self, length=235, orient='horizontal', mode='determinate')

    def start_progress(self, n):
        self.progressbar['maximum'] = n
        self.progressbar.grid(row=1, column=2, sticky="ew")
        # self.update()   # this may be unnecessary after I get the threads going
    def increment_progress(self, delta=1):
        self.progressbar['value'] += delta
    def stop_progress(self):
        self.progressbar.stop()
        self.progressbar.grid_forget()

# Buttons_Frame reserves a row of five buttons on the UsfmWizard main Frame.
# The buttons are initially hidden.
# The various Step classes populate the buttons as needed.
class Buttons_Frame(Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.button = [None] * 6
        self.rowconfigure(1, minsize=30)
        for i in (2,3,4):
            self.columnconfigure(i, minsize=117)
        for i in (1,5):
            self.columnconfigure(i, minsize=82)
        label1 = ttk.Label(self, text="     ")
        label1.grid(row=1, column=1, padx=(0,10))
        label2 = ttk.Label(self, text="     ")
        label2.grid(row=1, column=2, padx=50)
        label3 = ttk.Label(self, text="     ")
        label3.grid(row=1, column=3, padx=50)
        label4 = ttk.Label(self, text="     ")
        label4.grid(row=1, column=4, padx=50)
        label5 = ttk.Label(self, text="     ")
        label5.grid(row=1, column=5, padx=(10,0), ipady=6)
        self.show(1, text=">>>", tip="Next step")
        self.show(2, text=">>>", tip="Next step")
        self.show(3, text=">>>", tip="Next step")
        self.show(4, text=">>>", tip="Next step")
        self.show(5, text=">>>", tip="Next step")

    def show(self, psn, text="", tip=None, cmd=None):
        if psn == 5:
            stky = 'nse'
            padx=(5,0)
            ipady = 7
        elif psn == 1:
            stky = 'nsw'
            padx=(0,5)
            ipady = 7
        else:
            stky = 'nsew'
            padx=(5,5)
            ipady = 0 if '\n' in text else 6
        if 1 <= psn <= 5:
            self.hide(psn)
            self.button[psn] = ttk.Button(self, text=text, command=cmd)
            self.button[psn].grid(row=1, column=psn, sticky=stky, padx=padx, pady=10, ipady=ipady)
            if tip:
                buttonTip = Hovertip(self.button[psn], hover_delay=500, text=tip)

    def hide(self, psn): 
        try:
            self.button[psn].grid_remove()
        except:
            pass
    def enable(self, psn):
        try:
            self.button[psn].state(['!disabled'])
        except:
            pass
    def disable(self, psn):
        try:
            self.button[psn].state(['disabled'])
        except:
            pass

def create_menu(wizard):
    wizard.option_add('*tearOff', FALSE)  # essential to have a normal menu
    menubar = Menu(wizard)
    menu_file = Menu(menubar)
    menubar.add_cascade(menu=menu_file, label='File')
    menu_file.add_command(label='Exit', command=exit_wizard)
    menu_help = Menu(menubar)
    menubar.add_cascade(menu=menu_help, label='Help')
    menu_help.add_command(label='Procedures', command=read_the_docs)
    menu_help.add_command(label='About', command=about)
    menu_help.add_command(label='Version history', command=version_history)
    wizard['menu'] = menubar

def read_the_docs(*args):
    os.startfile(r'https://wycliffeassociatesinc-my.sharepoint.com/:w:/g/personal/larry_versaw_wycliffeassociates_org/EVOk8ijgv-hOkdNo2T--mmsBhlNzHiwDd2v3JQ44XN_Ciw?e=y6ww9j')
def version_history(*args):
    os.startfile(r'https://wycliffeassociatesinc-my.sharepoint.com/:t:/g/personal/larry_versaw_wycliffeassociates_org/EfAjyDKzT85Dg27NcWhk-jABmk6a2K6jSlwIjc_ddfSWaA?e=sry9f0')
def about(*args):
    configpath = wizard.config.config_path()
    messagebox.showinfo(title='About USFM Wizard', message=f"Version {app_version}",
                        detail=f"Config file: {configpath}")
def exit_wizard(*args):
    wizard.destroy()
    # It would be nice if I killed any threads that are still running here.

if __name__ == "__main__":
    wizard = UsfmWizard()
    create_menu(wizard)
    wizard.attributes("-topmost", True)    # works around issue where wizard comes up behind cmd window
    wizard.mainloop()
