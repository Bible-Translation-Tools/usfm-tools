# -*- coding: utf-8 -*-
# Support for footnotes
# There are only a few external functions:
#   getFootnotedVerses(dir="")
#   reset()
#   validSourceDir(dir) -- safe to use, but should not be necessary to use, except by unit tests
#   preScanned(dir) -- safe to use, but should not be necessary to use, except by unit tests

import os
import io
import sys
import re
import json
import usfmReader
import usfm_utils

# Verses with footnotes in the English ULB. (Default set)
footnotedVerses_en_ulb = {
  "GEN 1:26",
  "GEN 4:8",
  "GEN 10:4",
  "GEN 31:25",
  "LEV 20:7",
  "NUM 21:14",
  "NUM 24:24",
  "JOS 5:1",
  "JOS 9:4",
  "JOS 13:5",
  "JDG 3:3",
  "RUT 2:7",
  "RUT 3:3",
  "1SA 1:1",
  "1SA 1:24",
  "1SA 1:28",
  "1SA 6:19",
  "1SA 8:16",
  "1SA 10:27",
  "1SA 14:41",
  "1SA 20:41",
  "1SA 22:3",
  "1SA 27:8",
  "2SA 8:18",
  "2SA 17:25",
  "2SA 21:8",
  "2SA 23:8",
  "2SA 23:27",
  "2SA 23:29",
  "2SA 23:36",
  "1KI 2:26",
  "1KI 4:4",
  "1KI 5:11",
  "1KI 5:18",
  "1KI 7:7",
  "1KI 9:18",
  "1KI 10:8",
  "1KI 12:2",
  "2KI 12:21",
  "2KI 15:16",
  "2KI 24:3",
  "1CH 1:4",
  "1CH 1:6",
  "1CH 2:7",
  "1CH 2:24",
  "1CH 3:5",
  "1CH 4:12",
  "1CH 4:13",
  "1CH 4:17",
  "1CH 6:27",
  "1CH 6:59",
  "1CH 6:77",
  "1CH 9:19",
  "1CH 11:11",
  "1CH 15:18",
  "1CH 25:2",
  "1CH 25:3",
  "1CH 25:4",
  "1CH 25:11",
  "1CH 25:14",
  "1CH 25:18",
  "1CH 26:1",
  "1CH 26:2",
  "1CH 26:14",
  "1CH 26:18",
  "2CH 1:5",
  "2CH 2:10",
  "2CH 3:10",
  "2CH 4:16",
  "2CH 9:4",
  "2CH 9:7",
  "2CH 16:4",
  "2CH 17:3",
  "2CH 20:1",
  "2CH 20:2",
  "2CH 20:9",
  "2CH 20:25",
  "2CH 22:11",
  "2CH 23:20",
  "2CH 26:5",
  "2CH 31:16",
  "2CH 32:5",
  "2CH 32:22",
  "2CH 32:29",
  "2CH 33:19",
  "2CH 34:21",
  "2CH 36:2",
  "EZR 3:9",
  "EZR 4:6",
  "EZR 4:9",
  "EZR 8:10",
  "EZR 10:25",
  "EZR 10:29",
  "EZR 10:38",
  "EZR 10:40",
  "EZR 10:44",
  "NEH 7:43",
  "NEH 7:70",
  "NEH 8:7",
  "NEH 11:8",
  "NEH 11:35",
  "NEH 12:14",
  "NEH 12:17",
  "EST 1:1",
  "JOB 15:30",
  "JOB 17:11",
  "JOB 23:2",
  "JOB 30:22",
  "JOB 36:27",
  "PSA 8:2",
  "PSA 18:13",
  "PSA 68:4",
  "PSA 68:18",
  "PSA 68:26",
  "PSA 77:11",
  "PSA 83:7",
  "PSA 84:6",
  "PSA 89:8",
  "PSA 89:19",
  "PSA 94:7",
  "PSA 94:12",
  "PSA 102:18",
  "PSA 104:35",
  "PSA 105:45",
  "PSA 106:1",
  "PSA 106:48",
  "PSA 111:1",
  "PSA 112:1",
  "PSA 113:1",
  "PSA 113:9",
  "PSA 115:17",
  "PSA 115:18",
  "PSA 116:19",
  "PSA 117:2",
  "PSA 118:5",
  "PSA 118:14",
  "PSA 118:17",
  "PSA 118:18",
  "PSA 118:19",
  "PSA 122:4",
  "PSA 130:3",
  "PSA 135:1",
  "PSA 135:3",
  "PSA 135:4",
  "PSA 135:21",
  "PSA 146:1",
  "PSA 146:10",
  "PSA 147:1",
  "PSA 147:20",
  "PSA 148:1",
  "PSA 148:14",
  "PSA 149:1",
  "PSA 149:9",
  "PSA 150:1",
  "PSA 150:6",
  "PRO 7:22",
  "PRO 13:15",
  "PRO 21:29",
  "PRO 25:27",
  "PRO 27:9",
  "PRO 30:1",
  "ECC 2:8",
  "ECC 3:15",
  "ECC 3:21",
  "ECC 7:18",
  "ECC 8:8",
  "ECC 8:9",
  "ECC 8:10",
  "ECC 9:2",
  "ECC 11:5",
  "SNG 5:6",
  "SNG 5:13",
  "SNG 6:13",
  "SNG 7:6",
  "SNG 7:9",
  "SNG 7:11",
  "SNG 8:10",
  "ISA 1:17",
  "ISA 5:17",
  "ISA 7:2",
  "ISA 9:2",
  "ISA 9:20",
  "ISA 10:27",
  "ISA 12:2",
  "ISA 14:4",
  "ISA 19:13",
  "ISA 19:18",
  "ISA 21:8",
  "ISA 23:1",
  "ISA 23:2",
  "ISA 23:10",
  "ISA 26:4",
  "ISA 26:16",
  "ISA 27:8",
  "ISA 28:25",
  "ISA 33:8",
  "ISA 33:9",
  "ISA 37:25",
  "ISA 38:11",
  "ISA 38:13",
  "ISA 40:3",
  "ISA 40:9",
  "ISA 49:24",
  "ISA 51:19",
  "ISA 52:5",
  "ISA 53:11",
  "ISA 57:9",
  "ISA 66:17",
  "ISA 66:18",
  "ISA 66:19",
  "JER 2:10",
  "JER 2:11",
  "JER 13:4",
  "JER 13:7",
  "JER 15:14",
  "JER 25:38",
  "JER 27:1",
  "JER 28:8",
  "JER 43:12",
  "JER 46:9",
  "JER 49:1",
  "EZK 6:14",
  "EZK 7:5",
  "EZK 16:6",
  "EZK 16:57",
  "EZK 18:10",
  "EZK 19:7",
  "EZK 19:10",
  "EZK 22:16",
  "EZK 22:25",
  "EZK 26:20",
  "EZK 27:13",
  "EZK 32:9",
  "EZK 37:23",
  "EZK 40:6",
  "EZK 40:48",
  "EZK 40:49",
  "EZK 41:1",
  "EZK 41:22",
  "EZK 42:4",
  "EZK 42:10",
  "EZK 42:16",
  "EZK 42:17",
  "EZK 42:18",
  "EZK 42:19",
  "EZK 43:3",
  "EZK 45:1",
  "EZK 46:22",
  "EZK 47:15",
  "EZK 47:18",
  "EZK 47:22",
  "DAN 9:1",
  "DAN 10:13",
  "DAN 11:6",
  "DAN 11:39",
  "HOS 5:2",
  "HOS 7:14",
  "HOS 11:2",
  "HOS 14:2",
  "AMO 8:14",
  "MIC 5:1",
  "MIC 5:6",
  "MIC 6:9",
  "MIC 6:14",
  "MIC 6:16",
  "HAB 1:9",
  "HAB 2:1",
  "HAB 2:15",
  "HAB 3:1",
  "ZEP 1:5",
  "ZEP 3:8",
  "ZEP 3:18",
  "ZEC 5:6",
  "ZEC 9:8",
  "ZEC 10:4",
  "MAL 2:3",
  "MAL 2:12",
  "MAT 5:44",
  "MAT 6:13",
  "MAT 15:6",
  "MAT 17:21",
  "MAT 18:11",
  "MAT 19:9",
  "MAT 20:16",
  "MAT 23:14",
  "MAT 27:16",
  "MRK 6:3",
  "MRK 7:16",
  "MRK 7:25",
  "MRK 9:44",
  "MRK 9:46",
  "MRK 11:26",
  "MRK 13:33",
  "MRK 14:68",
  "MRK 15:28",
  "MRK 15:40",
  "MRK 16:9",
  "MRK 16:20",
  "LUK 2:14",
  "LUK 2:33",
  "LUK 2:49",
  "LUK 8:43",
  "LUK 10:1",
  "LUK 11:11",
  "LUK 17:36",
  "LUK 18:24",
  "LUK 23:17",
  "JHN 5:3",
  "JHN 5:4",
  "JHN 6:69",
  "JHN 7:53",
  "JHN 8:1",
  "JHN 8:11",
  "ACT 7:46",
  "ACT 8:37",
  "ACT 10:19",
  "ACT 10:32",
  "ACT 10:33",
  "ACT 12:25",
  "ACT 13:18",
  "ACT 15:18",
  "ACT 15:34",
  "ACT 19:40",
  "ACT 20:28",
  "ACT 24:6",
  "ACT 24:7",
  "ACT 28:29",
  "ROM 8:28",
  "ROM 11:6",
  "ROM 16:24",
  "1CO 2:1",
  "1CO 2:10",
  "1CO 9:20",
  "1CO 10:28",
  "1CO 13:3",
  "1CO 16:24",
  "2CO 8:7",
  "2CO 13:12",
  "2CO 13:13",
  "GAL 2:19",
  "EPH 1:1",
  "EPH 1:5",
  "PHP 4:23",
  "COL 1:2",
  "COL 1:7",
  "COL 1:12",
  "COL 1:14",
  "COL 2:13",
  "COL 3:4",
  "COL 3:6",
  "COL 4:8",
  "1TH 1:1",
  "1TH 2:7",
  "1TH 3:2",
  "2TH 2:3",
  "2TH 2:13",
  "1TI 6:5",
  "2TI 1:11",
  "2TI 2:14",
  "HEB 2:7",
  "HEB 4:2",
  "HEB 9:11",
  "HEB 10:34",
  "HEB 11:11",
  "HEB 11:37",
  "HEB 12:20",
  "JAS 2:20",
  "1PE 1:22",
  "2PE 2:4",
  "2PE 2:13",
  "2PE 2:15",
  "2PE 3:10",
  "1JN 1:4",
  "1JN 3:1",
  "1JN 4:3",
  "1JN 5:8",
  "REV 1:8",
  "REV 5:14",
  "REV 8:7",
  "REV 8:13",
  "REV 11:17",
  "REV 22:14",
  "REV 22:19",
  "REV 22:21"}

