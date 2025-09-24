# -*- coding: utf-8 -*-
# This script converts one or more valid .usfm files by adding paragraph marks.
# The model used for marking paragraphs are the USFM files in model_dir.
# Inserts paragraph marker after each chapter marker if needed, before verse 1.
# Also terminates sentences before a paragraph break, with punctuation from model text.
# Marks unmarked text as section headings where present in model.
# The input file(s) should be verified, correct USFM, except for unmarked text which may become section headings.
# Ensures a paragraph mark after every section heading.

from configmanager import ToolsConfigManager
import sys
import os
import usfmReader
import io
import re
import shutil
import sentences
import usfm_verses
import usfmWriter
import yaml
import section_titles
from datetime import datetime
from usfm_utils import unicodeBlock
# import cProfile

gui = None
# s5_only = False   # s5_only is the inverse of removes5markers
removes5markers = True
sentence_sensitive = True   # this is no longer configurable via the config file
copy_nb = False
nChanges = 0  # number of changes made
    # includes paragraphs, sections, and terminating punctuation copied from model,
    # and the number of \s5 markers removed.
issuesFile = None

class State:
    def __init__(self):
        self.reset_data("")
        self.model = ""     # e.g. "English UDB version 21-05"

    # Resets the state data for the next Bible book
    def reset_data(self, fname):
        self.fname = fname
        self.modelBlock = ''   # Unicode block of model text
        self.block = ''     # Unicode block of text being modified
        self.chapter = self.verse = 0
        self.bridge = 0
        self.pChapter = self.pVerse = 0
        self.s5chapter = self.s5verse = -1
        self.needPmarker = 0
        self.reference = fname
        self.paragraphs_model = []
        self.sections_model = []
        self.endPunctuation = ''
        self.lastText = ''
        self.expectText = False
        self.legacyBackup = False
        self.prevTokenType = self.currTokenType = ''

    def __repr__(self):
        return f'State({self.reference})'

    # Called only during the scanning phase, not the marking phase
    def addFile(self, fname):
        self.reset_data(fname)
        ## Open output USFM file for writing.
        source_dir = ToolsConfigManager().get('MarkParagraphs', 'source_dir')
        tmpPath = os.path.join(source_dir, fname + ".tmp")
        self.usfm = usfmWriter.usfmWriter(tmpPath)

    def addID(self, id):
        self.ID = id
        self.chapter = 0
        self.verse = 0
        self.bridge = 0
        self.expectText = False
        self.midSentence = False

    def addChapter(self, c):
        self.lastChapter = self.chapter
        if c.isnumeric():
            self.chapter = int(c)
            self.verse = 0
            self.bridge = 0
            self.reference = self.ID[0:3].upper() + " chapter " + c
        self.lastText = ''
        self.expectText = False
        self.needPmarker = 1    # need \p or \q before verse 1

    # Records the location of a paragraph marker found in the input text...
    # 8/9/24 ... or added by takeV() or takeText()
    def addP(self, nextverse):
        self.pChapter = self.chapter
        self.pVerse = nextverse
        self.lastText = ''
        self.expectText = True
        self.needPmarker = 0

    def addQ(self):
        self.lastText = ''
        self.expectText = True
        self.needPmarker = 0

    # Sets expectText and needPmarker to ensure that \p will follow any section marker
    # Do not use this method for \s5 markers.
    def addS(self, tag):
        self.midSentence = False    # fair assumption
        self.lastText = ''
        self.expectText = False
        # self.sChapter = self.chapter
        # self.sVerse = self.bridge
        self.sTag = tag
        self.needPmarker = self.bridge + 1

    def addS5(self):
        self.midSentence = False
        self.lastText = ''
        self.expectText = False
        self.sTag = "s5"
        self.s5chapter = self.chapter
        self.s5verse = self.bridge

    # Called only during the marking phase, not the scanning phase
    def addText(self, text):
        self.expectText = False
        self.midSentence = not sentences.endsSentence(text)
        self.lastText = text.rstrip()

    def addVerse(self, v):
        v1 = v.split('-')[0]
        v2 = v.split('-')[-1]
        if v1.isnumeric() and v2.isnumeric():
            self.verse = int(v1)
            self.bridge = int(v2)
            self.reference = self.ID[0:3].upper() + " " + str(self.chapter) + ":" + v
        if self.prevTokenType == 'v':
            self.lastText = ''   # last verse was empty
            self.midSentence = False
        self.expectText = True

    def addFootnote(self):
        self.expectText = True
        self.lastText = ''

    def saveTokenType(self, type):
        self.prevTokenType = self.currTokenType
        self.currTokenType = type

    def needP(self):
        return self.needPmarker

    # Returns True if a paragraph mark was already recorded for the current or next verse.
    # See addP()
    def pAlready(self, current):
        currVerse = self.verse if current else self.verse + 1
        return self.pVerse >= currVerse and self.pChapter == self.chapter

    # Returns True if an \s5 was already marked on the preceding verse.
    def s5Already(self):
        return (self.s5verse == self.bridge and self.s5chapter == self.chapter)

    # Returns the paragraph mark that occurred in the model text at the current location,
    # and the punctuation ending the preceding sentence in the model text.
    def pmarkInModel(self):
        pmark = punct = None
        for pp in self.paragraphs_model:
            if pp['chapter'] == self.chapter and pp['verse'] == self.verse and pp['located']:
                pmark = pp['mark']
                punct = pp['endPunc']
                break
        return (pmark, punct)

    # Returns True immediately after a verse or paragraph marker or footnote.
    def expectingText(self):
        return self.verse > 0 and self.expectText

    # Returns the section mark that occurred in the model file at the current location,
    # and the punctuation ending the preceding sentence.
    def smarkInModel(self):
        smark = punct = None
        for s in self.sections_model:
            if s['chapter'] == self.chapter and s['verse'] == self.verse and s['located']:
                smark = s['mark']
                punct = s['endPunc']
                break
        return (smark, punct)

    # Returns True if current verse is the last verse in a chapter
    def isEndOfChapter(self):
        chaps = usfm_verses.verseCounts[self.ID]['verses']
        return (self.verse >= chaps[self.chapter-1])

    def terminateSentence(self):
        self.midSentence = False

    # Returns True if the most recent text does not end a sentence.
    def isMidSentence(self):
        return self.midSentence

    def usfmClose(self):
        self.usfm.close()
    def keepBackup(self, keep=True):
        self.legacyBackup = keep

    def identifyModel(self, identity):
        self.model = identity

    def setModelBlock(self, block:str):
        self.modelBlock = block
    def getModelBlock(self):
        return self.modelBlock
    def setBlock(self, block:str):
        self.block = block
    def getBlock(self):
        return self.block

