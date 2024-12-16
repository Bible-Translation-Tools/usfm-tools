# -*- coding: utf-8 -*-
# This script converts text files containing whole books of the Bible to usfm files.
# The input format of the text files is flexible, generally intended to support 
# free form translation.
# The following are the minimum input format restrictions:
#    Each file contains a single book of the Bible, and no extraneous text.
#    The file names match XXX.txt or NN-XXX.txt, where XXX is the 3-character book id
#       and NN is the stardard, 2-digit number.
#    UTF-8 encoding is required.
#    Chapter and verse numbers are in Arabic numerals (0-9).
#
# The following additional restrictions will result in better conversion outcomes:
#    The input files already contain some (correct) usfm markers.
#    The first line of each file contains the indigenous book title.
#
# The script performs these operations:
#    Populates the USFM headers.
#    Standardizes the names of .usfm files. For example 41-MAT.usfm and 42-MRK.usfm.
#    Converts multiple books at once if there are multiple books.
#    Reports failure when chapter 1 is not found, and other errors.
# The script does not mark chunks. If that is desired. run usfm2rc.py later.

import configmanager
import usfm_verses
from usfmWriter import usfmWriter
import re
import operator
import io
import os
import sys
from pathlib import Path

config = None
gui = None
state = None
projects = []
issues_file = None
wroteHeader = False

# Entities
ID = 1
TITLE = 2
CHAPTER = 3
VERSE = 4
TEXT = 5
EOF = 6

class State:
    def __init__(self):
        self.ID = ""
        self.data = ""
        self.title = ""
        self.chapter = 0
        self.verse = 0
        self.reference = ""
        self.lastRef = ""
        self.lastEntity = None
        self.neednext = ID
        self.priority = ID
        self.usfm_file = None
        self.missing_chapters = []

    # Resets state data for a new book
    # Writes the \id and \ide fields to the usfm file.
    def addID(self, id):
        self.ID = id
        self.data = ""
        self.title = ""
        self.titletags = []
        self.chapter = 0
        self.verse = 0
        self.missing_chapters = []
        self.lastRef = self.reference + "0"
        self.lastEntity = ID
        self.neednext = {TITLE}
        self.priority = TITLE
        self.usfm_file = usfmWriter(makeUsfmPath(id))

    def addRemark(self, text):
        if not text.startswith("\\rem "):
            text = "\\rem " + text
        if self.data:
            self.data += '\n'
        self.data += text

    def addTitle(self, titletext, lineno, usfmtag=None):
        if usfmtag:
            self.usfm_file.writeUsfm(usfmtag, titletext)
            self.titletags.append(usfmtag)
            if not self.title:
                self.title = titletext.title()  # convert to title case
        elif len(titletext) <= 40:
            self.title += (" " if self.title else "") + titletext
        else:
            self.addRemark(titletext)
        self.lastEntity = TITLE
        self.neednext = {CHAPTER, TITLE}
        self.priority = CHAPTER

    def addChapter(self, nchap):
        self.data = ""
        self.chapter = nchap
        self.verse = 0
        self.lastRef = self.reference
        self.reference = self.ID + " " + str(nchap) + ":"
        self.lastEntity = CHAPTER
        self.neednext = {VERSE}
        self.priority = VERSE
        if nchap in self.missing_chapters:
            self.missing_chapters.remove(nchap)

    # Adds the specified chapter number to the list of missing chapters.
    # If we haven't even found chapter 1 yet, treats the text as front matter.
    def missingChapter(self, text, nchap):
        if not nchap in self.missing_chapters:
            self.missing_chapters.append(nchap)
        if self.chapter < 1:
            self.addFrontMatter(text)

    # Adds the line of text as is without touching any other state
    # Supports texts where chapter labels or section headings are tagged: \cl or \s
    def addMarkedLine(self, text):
        if self.title:
            self.data += "\n" + text
        else:
            self.data = ('\n' if self.data else '') + text

    def addVerse(self, vstr):
        self.data = ""
        self.verse = int(vstr)
        self.lastRef = self.reference
        self.reference = self.ID + " " + str(self.chapter) + ":" + vstr
        self.lastEntity = VERSE
        self.neednext = {TEXT}
        self.priority = TEXT

    def addTextData(self, text):
        if len(self.data) > 0:
            self.data += ' '
        text = text.lstrip(". ")   # lose period after preceding verse number
        self.data += text.strip()  # lose other leading and trailing white space
        self.addText()

    def addText(self):
        if self.lastEntity != TEXT:
            self.neednext = {VERSE, CHAPTER, TEXT}
            self.priority = whatsNext(self.ID, self.chapter, self.verse)
            self.lastEntity = VERSE

    # Called when the end of file is reached
    def addEOF(self):
        self.data = ""
        self.usfm_file.close()
        self.lastRef = self.reference
        self.lastEntity = EOF
        self.neednext = {ID}
        self.priority = ID
        if self.chapter == 0:
            self.title = ""
            self.lastref = self.ID + " 0"

