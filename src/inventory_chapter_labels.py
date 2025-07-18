# -*- coding: utf-8 -*-
# inventory() counts occurrences of each chapter label in a folder of .usfm files.

import sys
import os
import io
import re

gui = None
labels: dict = {}   # Chapter labels and counts

# Writes the error messages to stderr and the gui.
def reportError(msg):
    reportToGui('<<ScriptMessage>>', msg)
    write(msg, sys.stderr)

# Sends a status message to the GUI, and to stdout.
def reportStatus(msg):
    reportToGui('<<ScriptMessage>>', msg)
    write(msg, sys.stdout)

def reportToGui(event, msg):
    if gui:
        with gui.progress_lock:
            gui.progress = msg if not gui.progress else f"{gui.progress}\n{msg}"
        gui.event_generate(event, when="tail")

# Streams the specified message and handles UnicodeEncodeError exceptions.
def write(msg, stream):
    try:
        stream.write(msg + "\n")
    except UnicodeEncodeError as e:
        stream.write("(UnicodeEncodeError...)\n")

def dumpInventory(folder):
    if len(labels) > 1:
        msg = f"These chapter labels are found in {folder}:"
    elif len(labels) == 1:
        msg = f"Only one chapter label is found in {folder}:"
    else:
        msg = f"No chapter labels are found in {folder}:\n"
    reportStatus(msg)
    for label in sorted(labels.items(), key=lambda item: item[1], reverse=True):
        reportStatus(f"{label[0]}\t{label[1]:4}")

# Inventories chapter labels in the specified folder.
# Non-recursive.
def inventoryFolder(folder):
    for fname in os.listdir(folder):
        path = os.path.join(folder, fname)
        if fname.lower().endswith('sfm'):
            processFile(path)

cl_re = re.compile(r'\\cl +[\d]*([^\d]+)')

# Records the number of each chapter label in the specified file.
def processFile(path):
    with io.open(path, "r", encoding="utf-8-sig") as input:
        lines = input.readlines()
    for line in lines:
        if cl := cl_re.match(line):
            label = cl.group(1).strip()
            if label in labels:
                labels[label] += 1
            else:
                labels[label] = 1

# Processes the caller's directory and its files one at a time.
# caller must be a valid section in the ToolsConfigManager.
def inventory(app, caller):
    global gui
    gui = app
    from configmanager import ToolsConfigManager
    config = ToolsConfigManager()
    labels.clear()
    source_dir = config.get(caller, 'source_dir')
    if os.path.isdir(source_dir):
        inventoryFolder(source_dir)
    else:
        reportError(f"Invalid folder: {caller} source_dir = {source_dir}")
    dumpInventory(source_dir)
    sys.stdout.flush()
    if gui:
        gui.event_generate('<<ScriptEnd>>', when="tail")

def main(gui = None):
    from configmanager import ToolsConfigManager
    config = ToolsConfigManager()
    caller = config.get('UsfmWizard', 'step')
    if caller:
        inventory(gui, caller)