# Loads the specified yaml file and reports errors.
# Returns the contents of the file if no errors.
def parseYaml(path):
    contents = None
    if os.path.isfile(path):
        with io.open(path, "tr", encoding='utf-8-sig') as file:
            try:
                contents = yaml.safe_load(file)
            except yaml.scanner.ScannerError as e:
                reportError(f"Yaml syntax error at or before line {e.problem_mark.line} in: {path}")
            except yaml.parser.ParserError as e:
                reportError(f"Yaml parsing error at or before line {e.problem_mark.line} in: {path}")
    else:
        reportError(f"File missing: {path}")
    return contents

def identifyModel(model_dir):
    path = os.path.join(model_dir, "manifest.yaml")
    manifest = parseYaml(path)
    if manifest:
        core = manifest['dublin_core']
        language = core['language']['title']
        identifier = core['identifier'].upper()
        version = core['version']
        state.identifyModel(f"{language} {identifier} version {version}")

punctuated_re = re.compile(r'[^\w\s]\s*$')

# Returns True if the string ends with a punctuation mark.
def punctuated(s):
    return (punctuated_re.search(s) != None)

def mayTerminateLastSentence(punct):
    if punct and state.getBlock() == state.getModelBlock() and state.lastText and not punctuated(state.lastText):
        state.usfm.writeStr(punct)
        state.terminateSentence()
        # reportStatus(f"Added punctuation at {state.reference}")
        global nChanges
        nChanges += 1