# Determines whether a verse or a chapter is expected next.
# Based on the current book, chapter and verse as specified by the arguments.
# Not all languages and translation follow the same versification scheme, however.
# Returns VERSE, CHAPTER, or EOF
def whatsNext(book, chapter, verse):
    if verse < usfm_verses.verseCounts[book]['verses'][chapter-1]:
        next = VERSE
    elif chapter < usfm_verses.verseCounts[book]['chapters']:
        next = CHAPTER
    else:
        next = EOF
    return next

def writePending():
    if state.data:
        state.usfm_file.writeStr(re.sub(" +", " ", state.data))
        state.data = ""

vv_re = re.compile(r'([0-9]+)-([0-9]+)')

# cstr is the entire chapter label, often just the chapter number.
def takeChapter(cstr, nchap):
    writePending()
    if state.lastEntity == TITLE and not wroteHeader:
        writeHeader()
    schap = str(nchap)
    state.usfm_file.writeUsfm("c", schap)
    if len(cstr) > len(schap):
        # cl = cstr[len(schap):] if cstr.startswith(schap) else cstr
        state.usfm_file.writeUsfm("cl", cstr)
    state.addChapter(nchap)

vrange_re = re.compile(r'([0-9])+-([0-9]+)')

# vstr contains only the verse number, or a verse number range
def takeVerseNumber(vstr):
    writePending()
    if state.verse == 0:
        state.usfm_file.writeUsfm("p")
    state.usfm_file.writeUsfm("v", vstr)
    if range := vrange_re.search(vstr):
        state.addVerse(range.group(1))
        state.addVerse(range.group(2))
    else:
        state.addVerse(vstr)

nrun_re = re.compile(r'[\d\-]+')

# The string s starts with verse number and continues with the first line of verse text.
# The string must have been preceded by \\v.
def takeV(s, lineno):
    nrun = nrun_re.match(s)
    if nrun:
        vstr = nrun.group(0)
        if vstr.endswith('-'):
            vstr = vstr[:-1]
        takeVerseNumber(vstr)
        if len(s) > len(vstr):
            state.usfm_file.writeStr(s[len(vstr):])     # normally this writes the verse text
            state.addText()
    else:
        take("\\v " + s, lineno)

# The string s starts with chapter number and may have more text, considered a chapter label.
def takeC(s, lineno):
    if nrun := nrun_re.match(s):
        schap = nrun.group(0)
        takeChapter(s, int(schap))
        if len(s) > len(schap):
            state.usfm_file.writeUsfm("cl", s[len(schap):])
        state.addChapter(int(schap))
    else:
        take("\\c " + s, lineno)

# Verify that the encounter \id field matches previously identified book id.
def takeId(id, lineno):
    if id != state.ID:
        reportError(f"Book id found on line {lineno} (\\id {id}) contradicts file name.")

def takeTitle(s, lineno, tag):
    state.addTitle(s, lineno, tag)

def takeSection(s, lineno):
    writePending()
    if not wroteHeader:
        writeHeader()
    state.usfm_file.writeUsfm('s', s)

def takeMarkedText(tag, remainder, lineno):
    remainder = remainder.strip()
    if tag == 'id':
        takeId(remainder)
    elif tag == 'v':
        takeV(remainder, lineno)
    elif tag == 'c':
        takeC(remainder, lineno)
    elif tag in {'h', 'mt', 'mt1'}:
        takeTitle(remainder, lineno, tag)
    elif tag in {'s', 's1'}:
        takeSection(remainder, lineno)
    else:
        state.usfm_file.writeUsfm(tag, remainder)

tag_re = re.compile(r'\\([a-z]+[1-4]?)')
# titletag_re = re.compile(r'\\(h|mt) (.*)')