class State:
    def __init__(self):
        self.IDs = []
        self.ID = ""
        self.chapter = 0
        self.verse = 0
        self.reference = ""
        self.footnoteRefs = set()
        self.canContinue = True
        self.loadedDir = None

    def setLoadedDir(self, dir):
        self.loadedDir = dir

    # Resets state data for a new book
    def addID(self, id):
        self.IDs.append(id)
        self.ID = id
        self.chapter = 0
        self.verse = 0
        self.reference = id

    def getIDs(self):
        return self.IDs

    def addChapter(self, c):
        self.chapter = int(c)
        self.verse = 0
        self.reference = self.ID + " " + c

    def addVerse(self, v):
        self.verse = int(v)
        self.reference = self.ID + " " + str(self.chapter) + ":" + v

    # Adds the current reference to the list of footnote references
    def addFootnote(self):
        self.footnoteRefs.add(self.reference)

state = State()

# Resets to initial state, where no footnote references have been loaded.
def reset():
    global state
    state = State()

# Returns True if the specified folder contains any USFM files.
def validSourceDir(dir):
    valid = False
    if os.path.isdir(dir):
        with os.scandir(dir) as it:
            for entry in it:
                if entry.name.lower().endswith('sfm') and entry.is_file():
                    valid = True
                    break
    return valid