# Inserts \s5 mark if needed
def mayInsertS5(newchapter=False):
    if not removes5markers and not state.s5Already():
        global s5_only

        smark = ''
        if not newchapter:
            (smark, punct) = state.smarkInModel()

        # if (newchapter and s5_only) or (smark == "s5" and not removes5markers):
        if smark == "s5" or newchapter:
            mayTerminateLastSentence(punct)
            state.usfm.writeUsfm("s5")
            state.addS5()
            global nChanges
            nChanges += 1

# Write character style tags to the file with or without a newline as appropriate
def takeStyle(key):
    state.usfm.writeUsfm(key, None)

# Write to the file with or without a newline as appropriate
def takeAsIs(key, value):
    state.usfm.writeUsfm(key, value)

def takeFootnote(key, value):
    state.addFootnote()
    state.usfm.writeUsfm(key, value)

def takeID(id):
    if len(id) < 3:
        reportError("Invalid ID: " + id)
    state.usfm.writeUsfm("id", id)
    state.addID( id[0:3].upper() )
    state.usfm.writeUsfm("rem", f"Paragraph marks have been added, using {state.model} as a model.")

# Copies paragraph marker to output unless one was aleady added.
# Insert \s5 first, if needed.
def takeP(tag, value, nexttoken):
    if nexttoken.type == 'v':
        mayInsertS5()
        if not state.pAlready(current=False):
            state.addP(state.bridge+1)
            state.usfm.writeUsfm(tag, value)
    else:
        state.addP(state.bridge)
        state.usfm.writeUsfm(tag, value)

def takeS5():
    # global removes5markers
    if not state.s5Already() and not removes5markers:
        state.usfm.writeUsfm("s5", None)
        state.addS5()
    else:
        global nChanges
        nChanges += 1

def takeS(tag, value):
    state.addS(tag)
    state.usfm.writeUsfm(tag, value)

vv_re = re.compile(r'([0-9]+)-([0-9]+)')

def takeV(v):
    global nChanges
    global s5_only

    mayInsertS5()
    state.addVerse(v)
    if not state.pAlready(current=True) and removes5markers:
        (pmark, punct) = state.pmarkInModel()
        if pmark:
            if punct and not isPoetry(pmark):
                mayTerminateLastSentence(punct)
            if isPoetry(pmark) or not state.isMidSentence() or not sentence_sensitive:
                state.usfm.writeUsfm(pmark)
                state.addP(state.verse)
                nChanges += 1
    if not state.pAlready(current=True) and state.needP() == state.verse:  # occasioned by chapter or section heading
        state.usfm.writeUsfm("p")
        state.addP(state.verse)
        nChanges += 1
    state.usfm.writeUsfm("v", v)

def takeText(t):
    global nChanges
    smark = None
    t = t.strip()
    if not state.expectingText() and (not state.isMidSentence() or not sentence_sensitive):
        (smark, punct) = state.smarkInModel()
    if not state.getBlock() and state.verse > 0 and len(t) > 10:
        state.setBlock(unicodeBlock(t))
        if state.getBlock() != state.getModelBlock():
            reportStatus(f"The script is {state.getBlock()} but the model is {state.getModelBlock()}, \
so sentence termination functionality is disabled.")

    ####### This is the case where the model has a section heading, and t might be a section heading on a line by itself #######
    if smark and smark != "s5" and section_titles.is_possible_heading(t):
        mayTerminateLastSentence(punct)
        state.usfm.writeUsfm(smark, t)
        nChanges += 1
        state.addP(state.bridge+1)
        state.usfm.writeUsfm("p")
    ################# This is the normal case ################
    else:
        if state.prevTokenType == 'text':
            state.usfm.newline()    # preserve the line break
        state.usfm.writeStr(t)
        state.addText(t)

# Output chapter
# If we are copying \s5 markers, insert one before every chapter
def takeC(c):
    (mark, punct) = state.smarkInModel()
    if not punct:
        (mark, punct) = state.pmarkInModel()
    mayTerminateLastSentence(punct)
    mayInsertS5(newchapter=True)
    state.addChapter(c)
    state.usfm.writeUsfm("c", c)