# Processes a single line of input.
# The line has already been stripped of leading and trailing spaces.
def takeLine(line, lineno):
    mark = tag_re.search(line)
    if not mark:
        take(line, lineno)
    if mark and mark.start() > 0:     # handle the text preceding the usfm tag
        take(line[:mark.start()], lineno)
    endpos = 0
    while mark:
        pos = endpos + mark.start()
        endpos = endpos + mark.end()
        tag = mark.group(1)
        mark = tag_re.search(line[endpos:])
        if mark:
            remainder = line[endpos:endpos+mark.start()]
        else:
            remainder = line[endpos:]
        # nextpos = endpos + mark.start() if mark else -1
        # takeMarkedText(tag, line[endpos:nextpos], lineno)
        takeMarkedText(tag, remainder, lineno)

    # if line.startswith(r'\c '):
    #     cstr = line[3:]
    #     try:
    #         takeChapter(cstr, int(cstr))
    #     except ValueError as e:
    #         state.addMarkedLine(line)
    # elif tag := titletag_re.match(line):
    #     state.addTitle(tag.group(2), lineno, tag.group(1))
    # elif line.startswith(r'\s') or line.startswith(r'\rem '):
    #     state.addMarkedLine(line)
    # # elif line.startswith(r'\rem '):
    # else:
    #     take(line, lineno)

# Handles the next bit of text, which may be a line or part of a line.
# Uses recursion to handle complex lines.
def take(s, lineno):
    if state.priority == EOF:
        state.priority = TEXT
    if state.priority == TITLE:
        if len(s) > 40:
            reportError("First line is too long to be considered a book title.")
        else:
            state.addTitle(s, lineno)
    elif state.priority == CHAPTER:
        if hasnumber(s, state.chapter+1) >= 0 and len(s) < 25:    # may have to allow longer s
            takeChapter(s, state.chapter+1)
        elif TITLE in state.neednext:   # haven't reached chapter 1 yet
            state.addTitle(s, lineno)
        elif VERSE in state.neednext:
            (pretext, vv, remainder) = getvv(s, state.verse+1)
            if vv:
                if pretext:
                    take(pretext, lineno)
                takeVerseNumber(vv)
                if remainder:
                    take(remainder, lineno)
            elif TEXT in state.neednext:
                state.addTextData(s)
        elif TEXT in state.neednext:
            state.addTextData(s)
        else:
            state.missingChapter(s, state.chapter+1)
    elif state.priority == VERSE:
        (pretext, vv, remainder) = getvv(s, state.verse+1)
        if not vv and state.verse+1 < usfm_verses.verseCounts[state.ID]['verses'][state.chapter-1]:
            (pretext, vv, remainder) = getvv(s, state.verse+2)
            missingVerse = f"{state.ID} {state.chapter}:{state.verse+1}"
            if vv:
                reportError(f"Can't find {missingVerse}.")
        if vv:
            if pretext:
                take(pretext, lineno)
            takeVerseNumber(vv)
            if remainder:
                take(remainder, lineno)
        elif CHAPTER in state.neednext and hasnumber(s, state.chapter+1) >= 0:
            takeChapter(s, state.chapter+1)
        elif TEXT in state.neednext:
            state.addTextData(s)
        else:
            reportError("Expected verse not found. (" + state.reference + str(state.verse+1) + ", line " + str(lineno) + ")")
            if state.chapter > 0 and state.verse == 0:
                reportError(f"Is {state.ID} {state.chapter-1}:{state.chapter} missing?")
    elif state.priority == TEXT:
        (pretext, vv, remainder) = getvv(s, state.verse+1)
        if not vv and state.verse+1 < usfm_verses.verseCounts[state.ID]['verses'][state.chapter-1]:
            (pretext, vv, remainder) = getvv(s, state.verse+2)
            missingVerse = f"{state.ID} {state.chapter}:{state.verse+1}"
            if vv:
                reportError(f"Can't find {missingVerse}.")
        if vv:
            if pretext:
                state.addTextData(pretext)
            takeVerseNumber(vv)
            if remainder:
                take(remainder, lineno)
        else:
            state.addTextData(s)
    else:
        reportError("Internal error at line " + str(lineno) + " in the text.")

