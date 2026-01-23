# -*- coding: utf-8 -*-
# This module standardizes the names of USFM files to our preferred names.
# Intended to support Paratext and other file naming conventions.
# Paratext files are named like 41MATen_ulb.SFM.
# Our files are named like 41-MAT.usfm.
# This module may perform other conversions, such as:
#   change the line endings to LF.
#   ensure UTF-8 character encoding.
# Set these config values in the tools config file before running this script:
#   paratext_dir
#   target_dir
#   filename - leave blank to rename all files
from configmanager import ToolsConfigManager
from projectinfo import ProjectInfo
import io
import os
from pathlib import Path
import re
import sys
import usfm_verses

gui = None
projectinfo = None

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

format1_re = re.compile(r'0?[0-9][0-9]-?([123AC-EG-JL-PR-TZ][A-Z][A-Z])')

# Returns the apparent book ID from the specified file name.
def bookidfromFilename(fname):
    bookid = ""
    found = format1_re.match(fname.upper())
    if found:
        bookid = found.group(1)
    return bookid

idcode_re = re.compile(r'\\id +([\w][\w][\w])')
mtcode_re = re.compile(r'\\(mt|mt1|h|toc1) +(.*)')
# Retrieve book Id and title from the file.
def get_bookId(path:Path):
    # bookId = bookidfromFilename(path.name)
    # if not bookId:
    #     idcode_re = re.compile(r'\\id +([\w][\w][\w])')
    #     with io.open(path, "tr", encoding="utf-8-sig") as input:
    #         line1 = input.readline()
    #     if idcode := idcode_re.match(line1):
    #         bookId = idcode.group(1)
    #     else:
    #         reportError("USFM file does not start with standard \\id marker.")
    # return bookId
    bookId = bookTitle = ""
    with io.open(path, "tr", encoding="utf-8-sig") as input:
        count = 0
        for line in input:
            if idcode := idcode_re.match(line):
                bookId = idcode.group(1)
            if mtcode := mtcode_re.match(line):
                count += 1
                bookTitle = mtcode.group(2)
                if mtcode.group(1) in {'mt', 'mt1'} or count > 10:
                    break
    return bookId, bookTitle

# Appends information about the current book to the global projects list.
# Ultimately adds to manifest.yaml.
def appendToProjects(bookId, bookTitle):
    global projectInfo
    category = 'bible-nt'
    if usfm_verses.verseCounts[bookId]['sort'] < 40:
        category = 'bible-ot'
    elif usfm_verses.verseCounts[bookId]['sort'] > 66:
        category = "periph"
    project = { "title": bookTitle, "identifier": bookId.lower(), "sort": usfm_verses.verseCounts[bookId]["sort"], \
                "path": "./" + makeUsfmFilename(bookId), "categories": [ category ],
                 'versification': 'ufw' }
    projectInfo.addProject(project)

def copyfile(path, newpath):
    content = None
    with io.open(path, "tr", encoding="utf-8-sig") as input:
        content = input.read()
    if content:
        with io.open(newpath, "tw", encoding='utf-8', newline='\n') as output:
            output.write(content)

def convertFile(path:Path, target_dir):
    count = 0
    bookid, booktitle = get_bookId(path)
    if bookid:
        appendToProjects(bookid, booktitle)
        fname = makeUsfmFilename(bookid)
        if fname:
            newpath = os.path.join(target_dir, fname)
            if os.path.exists(newpath):
                bakpath = newpath.replace(".usfm", ".usfm-orig")
                os.replace(newpath, bakpath)
            copyfile(str(path), newpath)
            count = 1
    else:
        reportError(f"Can't identify the book in: {path.name}")
    return count

def convertFolder(ptx_dir, work_dir):
    count = 0
    ptxpath = Path(ptx_dir)
    for path in ptxpath.glob('*.usfm'):
        count += convertFile(path, work_dir)
    for path in ptxpath.glob('*.SFM'):
        count += convertFile(path, work_dir)
    if count == 0:
        reportError(f"There are no .sfm or .usfm files in {ptx_dir}.\n")
    return count

naming_re = re.compile(r'PostPart=".*" +BookNameForm=".*?"')

# Brings the Settings.xml file over to the target workiing folder,
# with corrections to the file Naming part.
def convertSettingsFile(source_dir, work_dir):
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
        # Copy to working folder
        path = os.path.join(work_dir, "Settings.xml")
        with io.open(path, "tw", encoding='utf-8') as output:
            output.write(s)
    else:
        reportError(f"Settings.xml file not found")

# Temporary function, until all references to "target_dir" are removed.
def getWorkDir():
    config = ToolsConfigManager()
    workdir = config.get('Paratext2Usfm', 'work_dir')
    if not workdir:
        workdir = config.get('Paratext2Usfm', 'target_dir')    # the old name
    return workdir

def main(app = None):
    global gui
    gui = app
    config = ToolsConfigManager()
    ptx_dir = config.get('Paratext2Usfm', 'paratext_dir')
    usfm_dir = getWorkDir()
    filename = config.get('Paratext2Usfm', 'filename')
    if not os.path.isdir(ptx_dir):
        reportError(f"Invalid paratext folder: {ptx_dir}")
    Path(usfm_dir).mkdir(exist_ok=True)
    global projectInfo
    projectInfo = ProjectInfo(usfm_dir, config.get('Paratext2Usfm', 'language_code'))
    projectInfo.useManifest(docreate=True)

    if filename:
        count = convertFile(Path(ptx_dir, filename), usfm_dir)
    else:
        count = convertFolder(ptx_dir, usfm_dir)
    if count > 0 and 'ParatextProjects' in ptx_dir:
        convertSettingsFile(ptx_dir, usfm_dir)
    projectInfo.save()
    reportStatus(f"Converted {count} file(s).")
    if gui:
        gui.event_generate('<<ScriptEnd>>', when="tail")

if __name__ == "__main__":
    main()