# Handles the specified token from the input file.
# Inserts paragraph and section markers where needed from model.
def take(token, nexttoken):
    state.saveTokenType(token.type)
    if token.type == 'v':
        takeV(token.value)
    elif token.type == 'text':
        takeText(token.value)
    elif token.type == 'c':
        takeC(token.value)
    elif isParagraph(token, scanning=False):
        takeP(token.type, token.value, nexttoken)
    elif isPoetry(token.type):
        # takeQ(token.type, token.value, nexttoken)
        takeP(token.type, token.value, nexttoken)
    elif token.type == 's5':
        takeS5()
    elif token.isSection():
        takeS(token.type, token.value)
    elif token.type == 'id':
        takeID(token.value)
    elif token.isFootnote():
        takeFootnote(token.type, token.value)
    elif token.isCharacterStyle():
        takeStyle(token.type)
    else:
        takeAsIs(token.type, token.value)

def isParagraph(token: usfmReader.Token, scanning):
    isp = token.isParagraph()
    if isp and scanning and not copy_nb and token.type in {'nb', 'b', 'm'}:
        isp = False
    return isp

def isPoetry(mark):
    return mark in {'q','q1','q2','q3','qa','qr','qc', 'qss','d','sp'}

backslash_re = re.compile(r'\\\s')
jammed_re = re.compile(r'(\\v +[-0-9]+[^-\s0-9])', re.UNICODE)
usfmcode_re = re.compile(r'(\\[^a-z\+\s])', re.UNICODE)

def isParseable(text, usfmpath, fname):
    parseable = True
    if backslash_re.search(text):
        reportError(f"{fname} contains stranded backslash(es) followed by space or end of line")
        parseable = False

    if bad := jammed_re.search(text):
        reportError(f"{fname} contains verse number(s) not followed by space: {bad.group(1)}")
        parseable = True   # let it convert because the bad spots are easier to locate in the converted USFM
    for badcode in re.finditer(usfmcode_re, text):
        reportError(f"{fname} contains foreign usfm code: {badcode.group(1)}")
        parseable = False
    if os.path.getsize(usfmpath) < 1000:
        reportError(f"{usfmpath} is incomplete, too small")
        parseable = False
    return parseable

# Returns False if the usfm file is not parseable.
def convertFile(usfmpath, fname):
    global nChanges
    startn = nChanges
    if not state.fname:
        reportError("Internal error: State is not initialized")  # first pass (scan) sets the state
        sys.exit(-1)
    with io.open(usfmpath, "tr", 1, encoding="utf-8-sig") as input:
        str = input.read(-1)
    sys.stdout.flush()
    success = isParseable(str, usfmpath, fname)
    if success:
        reportProgress(f"Marking {fname}")
        sys.stdout.flush()
        tokens = usfmReader.parseString(str)
        token = tokens[0]   # safe because isParseable should reject empty files
        for nexttoken in tokens[1:]:
            take(token, nexttoken)
            token = nexttoken
        take(token, token)
        state.usfmClose()
        if nChanges > startn:
            renameUsfmFiles(usfmpath)
        else:
            sys.stdout.write(f"  No changes to {fname}\n")
            removeTempFiles(usfmpath)
    else:
        state.usfmClose()
        removeTempFiles(usfmpath)
    return success

# Converts the book or books contained in the specified folder
def convertFolder(folder):
    if not os.path.isdir(folder):
        reportError("Invalid folder path given: " + folder)
        return
    for fname in os.listdir(folder):
        path = os.path.join(folder, fname)
        if fname[0] != '.' and os.path.isdir(path):
            convertFolder(path)
        elif fname.endswith('sfm'):
            processFile(path)

# Copies specified file to same file name with orig appended.
# Does not overwrite existing backup file.
def backupUsfmFile(path):
    bakpath = path + "orig"
    if not os.path.isfile(bakpath):
        shutil.copyfile(path, bakpath)
    else:
        state.keepBackup(True)

# Deletes temp file and backup file, and leaves original file unchanged.
def removeTempFiles(path):
    os.remove(path + ".tmp")
    if not state.legacyBackup:
        os.remove(path + "orig")

# Renames temp usfmfile to its original name, overwriting the original usfm file.
def renameUsfmFiles(usfmpath):
    tmppath = usfmpath + ".tmp"
    if os.path.isfile(tmppath):
        if os.path.isfile(usfmpath):
            try:
                os.remove(usfmpath)
            except PermissionError as e:
                reportError(f"Cannot convert {usfmpath}: {e.strerror}")
                return
        os.rename(tmppath, usfmpath)

