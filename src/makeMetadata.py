# -*- coding: utf-8 -*-
# This script is intended to create or regenerate manifest.yaml and metadata.json files.

from configmanager import ToolsConfigManager
from manifestyaml import ManifestYaml
from projectinfo import ProjectInfo
# from pathlib import Path
import usfm_verses
import re
import io
import os
import sys
from datetime import datetime
import operator
# from manifestjson import ManifestJson

projectInfo = None
gui = None
nConverted = 0
precleanup_file = None
postcleanup_file = None

def reportError(msg):
    reportToGui(msg, '<<ScriptMessage>>')
    sys.stderr.write(msg + '\n')
    sys.stderr.flush()

# Sends a status message to the GUI.
# To be called only if the gui is set.
def reportStatus(msg):
    reportToGui(msg, '<<ScriptMessage>>')
    print(msg)

def reportToGui(msg, event):
    if gui:
        with gui.progress_lock:
            gui.progress = msg if not gui.progress else f"{gui.progress}\n{msg}"
        gui.event_generate(event, when="tail")

# Returns the modified date/time of the specified file, formatted as a string.
def get_timestamp(path):
    mtime = os.path.getmtime(path)
    dt = datetime.fromtimestamp(mtime)
    s = dt.strftime("%Y%m%d%H%M")
    return s[2:]

# Returns True if the specified path looks like a collection of chapter folders
def isBookFolder(path):
    chapterPath = os.path.join(path, '01')
    return os.path.isdir(chapterPath)

def shortname(longpath):
    source_dir = ToolsConfigManager().get('Txt2USFM', 'source_dir')
    shortname = longpath
    if shortname == source_dir:
        shortname = os.path.basename(longpath)
    elif shortname.startswith(source_dir):
        shortname = os.path.relpath(shortname, source_dir)
    return shortname

title_re = re.compile(r'\\(id|h|mt|mt1|toc1|toc2) +(.+)')

# Returnsbook id and title found in the first few lines of the specified usfm file.
def getIdAndTitle(path):
    N = 16
    id = ""
    title = ""
    titles = []
    with io.open(path, "tr", encoding='utf-8-sig') as file:
        for i in range(N):
            try:
                line = next(file).strip()
                if titleline := title_re.match(line):
                    if titleline.group(1) == 'id':
                        id = titleline.group(2)[0:3]
                    elif titleline.group(1) in {'mt','mt1'}:
                        title = titleline.group(2)
                    elif not title:
                        titles.append(titleline.group(2))
                    elif title and id:
                        break
            except StopIteration:
                break

    if not title and len(titles) > 0:
        titles.sort(reverse=True, key=operator.itemgetter('count'))
        title = titles[0]
    return id, title

# Adds book to metadata if it can determine the book ID and title.
def addBook(usfmpath):
    global projectInfo
    assert projectInfo
    bookId = ""
    bookTitle = ""
    bookId, bookTitle = getIdAndTitle(usfmpath)
    if bookId and bookTitle:
        projectInfo.addProject(bookTitle, bookId, usfmpath)
    else:
        if not bookId:
            reportError("Unable to determine book ID in " + shortname(usfmpath))
        if not bookTitle:
            reportError("Unable to determine book title in " + shortname(usfmpath))

# Converts the book or books contained in the specified folder
def addBooks(dir):
    for entry in os.listdir(dir):
        if entry.endswith(".usfm"):
            path = os.path.join(dir, entry)
            if os.path.isfile(path):
                addBook(path)

def main(app = None):
    global gui
    gui = app

    config = ToolsConfigManager()
    work_dir = config.get('MakeMetadata', 'work_dir')
    language_code = config.get('MakeMetadata', 'language_code')
    global projectInfo
    projectInfo = ProjectInfo(work_dir, language_code)
    projectInfo.useManifest(docreate=True)
    projectInfo.setGenerator("UsfmWizard", config.get('UsfmWizard', 'version'))
    projectInfo.setLanguage(config.get('MakeMetadata', 'language_name_en'), 'en', config.get('MakeMetadata', 'direction'))
    projectInfo.setLanguage(config.get('MakeMetadata', 'localized_name'), language_code, config.get('MakeMetadata', 'direction'))
    addBooks(work_dir)
    projectInfo.addLicense(config.get('MakeMetadata', 'license_file'), config.get('MakeMetadata', 'license_type'))
    projectInfo.setIdentification(config.get('MakeMetadata', 'repo_owner'), config.get('MakeMetadata', 'repo_name'))

    is_valid, msg = projectInfo.save()
    if not is_valid:
        reportError(f"Error saving {msg}")
    else:
        reportStatus("\nDone.")
    if gui:
        gui.event_generate('<<ScriptEnd>>', when="tail")

if __name__ == "__main__":
    main()