# Extracts specified verse number or verse range beginning with that number.
# Return a (pretext, vv, remainder) tuple.
# If the specified verse is not found, returns ("","","")
def getvv(s, n):
    pos = hasnumber(s, n)
    if pos < 0:
        pretext = ""
        vv = ""
        remainder = ""
    else:
        vtok = re.search(f'\\\\v +{str(n)}', s)
        # posvmarker = s.find("\\v ")
        if vtok:
        # if -1 < posvmarker < pos:
            pretext = s[0:vtok.start()]
        else:
            pretext = s[0:pos]
        if range := vrange_re.match(s[pos:]):
            vv = s[pos:range.end()]
        else:
            vv = str(n)
        if len(s) > pos + len(vv):
            remainder = s[pos + len(vv):]
        else:
            remainder = ""
    return (pretext, vv, remainder)


# Searches for the specified number in the string.
# Returns the position of the specified number in the string, or -1
def hasnumber(s, n):
    s = isolateNumbers(s)
    nstr = str(n)
    if s == nstr or s.startswith(nstr + " "):
        pos = 0
    elif s.endswith(" " + nstr):
        pos = len(s) - len(nstr)
    else:
        pos = s.find(" " + nstr + " ")
        if pos >= 0:
            pos += 1
    return pos

# Returns a string with all non-numeric characters changed to a space.
def isolateNumbers(s):
    t = ""
    for i in range(0,len(s)):
        if s[i] in "0123456789":
            t += s[i]
        else:
            t += ' '
    return t

# Writes error message to stderr and to issues.txt.
def reportError(msg):
    reportToGui('<<ScriptMessage>>', msg)
    write(msg, sys.stderr)
    openIssuesFile().write(msg + "\n")

# Sends a progress message to the GUI, and to stdout.
def reportProgress(msg):
    reportToGui('<<ScriptProgress>>', msg)
    write(msg, sys.stdout)

# Sends a status message to the GUI, and to stdout.
def reportStatus(msg):
    reportToGui('<<ScriptMessage>>', msg)
    write(msg, sys.stdout)

def reportToGui(event, msg):
    if gui:
        with gui.progress_lock:
            gui.progress = msg if not gui.progress else f"{gui.progress}\n{msg}"
        gui.event_generate(event, when="tail")

# This little function streams the specified message and handles UnicodeEncodeError
# exceptions, which are common in Indian language texts. 2/5/24.
def write(msg, stream):
    try:
        stream.write(msg + "\n")
    except UnicodeEncodeError as e:
        stream.write(state.reference + ": (Unicode...)\n")

# If issues.txt file is not already open, opens it for writing.
# First renames existing issues.txt file to issues-oldest.txt unless
# issues-oldest.txt already exists.
# Returns file pointer.
def openIssuesFile():
    global issues_file
    if not issues_file:
        path = os.path.join(config['source_dir'], "issues.txt")
        if os.path.exists(path):
            bakpath = os.path.join(config['source_dir'], "issues-oldest.txt")
            if not os.path.exists(bakpath):
                os.rename(path, bakpath)
        issues_file = io.open(path, "tw", buffering=2048, encoding='utf-8', newline='\n')
    return issues_file

def closeIssuesFile():
    global issues_file
    if issues_file:
        issues_file.close()
        issues_file = None

num_name_re = re.compile(r'([0-6][0-9]?)[ \-\.]*([A-Za-z1-3][A-Za-z][A-Za-z])')

# Parses the book id from the file name.
# Return upper case bookId, or empty string on failure.
def getBookId(filename):
    bookId = None
    id = ""
    (fname, ext) = os.path.splitext(filename)
    if ext == ".txt" and len(fname) == 3:
        id = fname
    else:
        if num_name := num_name_re.match(fname):
            id = num_name.group(2)
    if id.upper() in usfm_verses.verseCounts:
        bookId = id.upper()
    else:
        reportError(f"Cannot identify book from file name: {filename}.\n  Use XXX.txt or NN-XXX.txt")
    return bookId

# Appends information about the current book to the global projects list.
def appendToProjects(bookId, bookTitle):
    global projects
    testament = 'nt'
    if usfm_verses.verseCounts[bookId]['sort'] < 40:
        testament = 'ot'
    project = { "title": bookTitle, "id": bookId.lower(), "sort": usfm_verses.verseCounts[bookId]["sort"], \
                "path": "./" + makeUsfmFilename(bookId), "category": "[ 'bible-" + testament + "' ]" }
    projects.append(project)