# Returns the modified date/time of the specified file, formatted as a string.
def get_timestamp(path):
    mtime = os.path.getmtime(path)
    dt = datetime.fromtimestamp(mtime)
    s = dt.strftime("%Y%m%d%H%M")
    return s[2:]

# If issues.txt file is not already open, opens it for writing.
# First saves existing issues.txt file to another name.
# Returns new file pointer.
def openIssuesFile():
    global issuesFile
    if not issuesFile:
        workdir = ToolsConfigManager().get('MarkParagraphs', 'source_dir')
        path = os.path.join(workdir, "issues.txt")
        if os.path.exists(path):
            timestamp = get_timestamp(path)
            bakpath = os.path.join(workdir, f"issues-{timestamp}.txt")
            if not os.path.exists(bakpath):
                os.rename(path, bakpath)
        issuesFile = io.open(path, "tw", encoding='utf-8', newline='\n')
        issuesFile.write("Issues detected by MarkParagraphs:\n------------------------------------\n")
    return issuesFile

#def openReportFile():
    #global reportFile
    #if not reportFile:
        #global source_dir
        #path = os.path.join(source_dir, "uncopied pp marks.txt")
        #reportFile = io.open(path, "tw", buffering=4096, encoding='utf-8', newline='\n')
    #return reportFile

def closeIssuesFiles():
    global issuesFile
    if issuesFile:
        issuesFile.close()
        issuesFile = None

# Writes message to stderr and to issues.txt.
# If it is not a real issue, writes message to report file.
def reportError(msg, realIssue=True):
    if realIssue:
        reportStatus(msg)     # message to gui
        try:
            sys.stderr.write(msg + "\n")
        except UnicodeEncodeError as e:
            sys.stderr.write(state.reference + ": (Unicode...)\n")
        if issues := openIssuesFile():
            issues.write(msg + "\n")
    #else:
        #report = openReportFile()
        #report.write(msg + "\n")

# Sends a progress report to the GUI, and to stdout.
def reportProgress(msg):
    global gui
    if gui:
        with gui.progress_lock:
            gui.progress = msg if not gui.progress else f"{gui.progress}\n{msg}"
        gui.event_generate('<<ScriptProgress>>', when="tail")
    print(msg)

def reportStatus(msg):
    global gui
    if gui:
        with gui.progress_lock:
            gui.progress = msg if not gui.progress else f"{gui.progress}\n{msg}"
        gui.event_generate('<<ScriptMessage>>', when="tail")
    print(msg)

# Sets the chapter number in the state object
# If there is still a tentative paragraph mark, remove it.
def scanC(c):
    state.addChapter(c)
    if len(state.paragraphs_model) > 0:
        pp = state.paragraphs_model[-1]
        if not pp['located']:
            reportError(f"Paragraph mark (\\{pp['mark']}) before {state.reference} not copied", False)
            state.paragraphs_model.remove(pp)

# Save the paragraph mark and its tentative location
# If the previous paragraph mark is still tentative, it is invalid, overwrite it in the state.
def scanPQ(type):
    p = {}
    p['mark'] = type
    p['chapter'] = state.chapter
    p['verse'] = 0      # verse unknown
    p['located'] = False
    p['endPunc'] = state.endPunctuation
    if len(state.paragraphs_model) > 0:
        pp = state.paragraphs_model[-1]
        if not pp['located']:
            state.paragraphs_model.remove(pp)
    state.paragraphs_model.append(p)

# Save the section mark and its location.
# Unlike paragraph marks, sections marks take the previous verse number as their location.
def scanS(type):
    section = {}
    section['mark'] = type
    section['chapter'] = state.chapter
    section['verse'] = state.verse
    section['located'] = True
    section['endPunc'] = state.endPunctuation
    state.sections_model.append(section)

