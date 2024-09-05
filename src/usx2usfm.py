# -*- coding: utf-8 -*-
# This script parses one or more USX files
# to generate a set of USFM text files.
# Uses xml.sax.

# Global variables
gui = None
config = None
projects = []
bookId = ""
issuesFile = None

import xml.sax
import configmanager
import operator
import io
import os
from pathlib import Path
import sys
import usfm_verses
import usfmWriter

def shortname(longpath):
    dir = config['usx_dir']
    shortname = str(longpath)
    if shortname.startswith(dir):
        shortname = os.path.relpath(shortname, dir)
    return shortname

# Writes message to gui, stderr, and issues.txt.
def reportError(msg):
    reportStatus(msg)     # message to gui
    sys.stderr.write(msg + "\n")
    openIssuesFile().write(msg + "\n")

# Sends a progress report to the GUI, and to stdout.
def reportProgress(msg):
    global gui
    if gui:
        with gui.progress_lock:
            gui.progress = msg if not gui.progress else f"{gui.progress}\n{msg}"
        gui.event_generate('<<ScriptProgress>>', when="tail")
    print(msg)

# Sends a status message to the GUI, and to stdout.
def reportStatus(msg):
    global gui
    if gui:
        with gui.progress_lock:
            gui.progress = msg if not gui.progress else f"{gui.progress}\n{msg}"
        gui.event_generate('<<ScriptMessage>>', when="tail")
    print(msg)
    openIssuesFile().write(msg + "\n")

# If issues.txt file is not already open, opens it for writing.
# First renames existing issues.txt file to issues-oldest.txt unless
# issues-oldest.txt already exists.
# Returns file pointer.
def openIssuesFile():
    global issuesFile
    if not issuesFile:
        workdir = config['usx_dir']
        path = os.path.join(workdir, "issues.txt")
        if os.path.exists(path):
            bakpath = os.path.join(workdir, "issues-oldest.txt")
            if not os.path.exists(bakpath):
                os.rename(path, bakpath)
        issuesFile = io.open(path, "tw", encoding='utf-8', newline='\n')
        issuesFile.write(f"Status and issues reported by usx2usfm\n-------------------\n")
    return issuesFile

# Appends information about the current book to the global projects list.
def appendToProjects(bookId, bookTitle):
    global projects
    sort = usfm_verses.verseCounts[bookId]['sort']
    if sort <= 66:
        testament = 'ot' if sort < 40 else 'nt'
        project = { "title": bookTitle, "id": bookId.lower(), "sort": usfm_verses.verseCounts[bookId]["sort"], \
                "path": "./" + makeUsfmName(bookId), "category": "[ 'bible-" + testament + "' ]" }
        projects.append(project)

def dumpProjects(target_dir):
    global projects
    projects.sort(key=operator.itemgetter('sort'))

    path = os.path.join(target_dir, "projects.yaml")
    manifest = io.open(path, "tw", buffering=1, encoding='utf-8', newline='\n')
    manifest.write("projects:\n")
    for p in projects:
        manifest.write("  -\n")
        if not "'" in p['title']:
            manifest.write("    title: '" + p['title'] + "'\n")
        else:
            manifest.write('    title: "' + p['title'] + '"\n')
        manifest.write("    versification: ufw\n")
        manifest.write("    identifier: '" + p['id'] + "'\n")
        manifest.write("    sort: " + str(p['sort']) + "\n")
        manifest.write("    path: '" + p['path'] + "'\n")
        manifest.write("    categories: " + p['category'] + "\n")
    manifest.close()

class UsxErrorHandler(xml.sax.ErrorHandler):
    def error(e):
        print(e)
        reportError("Error reported by usx parser")

    def warning(e):
        print(e)
        reportStatus("Warning reported by usx parser")

