# -*- coding: utf-8 -*-
# Paratext files are named like 41MATen_ulb.SFM.
# Our files are named like 41-MAT.usfm.
# This module renames Paratext files to our standard naming convention,
# and changes the line endings to LF.
# Set these config values in config.ini before running this script.
#   paratext_dir
#   target_dir
#   filename - leave blank to rename all files

import configmanager
import io
import os
from pathlib import Path
import re
import sys
import usfm_verses

gui = None
config = None

# Writes message to stderr and to issues.txt.
# If it is not a real issue, writes message to report file.
def reportError(msg):
    reportStatus(msg)     # message to gui
    try:
        sys.stderr.write(msg + "\n")
    except UnicodeEncodeError as e:
        sys.stderr.write("(Unicode...)\n")

def reportStatus(msg):
    global gui
    if gui:
        with gui.progress_lock:
            gui.progress = msg if not gui.progress else f"{gui.progress}\n{msg}"
        gui.event_generate('<<ScriptMessage>>', when="tail")
    print(msg)

# Generates our standard name for usfm file
def makeUsfmFilename(bookId):
    fname = ""
    try:
        num = usfm_verses.verseCounts[bookId]['usfm_number']
        fname = num + '-' + bookId + '.usfm'
    except KeyError as e:
        reportError(f"Invalid book ID: {bookId}")
    return fname

format1_re = re.compile(r'0?[0-6][0-9]-?([123AC-EG-JL-PR-TZ][A-Z][A-Z])')

# Returns the apparent book ID from the specified file name.
def bookidfromFilename(fname):
    bookid = ""
    found = format1_re.match(fname.upper())
    if found:
        bookid = found.group(1)
    return bookid

def copyfile(path, newpath):
    content = None
    with io.open(path, "tr", encoding="utf-8-sig") as input:
        content = input.read()
    if content:
        with io.open(newpath, "tw", encoding='utf-8', newline='\n') as output:
            output.write(content)

def convertFile(path:Path, target_dir):
    count = 0
    bookid = bookidfromFilename(path.name)
    fname = makeUsfmFilename(bookid)
    if fname:
        newpath = os.path.join(target_dir, fname)
        if os.path.exists(newpath):
            bakpath = newpath.replace(".usfm", ".usfm-orig")
            os.replace(newpath, bakpath)
        copyfile(str(path), newpath)
        count = 1
    else:
        reportError(f"Could not get book id from file name: {path.name}")
    return count

def convert(source_dir, target_dir):
    count = 0
    sourcepath = Path(source_dir)
    for path in sourcepath.glob('*.SFM'):
        count += convertFile(path, target_dir)
    if count == 0:
        reportError(f"There are no .SFM files in {source_dir}.\n")
    return count

naming_re = re.compile(r'PostPart=".*" +BookNameForm=".*?"')

# Brings the Settings.xml file over to the target folder,
# with corrections to the file Naming part.
def convertSettingsFile(source_dir, target_dir):
    path = os.path.join(source_dir, "Settings.xml")
    if os.path.exists(path):
        with io.open(path, "r", encoding="utf-8-sig") as input:
            s = input.read()
            naming = naming_re.search(s)
            if naming:
                newparts = 'PostPart=".usfm" BookNameForm="41-MAT"'
                s = s[0:naming.start()] + newparts + s[naming.end()]
            else:
                reportError("Could not find PostPart & BookNameForm elements in Settings.xml. Beware if using AQuA.")
        # Copy to target folder
        path = os.path.join(target_dir, "Settings.xml")
        with io.open(path, "tw", encoding='utf-8') as output:
            output.write(s)
    else:
        reportError(f"Settings.xml file not found")

def main(app = None):
    global gui
    gui = app
    global config
    config = configmanager.ToolsConfigManager().get_section('Paratext2Usfm')
    if config:
        ptx_dir = config['paratext_dir']
        usfm_dir = config['target_dir']
        filename = config['filename']

        if not os.path.isdir(ptx_dir):
            reportError(f"Invalid paratext folder: {ptx_dir}")
        Path(usfm_dir).mkdir(exist_ok=True)
        if filename:
            count = convertFile(Path(ptx_dir, filename), usfm_dir)
        else:
            count = convert(ptx_dir, usfm_dir)
        if count > 0:
            convertSettingsFile(ptx_dir, usfm_dir)
        reportStatus(f"Coverted {count} .SFM file(s).")
    if gui:
        gui.event_generate('<<ScriptEnd>>', when="tail")

if __name__ == "__main__":
    main()