# Removes the last paragraph mark from the list if it is not already located to
# a specific verse, because it apparently occurs in the middle of a verse.
def scanText(text):
    if len(state.paragraphs_model) > 0:
        pp = state.paragraphs_model[-1]
        if not pp['located']:
            reportError(f"Paragraph mark (\\{pp['mark']}) within {state.reference} not copied", False)
            state.paragraphs_model.remove(pp)
    state.endPunctuation = sentences.endsSentence(text) # endPunctuation is a temporary holding place
    if not state.getModelBlock() and state.verse > 0 and len(text) > 10:
        state.setModelBlock(unicodeBlock(text))

# v is the verse number or range
# Assign the verse number to the preceding paragraph mark, if any.
# Unlike sections, paragraphs take the location of the following verse.
def scanV(v):
    state.addVerse(v)
    v1 = v.split('-')[0]
    if len(state.paragraphs_model) > 0:
        pp = state.paragraphs_model[-1]     # the last pq found
        if not pp['located']:
            pp['verse'] = int(v1)
            pp['located'] = True

# Analyzes the specified token in the model file.
# Only cares about locations of paragraphs.
def scan(token: usfmReader.Token):
    if token.type == 'c':
        scanC(token.value)
    elif token.type == 'v':
        scanV(token.value)
    elif token.type == 'text':
        scanText(token.value)
    elif isParagraph(token, scanning=True) or isPoetry(token.type):
        scanPQ(token.type)
    elif token.isSection():
        scanS(token.type)
    elif token.type== 'id':
        state.addID(token.value)

# Gathers the location and type of all paragraph marks in the model USFM file.
def scanModelFile(modelpath, fname):
    success = False
    if os.path.isfile(modelpath):
        input = io.open(modelpath, "tr", 1, encoding="utf-8-sig")
        str = input.read(-1)
        input.close()
        sys.stdout.flush()
        success = isParseable(str, modelpath, os.path.basename(modelpath))
        if success:
            reportProgress(f"Parsing model file: {fname}")
            sys.stdout.flush()
            state.addFile(fname)
            tokens = usfmReader.parseString(str)
            for token in tokens:
                scan(token)
    return success

# def countParagraphs(path):
#     with io.open(path, "tr", 1, encoding="utf-8-sig") as input:
#         str = input.read(-1)
#     nchapters = str.count("\\c ")
#     nparagraphs = str.count("\\p") + str.count("\\nb") + str.count("\\li")
#     npoetry = str.count("\\q")
#     return (nchapters, nparagraphs, npoetry)

def processFile(path):
    fname = os.path.basename(path)
    model_dir = ToolsConfigManager().get('MarkParagraphs', 'model_dir')
    model_path = os.path.join(model_dir, fname)
    if os.path.isfile(model_path):
        # cmd = f"scanModelFile( r'{model_path}', '{fname}' )"
        # cProfile.run(cmd)
        if scanModelFile(model_path, fname):
            backupUsfmFile(path)
            if not convertFile(path, fname):
                reportError("File cannot be converted: " + fname)
        else:
            reportError("Model file is unusable; file cannot be processed " + fname)
    else:
        reportError("Model file not found; file cannot be processed: " + fname)

state = State()

# Processes each directory and its files one at a time
def main(app = None):
    global gui
    gui = app
    global nChanges
    nChanges = 0
    # global s5_only
    global removes5markers
    # global sentence_sensitive
    global copy_nb

    config = ToolsConfigManager()
    # s5_only = config.getboolean('MarkParagraphs', 's5_only')
    removes5markers = config.getboolean('MarkParagraphs', 'removeS5markers')
    # sentence_sensitive = config.getboolean('MarkParagraphs', 'sentence_sensitive')
    copy_nb = config.getboolean('MarkParagraphs', 'copy_nb')
    identifyModel(config.get('MarkParagraphs', 'model_dir'))
    source_dir = config.get('MarkParagraphs', 'source_dir')
    file = config.get('MarkParagraphs', 'filename')
    if file:
        path = os.path.join(source_dir, file)
        if os.path.isfile(path):
            processFile(path)
        else:
            reportError(f"File does not exist: {path}")
    else:
        convertFolder(source_dir)

    closeIssuesFiles()
    reportStatus(f"\nDone.")
    if nChanges > 0:
        reportStatus("Changes were made.")
    if gui:
        gui.event_generate('<<ScriptEnd>>', when="tail")

if __name__ == "__main__":
    main()