# Returns True if the specified folder has already been scanned for footnote locations.
# @TODO Check for .usfm file dates newer than the .json date. (Maybe a separate function.)
def preScanned(dir):
    if not dir:
        return False
    fvpath = os.path.join(dir, "footnotedVerses.json")
    return os.path.isfile(fvpath)

# Returns the set of footnoted verses found in the usfm files in dir.
# If no value for dir, returns the current set, if any, or the default set, which is from English UDB.
def getFootnotedVerses(dir=""):
    global state
    if not state:
        state = State()
    if dir and preScanned(dir):
        _loadPrescanned(dir)
    elif validSourceDir(dir):
        _scanFootnotes(dir)
    elif not dir:
        state.footnoteRefs = footnotedVerses_en_ulb
        state.loadedDir = ""
    return state.footnoteRefs

# Loads the pre-scanned set of footnoted verses if possible.
# Sets state.footnoteRefs and state.loadedDir, or leaves them unchanged.
def _loadPrescanned(dir):
    global state
    if dir != state.loadedDir:
        fvpath = os.path.join(dir, "footnotedVerses.json")
        if os.path.isfile(fvpath):
            with io.open(fvpath, 'r') as json_file:
                state.footnoteRefs = set( json.load(json_file) )  # JSON saves a list
            state.setLoadedDir(dir)

