# -*- coding: utf-8 -*-

# Checks manifest.yaml by calling verifyManifest().
# Checks burrito file metadata.json by calling verifyBurrito().

import sys
from verifyManifest import verifyManifest
from verifyBurrito import verifyBurrito

gui = None

def reportStatus(msg):
    reportToGui('<<ScriptMessage>>', msg)
    stream(msg, "Status", sys.stdout)

# Sends a progress report to the GUI, and to stdout.
def reportProgress(msg):
    reportToGui('<<ScriptProgress>>', msg)
    print(msg)

def reportToGui(event, msg):
    if gui:
        with gui.progress_lock:
            gui.progress = msg if not gui.progress else f"{gui.progress}\n{msg}"
        gui.event_generate(event, when="tail")

# This little function streams the specified message and handles UnicodeEncodeError
# exceptions, which are common in Indian language texts. 2/5/24.
def stream(msg, msgtype, stream):
    try:
        stream.write(msg + "\n")
    except UnicodeEncodeError as e:
        stream.write(f"{msgtype} message not shown, contains Unicode.\n")

def main(app = None):
    global gui
    gui = app
    nIssues = verifyManifest(gui)
    reportProgress(f"Finished checking manifest.yaml, found {nIssues} issue(s).")
    nBurritoIssues = verifyBurrito(gui)
    if nBurritoIssues == 0:
        reportStatus("\nNo issues found in metadata.json.")
    nIssues += nBurritoIssues
    reportProgress(f"\nDone, found {nIssues} issue(s).")
    if gui:
        gui.event_generate('<<ScriptEnd>>', when="tail")

if __name__ == "__main__":
    main()