# Writes list of projects converted to the specified file.
# The resulting file can be used as the projects section of manifest.yaml.
def dumpProjects(path):
    projects.sort(key=operator.itemgetter('sort'))

    manifest = io.open(path, "tw", buffering=1, encoding='utf-8', newline='\n')
    manifest.write("projects:\n")
    for p in projects:
        manifest.write("  -\n")
        manifest.write("    title: '" + p['title'] + "'\n")
        manifest.write("    versification: ufw\n")
        manifest.write("    identifier: '" + p['id'] + "'\n")
        manifest.write("    sort: " + str(p['sort']) + "\n")
        manifest.write("    path: '" + p['path'] + "'\n")
        manifest.write("    categories: " + p['category'] + "\n")
    manifest.close()

def shortname(longpath):
    source_dir = Path(config['source_dir'])
    shortname = Path(longpath)
    if shortname.is_relative_to(source_dir):
        shortname = shortname.relative_to(source_dir)
    return str(shortname)

# Generates name for usfm file
def makeUsfmPath(bookId):
    return os.path.join(config['target_dir'], makeUsfmFilename(bookId))

    # Generates name for usfm file
def makeUsfmFilename(bookId):
    num = usfm_verses.verseCounts[bookId]['usfm_number']
    return num + '-' + bookId + '.usfm'


# Write the usfm header field that follow \id and \ide.
def writeHeader():
    global wroteHeader
    for tag in ['h', 'mt', 'toc1', 'toc2']:
        if tag not in state.titletags:
            state.usfm_file.writeUsfm(tag, state.title)
    state.usfm_file.writeUsfm("toc3", state.ID.lower())
    state.usfm_file.newline(2)
    wroteHeader = True

def initUsfm(bookId):
    state.addID(bookId)     # creates usfm file
    state.usfm_file.writeUsfm("id", bookId)
    state.usfm_file.writeUsfm("ide", "UTF-8")
    writePending()   # Write any text that preceded the book ID

# This method is called to convert the specified file to usfm.
# It processes the input line by line.
def convertBook(path, bookId):
    reportProgress(f"Converting: {shortname(path)}...")
    sys.stdout.flush()
    global wroteHeader
    wroteHeader = False

    with io.open(path, "tr", 1, encoding='utf-8-sig') as input:
        lines = input.readlines()
    lineno = 0
    for line in lines:
        lineno += 1
        line = line.strip()
        if len(line) > 0:
            takeLine(line, lineno)
    # end of file
    writePending()
    state.addEOF()
    if state.missing_chapters:
        reportError("Chapter number(s) " + str(state.missing_chapters) + " not found in " + shortname(path))

def convertFolder(folder):
    for entry in os.listdir(folder):
        path = os.path.join(folder, entry)
        if os.path.isdir(path) and entry[0] != '.':
            convertFolder(path)
        elif os.path.isfile(path) and entry.endswith(".txt") and not entry.startswith("issues"):
            bookId = getBookId(entry)
            if bookId:
                initUsfm(bookId)
                convertBook(path, bookId)
            if bookId and state.title:
                appendToProjects(bookId, state.title)
            else:
                if not bookId:
                    reportError("Unable to identify " + shortname(path) + " as a Bible book.")
                elif not state.title:
                    reportError("Book title not found in: " + shortname(path))

def main(app = None):
    global gui
    gui = app
    projects.clear()
    global config
    config = configmanager.ToolsConfigManager().get_section('Plaintext2Usfm')
    if config:
        global state
        state = State()
        source_dir = config['source_dir']
        file = config['filename']
        target_dir = config['target_dir']
        Path(target_dir).mkdir(exist_ok=True)

        if file:
            path = os.path.join(source_dir, file)
            if os.path.isfile(path):
                bookId = getBookId(file)
                if bookId:
                    initUsfm(bookId)
                    convertBook(path, bookId)
                if not state.title:
                    reportError(f"Book title not found in: {shortname(path)}")
            else:
                reportError(f"No such file: {path}")
        else:
            convertFolder(source_dir)
            if projects:
                dumpProjects( os.path.join(target_dir, "projects.yaml") )

    closeIssuesFile()
    reportStatus("\nDone.")
    sys.stdout.flush()
    if gui:
        gui.event_generate('<<ScriptEnd>>', when="tail")

# Processes each directory and its files one at a time
if __name__ == "__main__":
    main()
