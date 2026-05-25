# -*- coding: utf-8 -*-

# Script for verifying a Scripture Burrito metadata.json.

nIssues = 0
resouceDir = ""

from configmanager import ToolsConfigManager
from datetime import datetime
from datetime import date
import sys
# import os
# import io
# import re

# Writes error message to stderr.
def reportError(msg):
    reportToGui(msg)
    stream(msg, "Error", sys.stderr)
    sys.stderr.flush()
    global nIssues
    nIssues += 1

# Writes warnings message to stderr.
def reportWarning(msg):
    reportError("Potential error. Please check: " + msg)

def reportStatus(msg):
    reportToGui(msg)
    stream(msg, "Status", sys.stdout)

def reportToGui(msg):
    if gui:
        with gui.progress_lock:
            gui.progress = msg if not gui.progress else f"{gui.progress}\n{msg}"
        gui.event_generate('<<ScriptMessage>>', when="tail")

# This little function streams the specified message and handles UnicodeEncodeError
# exceptions, which are common in Indian language texts. 2/5/24.
def stream(msg, msgtype, stream):
    try:
        stream.write(msg + "\n")
    except UnicodeEncodeError as e:
        stream.write(f"{msgtype} message not shown, contains Unicode.\n")

# Verifies the syntactical correctness of the metadata.json file for now.
# Returns the number of issues found.
def verifyBurrito(app = None):
    global gui
    gui = app
    global nIssues
    nIssues = 0
    global resouceDir
    resouceDir = ToolsConfigManager().get('VerifyManifest', 'work_dir')

    from scripture_burrito import Burrito
    burrito = Burrito(resouceDir)
    is_valid, msg = burrito.load()
    if not is_valid:
        reportError(f"Invalid burrito data: {msg}")
    return nIssues

def main(app = None):
    verifyBurrito(app)
    if nIssues == 0:
        reportStatus("Done, no issues found.")
    else:
        reportStatus("\nFinished checking, found " + str(nIssues) + " issue(s).")
    sys.stdout.flush()
    if gui:
        gui.event_generate('<<ScriptEnd>>', when="tail")

if __name__ == "__main__":
    main()
