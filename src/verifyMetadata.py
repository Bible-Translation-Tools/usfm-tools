# -*- coding: utf-8 -*-

# Checks manifest.yaml by calling verifyManifest().
# Checks burrito file metadata.json by calling verifyBurrito().

import sys
from verifyManifest import verifyManifest
from verifyBurrito import verifyBurrito

def reportStatus(msg, gui):
    reportToGui(msg, gui)
    stream(msg, "Status", sys.stdout)

def reportToGui(msg, gui):
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

def main(gui = None):
    nIssues = verifyManifest(gui)
    nIssues += verifyBurrito(gui)
    if nIssues == 0:
        reportStatus("Done, no issues found.", gui)
    else:
        reportStatus("\nFinished checking, found " + str(nIssues) + " issue(s).", gui)
    sys.stdout.flush()
    if gui:
        gui.event_generate('<<ScriptEnd>>', when="tail")

if __name__ == "__main__":
    main()