class UsxHandler(xml.sax.ContentHandler):
    # Implements ContentHandler.startDocument
    def startDocument(self):
        self.writer = None
        self.elements = []
        self.styles = []
        self.pop = 0
        self.chapter = "0"

    # Implements ContentHandler.startElement
    def startElement(self, name, attrs):
        style = "" if not 'style' in attrs else attrs['style']
        self.elements.append(name)
        self.styles.append(style)
        handled = False
        if name == "book":
            self.startUsfm(attrs['code'])
            self.location = attrs['code']
            handled = True
        elif name == "para":
            if not self.ignorable_style(style):
                self.writer.writeUsfm(style)
                handled = True
        elif name == "char" and style in {"add", "k", "nd", "pn", "qac", "qs", "qt", "sig", "sls", "tl", "wj"}:
            handled = True
        elif name == "verse":
            if "sid" in attrs:
                self.location = attrs['sid']
            else:
                self.location = f"{self.bookId} {self.chapter}:{attrs['number']}"
            self.writer.writeUsfm(style, attrs['number'])
            handled = True
        elif name == "chapter":
            self.chapter = attrs['number']
            if "sid" in attrs:
                self.location = attrs['sid']
            else:
                self.location = f"{self.bookId} {self.chapter}"
            self.writer.writeUsfm(style, attrs['number'])
            handled = True
        elif name == 'usx':
            handled = True

        if not handled and self.pop < 1:
            self.pop = len(self.elements)

    # Implements ContentHandler.endElement
    def endElement(self, name):
        if name != self.elements[-1]:
            reportError(f"Internal error: endElement({name}) at {self.location}")
        if len(self.elements) != len(self.styles):
            reportError(f"Internal error: unequal elements ({len(self.elements)}) and styles ({len(self.styles)}) lengths. At {self.location}")
        if len(self.elements) == self.pop:
            self.pop = 0
            reportIgnored(name, self.styles[-1], self.location)
        self.elements = self.elements[0:-1]
        self.styles = self.styles[0:-1]
        if name == "book":
            self.writer.writeUsfm("ide", "UTF-8")
        elif name == "usx":
            self.writer.close()
            if self.bookId in usfm_verses.verseCounts and usfm_verses.verseCounts[self.bookId]['sort'] <= 66:
                # otherwise, bookTitle doesn't exist -> crash
                appendToProjects(self.bookId, self.bookTitle)

    def ignorable_style(self, style):
        ignorable = (style[0] == 'i' and style not in {'it','id'}) or style in {'mr','r'}
        return ignorable

    # Implements ContentHandler.characters
    def characters(self, content):
        content = content.strip()
        if content and self.pop == 0:
            self.writer.writeStr(content)
        if self.elements[-1] == 'para' and self.styles[-1] in {'mt','mt1'}:
            self.bookTitle = content

    # Create and open the usfm file for the book specified in attrs.
    # Remember the book id.
    def startUsfm(self, id):
        self.bookId = id
        path = makeUsfmPath(id)
        self.writer = usfmWriter.usfmWriter(path)
        self.writer.writeUsfm("id", id)
        # reportStatus("Creating " + shortname(path))

    # For possible future use
    def writeNote(self, attrs):
        self.writer.writeUsfm(attrs['style'], attrs['caller'])

reported_note_x = False
reported_note_f = False
reported_note_r = False
reported_note_g = False

def reportIgnored(name, style, location):
    msg = None
    global reported_note_x
    global reported_note_f
    global reported_note_r
    global reported_note_g
    if (name, style) == ("note", "x"):
        if not reported_note_x:
            reported_note_x = True
            msg = f'Ignored all occurrences of <{name} style="{style}">'
    elif (name, style) == ("note", "f"):
        if not reported_note_f:
            reported_note_f = True
            msg = f'Ignored all occurrences of <{name} style="{style}">'
    elif (name, style) == ('para', 'r'):
        if not reported_note_r:
            reported_note_r = True
            msg = f'Ignored all occurrences of <{name} style="{style}">'
    elif location == "GLO":
        if not reported_note_g:
            reported_note_g = True
            msg = f"Ignored most GLO content"
    else:
        msg = f'Ignored <{name} style="{style}"> at {location}'
    if msg:
        reportStatus(msg)

# Returns the value corresponding to the specified key in attrs
# attrs must be a list of (key,value) pairs)
def getValue(attrs, key):
    value = None
    for (k,v) in attrs.items():
        if k == key:
            value = v
            break
    return value

def makeUsfmName(bookId):
    if bookId in usfm_verses.verseCounts:
        num = usfm_verses.verseCounts[bookId]['usfm_number']
        name = f"{num}-{bookId}.usfm"
    else:
        name = f"{bookId}.usfm"
    return name

# Returns file name for usfm file in target folder
def makeUsfmPath(bookId):
    return os.path.join(config['usfm_dir'], makeUsfmName(bookId))

def convertFile(usxpath):
    global reported_note_x
    global reported_note_f
    global reported_note_r
    global reported_note_g
    reported_note_x = False
    reported_note_f = False
    reported_note_r = False
    reported_note_g = False
    reportStatus("\nConverting: " + shortname(usxpath))
    parser = xml.sax.make_parser()
    parser.setContentHandler(UsxHandler())
    parser.setErrorHandler(UsxErrorHandler())
    with io.open(usxpath, "tr", encoding="utf-8-sig") as usxfile:
        parser.parse(usxfile)

def convertFolder(folder):
    for entry in os.listdir(folder):
        if entry[0] != '.':
            path = os.path.join(folder, entry)
            if os.path.isdir(path):
                convertFolder(path)
            elif entry.lower().endswith(".usx"):
                convertFile(path)
    dumpProjects(config['usfm_dir'])

def main(app=None):
    global gui
    global config

    gui = app
    config = configmanager.ToolsConfigManager().get_section('Usx2Usfm')
    if config:
        Path(config['usfm_dir']).mkdir(exist_ok=True)
        usx_dir = config['usx_dir']
        file = config['filename']
        if file:
            path = os.path.join(usx_dir, file)
            if os.path.isfile(path):
                convertFile(path)
            else:
                reportError(f"No such file: {path}")
        else:
            convertFolder(usx_dir)
    if gui:
        gui.event_generate('<<ScriptEnd>>', when="tail")
    else:
        reportStatus("The conversion is done.")
    global issuesFile
    if issuesFile:
        issuesFile.close()
        issuesFile = None   # needed for when the process is rerun in same Python session

if __name__ == "__main__":
    main()