# Scans all USFM files in the specified folder and saves the results.
# Sets state.footnoteRefs and state.loadedDir, or leaves them unchanged.
def _scanFootnotes(dir):
    global state
    state.footnoteRefs.clear()
    if os.path.isdir(dir):
        _processDir(dir)
        state.setLoadedDir(dir)
        _saveReferences( os.path.join(dir, "footnotedVerses.json") )

# Scans the usfm files in the specified folder only.
def _processDir(dirpath):
    global state
    with os.scandir(dirpath) as it:
        for entry in it:
            if entry.name.lower().endswith('sfm') and entry.is_file():
                state.canContinue = True
                _processFile(entry.path)

# Adds the footnoted verse references from the specified file to state.footnoteRefs.
def _processFile(path):
    global state
    state.canContinue = True
    with io.open(path, "tr", 1, encoding="utf-8-sig") as input:
        contents = input.read(-1)
    if "lemma=" in contents or "x-occurrences" in contents:
        contents = usfm_utils.unalign_usfm(contents)

    for token in usfmReader.parseString(contents):
        _take(token)
        if not state.canContinue:
            break
    state.addID("")

def _take(token: usfmReader.Token):
    if token.type in {'f','f*'}:
        state.addFootnote()
    if token.type == 'id':
        _takeID(token.value)
    elif token.type == 'c':
        if not state.ID:        # means this usfm file is invalid
            _reportError("Missing book ID: " + state.reference)
            state.canContinue = False
        _takeC(token.value)
    elif token.type == 'v':
        _takeV(token.value)

def _takeID(id):
    if len(id) < 3:
        _reportError("Invalid ID: " + id)
    id = id[0:3].upper()
    if id in state.getIDs():
        _reportError("Duplicate ID: " + id)
    state.addID(id)

def _takeC(c):
    state.addChapter(c)

vv_re = re.compile(r'([0-9]+)-([0-9]+)')

# Receives a string containing a verse number or range of verse numbers.
# Reports errors related to the verse number(s), such as missing or duplicated verses.
def _takeV(vstr):
    vlist = []
    if vstr.find('-') > 0:
        vv_range = vv_re.search(vstr)
        if vv_range:
            vn = int(vv_range.group(1))
            vnEnd = int(vv_range.group(2))
            while vn <= vnEnd:
                vlist.append(vn)
                vn += 1
        else:
            _reportError("Problem in verse range near " + state.reference)
    else:
        vlist.append(int(vstr))

    for vn in vlist:
        v = str(vn)
        state.addVerse(str(vn))

# Writes error message to stderr and to issues.txt.
def _reportError(msg):
    try:
        sys.stderr.write(msg + "\n")
    except UnicodeEncodeError as e:
        msg = state.reference if state else ""
        sys.stderr.write(msg + ": (Unicode...)\n")

# Saves the current list of footnoted verses to the specified file location.
# Note: JSON can't directly save a set, so save as a list.
def _saveReferences(fvpath):
    with io.open(fvpath, 'w') as json_file:
        json.dump( list(state.footnoteRefs), json_file, indent=2)
