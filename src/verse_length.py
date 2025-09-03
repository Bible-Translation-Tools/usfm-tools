# -*- coding: utf-8 -*-
# Experimentation with verse lengths, detecting very short and extra long verses.

gui = None
listener = None # Reuben sets this externally
issuesFile = None
issues: dict = {}   # Can't put in State because we want to accumulate issues across all files.
lengths = dict()
lengths_src = dict()
footnotedVerses = {}
footnotedVerses_en_ulb = {}
nFiles = 0  # number of .usfm files verified
primarily_ascii = False

from configmanager import ToolsConfigManager
import os
from pathlib import Path
import sys
import usfmReader
import io
import footnotes
import usfm_verses
import re
import usfm_utils
from datetime import date, datetime

# Item categories
PP = 1      # paragraph or quote
QQ = 2      # poetry
B = 3       # \b for blank line; no titles, text, or verse markers may immediately follow
C = 4       # \c
S = 5
OTHER = 9

# Manages the verify state for a single usfm file.
class State:
    def __init__(self):
        self.IDs = []       # list of book IDs that have been processed
        self.ID = ""
        self.reference = ""
        self.errorRefs = set()
        self.scanning = False    # True when scanning source text
        self.sourcetext = {}    # verse-reference: verse-text
        self.source_nverses = {}  # chapter-reference: number of verses
        self.sourcefootnote = {}    # verse-reference: text of footnote(s)
        self.booklength_src = 1
        self.booklength = 1
        self.canContinue = True
        self.source_id = "en_ulb"
        self.initBook()

    def initBook(self):
        self.usfm_version = 2
        self.aligned_usfm = False
        self.booktitles = []
        self.chaptertitles = []
        self.nChapterLabels = 0
        self.nParagraphs = 0
        self.nPoetry = 0
        self.chapter = 0
        self.verse = 0
        self.lastVerse = 0
        self.lastToken = None
        self.startChunkVerse = 1
        self.needPP = False
        self.needQQ = False
        self.needVerseText = False
        self.inVerse = False
        self.versetext = ""
        self.textOkayHere = False
        self.footnote_starts = 0
        self.footnote_ends = 0
        self.endnote_starts = 0
        self.endnote_ends = 0
        self.reference = ""
        self.lastRef = ""
        self.startChunkRef = ""
        self.currItemCategory = OTHER
        self.prevItemCategory = OTHER
        self.toc3 = None
        self.upperCaseReported = False

    def __repr__(self):
        return f'State({self.reference})'

    # Resets state data for a new book
    # The scan parameter is set when source text is being parsed.
    def addID(self, id):
        self.initBook()
        self.reference = id + " header/intro"
        self.ID = id
        if self.scanning:
            self.sourcetext.clear()
            self.source_nverses.clear()
            self.sourcefootnote.clear()
        elif id and id not in self.IDs:
            self.IDs.append(id)

    def addTitle(self, bookTitle):
        self.booktitles.append(bookTitle)
        self.prevItemCategory = self.currItemCategory
        self.currItemCategory = OTHER
        self.inVerse = False

    def addToc3(self, toc3):
        self.toc3 = toc3
        self.inVerse = False

    def addB(self):
        self.prevItemCategory = self.currItemCategory
        self.currItemCategory = B

    def addChapter(self, c: str):
        self.lastChapter = self.chapter
        self.chapter = int(c)
        self.needPP = True
        self.inVerse = False
        self.lastVerse = 0
        self.verse = 0
        self.needVerseText = False
        self.textOkayHere = False
        self.lastRef = self.reference
        self.reference = self.ID + " " + c
        self.startChunkRef = self.reference + ":1"
        self.prevItemCategory = self.currItemCategory
        self.currItemCategory = C
        if self.scanning:
            state.source_nverses[state.reference] = 1

    # Isolate the word/phrase for "chapter" from the given string.
    # Add it to the list of chapter titles.
    def addChapterLabel(self, title):
        if title not in self.chaptertitles:
            self.chaptertitles.append(title)
        self.nChapterLabels += 1
        self.inVerse = False
        return title    # without chapter number, but spacing unchanged

    def addUncountedParagraph(self):
        self.needPP = False
        self.textOkayHere = True
        self.prevItemCategory = self.currItemCategory
        self.currItemCategory = PP

    def addParagraph(self):
        self.nParagraphs += 1
        self.needPP = False
        self.needQQ = False
        self.textOkayHere = True
        self.prevItemCategory = self.currItemCategory
        self.currItemCategory = PP

    def addPoetry(self, value):
        self.nPoetry += 1
        self.needQQ = False
        self.needPP = False
        self.textOkayHere = True
        if value:
            self.needVerseText = False
        self.prevItemCategory = self.currItemCategory
        self.currItemCategory = QQ

    def addSection(self, tag):
        self.prevItemCategory = self.currItemCategory
        self.currItemCategory = S
        self.inVerse = False

    # Records the start of a new chunk
    def addS5(self):
        self.startChunkVerse = self.verse + 1
        self.startChunkRef = self.ID + " " + str(self.chapter) + ":" + str(self.startChunkVerse)

    def addVerse(self, v: str):
        self.lastVerse = self.verse
        try:
            self.verse = int(v.split('-')[-1])
        except ValueError as e:
            pass
        self.needVerseText = True
        self.inVerse = True
        self.versetext = ""
        self.textOkayHere = True
        self.lastRef = self.reference
        self.reference = self.ID + " " + str(self.chapter) + ":" + v
        self.prevItemCategory = self.currItemCategory
        self.currItemCategory = OTHER
        if self.scanning:
            chapref = self.ID + " " + str(self.chapter)
            self.source_nverses[chapref] = self.verse

    # Returns the number of verses in the current chapter in the source text.
    # Returns 0 if no data for the current chapter.
    def nVerses_source(self):
        n = 0
        if self.source_nverses:
            chapref = self.ID + " " + str(self.chapter)
            n = self.source_nverses[chapref]
        return n

    def addAcrosticHeading(self):
        self.textOkayHere = True
        self.needQQ = True

    # Completes processing of the specified (current) token
    def advance(self, token):
        self.lastToken = token

    def setAlignedUsfm(self, aligned):
        self.aligned_usfm = aligned
    def setUsfmVersion(self, version):
        self.usfm_version = version

    # Resets needQQ flag so that errors are not repeated verse after verse
    def resetPoetry(self):
        self.needQQ = False

    def textOkay(self):
        return self.textOkayHere

    def needText(self):
        return self.needVerseText

    def getTextLength(self):
        return len(self.versetext)

    def addText(self, text):
        self.prevItemCategory = self.currItemCategory
        self.currItemCategory = OTHER
        self.needVerseText = False
        if text and text not in '-+':
            self.versetext += text + " "
        self.textOkayHere = True
        global lengths
        lengths[state.reference] = len(self.versetext)

    def inFootnote(self):
        return self.footnote_starts > self.footnote_ends or self.endnote_starts > self.endnote_ends

    # Increments \f counter
    def addFootnoteStart(self):
        self.footnote_starts += 1
        self.prevItemCategory = self.currItemCategory
        self.currItemCategory = OTHER
        self.needVerseText = False
        self.textOkayHere = True

    # Increments \f* counter
    def addFootnoteEnd(self):
        self.footnote_ends += 1
        self.needVerseText = False
        self.textOkayHere = True

    # Increments \fe counter
    def addEndnoteStart(self):
        self.endnote_starts += 1
        self.prevItemCategory = self.currItemCategory
        self.currItemCategory = OTHER
        self.needVerseText = False
        self.textOkayHere = True

    # Increments \fe* counter
    def addEndnoteEnd(self):
        self.endnote_ends += 1
        self.needVerseText = False
        self.textOkayHere = True

    # Simply appends the text to the sourcetext for the current verse
    def addSourceText(self, t):
        if self.reference in self.sourcetext:
            state.sourcetext[state.reference] += " " + t
        else:
            state.sourcetext[state.reference] = t
        global lengths_src
        lengths_src[state.reference] = len(t)

    def addSourceFootnote(self, t):
        if self.reference in self.sourcefootnote:
            state.sourcefootnote[state.reference] += " " + t
        else:
            state.sourcefootnote[state.reference] = t

    # Adds the specified reference to the set of error references
    # Returns True if reference can be added
    # Returns False if reference was previously added
    def addError(self, ref):
        success = False
        if ref not in self.errorRefs:
            self.errorRefs.add(ref)
            success = True
        return success

state: State

# Returns the category of the specified marker.
def category(token: usfmReader.Token):
    category = OTHER
    if token.type == 'b':
        category = B
    elif token.type == 'c':
        category = C
    elif token.type in {'p','pi','pc','nb','m'}:
        category = PP
    elif token.isPoetry():
        category = QQ
    return category

# Tries to interpret the specified string as an integer, regardless of language.
# Returns 0 if unable to interpret.
def decimal_value(s):
    s = s.strip()
    return int(s) if s.isdecimal() else 0

# Returns the number of chapters that the specified book should contain.
# Returns 0 if the book id is invalid.
def nChapters(id):
    n = 0
    if id in usfm_verses.verseCounts:
        n = usfm_verses.verseCounts[id]['chapters']
    return n

# Returns the number of verses that the specified chapter contains in the NIV.
def nVerses_niv(id, chap):
    chaps = usfm_verses.verseCounts[id]['verses']
    n = 0 if chap > len(chaps) else chaps[chap-1]
    return n

# Returns the English title for the specified book
def bookTitleEnglish(id):
    return usfm_verses.verseCounts[id]['en_name']

def shortname(longpath):
    config = ToolsConfigManager()
    workdir = Path(config.get('VerseLength', 'work_dir'))
    shortname = Path(longpath)
    if shortname.is_relative_to(workdir):
        shortname = shortname.relative_to(workdir)
    return str(shortname)

# Returns the modified date/time of the specified file, formatted as a string.
def get_timestamp(path):
    mtime = os.path.getmtime(path)
    dt = datetime.fromtimestamp(mtime)
    s = dt.strftime("%Y%m%d%H%M")
    return s[2:]

# If vlissues.txt file is not already open, opens it for writing.
# Returns file pointer.
def openIssuesFile():
    global issuesFile
    if not issuesFile:
        config = ToolsConfigManager()
        workdir = config.get('VerseLength', 'work_dir')
        path = os.path.join(workdir, "vlissues.txt")
        issuesFile = io.open(path, "tw", encoding='utf-8', newline='\n')
        issuesFile.write(f"Issues detected by verse_length version {config.get('UsfmWizard', 'version')}, {date.today()}, {workdir}\n")
        if compare_dir := config.get('VerseLength', 'compare_dir'):
            issuesFile.write(f"   with reference to {identifySource(compare_dir)} as the source text.\n")
        issuesFile.write("-------------------\n")
    return issuesFile

# Returns the longest common substring at the start of s1 and s2
def long_substring(s1, s2):
    if s1.startswith(s2):
        return s2
    i = 0
    while i < len(s1) and i < len(s2) and s1[i] == s2[i]:
        i += 1
    return s1[0:i]

# Writes error message to stderr and to issues.txt.
# Keeps track of how many errors of each type.
def reportError(msg, errorId=0.0, summarize_only=False):
    if not summarize_only:
        reportToGui('<<ScriptMessage>>', msg)
        write(msg, sys.stderr)
        openIssuesFile().write(msg + "\n")
    if listener:
        listener.error(msg, errorId)

    if errorId > 0:
        global issues
        if errorId in issues:
            newmsg = long_substring(msg, issues[errorId][0])
            newcount = issues[errorId][1] + 1
        else:
            newmsg = msg
            newcount = 1
        issues[errorId] = (newmsg, newcount, " not reported individually" if summarize_only else "")

# Sends a progress message to the GUI, and to stdout.
def reportProgress(msg):
    reportToGui('<<ScriptProgress>>', msg)
    write(msg, sys.stdout)
    if listener:
        listener.progress(msg)

# Sends a status message to the GUI, and to stdout.
def reportStatus(msg):
    reportToGui('<<ScriptMessage>>', msg)
    write(msg, sys.stdout)
    sys.stdout.flush()

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

# Write summary of issues to issuesFile
def reportIssues():
    global issues
    total = 0
    issuesfile = openIssuesFile()
    issuesfile.write("\nSUMMARY:\n")
    for issue in sorted(issues.items(), key=lambda kv: kv[1][1], reverse=True):
        total += issue[1][1]
        if issue[1][1] == 1:
            issuesfile.write(f"{issue[1][0]}:  1 occurrence.\n")
        else:
            issuesfile.write(f"{issue[1][0]}...:  {issue[1][1]} occurrences{issue[1][2]}.\n")
    issuesfile.write(f"\n{total} issues reported.\n")

# Handles the next token in the source text.
# Only cares about storing text, as of the date of this comment (Apr-2024)
def scan(token: usfmReader.Token):
    if token.type == 'text':
        state.addSourceText(token.value)
    elif token.type == 'v':
        state.addVerse(token.value)
    elif token.type == 'c':
        state.addChapter(token.value)
    elif token.type == 'id':
        state.addID(token.value[0:3].upper())
    elif token.isFootnote():
        state.addSourceFootnote(token.value)

# Parses the source text into a Python data structure.
def scanSourceFile(path):
    state.initBook()
    with io.open(path, "tr", encoding="utf-8-sig") as input:
        contents = input.read(-1)
    if "lemma=" in contents or "x-occurrences" in contents:
        contents = usfm_utils.unalign_usfm(contents)
    tokens = usfmReader.parseString(contents)
    for token in tokens:
        scan(token)
    state.booklength_src = len(contents) if len(contents) > 0 else 1
    global lengths_src
    lengths_src[state.ID] = state.booklength_src
    lengths_src[' All'] += state.booklength_src

# Returns the language code, resource identifier and version as a string.
def identifySource(sourcedir):
    from manifestyaml import ManifestYaml
    my = ManifestYaml()
    my.load(sourcedir)
    id = my.getLanguageId() + "_" + my.getResourceId() + " " + my.getVersion()
    return id

# Loads the source text for the current book if compare_dir is set.
# It parses a usfm file and stores verse text in a dict.
def load_source(fname):
    global footnotedVerses
    config = ToolsConfigManager()
    sourcedir = config.get('VerseLength', 'compare_dir')
    if sourcedir:
        state.source_id = identifySource(sourcedir)

        # Load footnote references first, for the whole directory
        global footnotedVerses_en_ulb
        if len(footnotedVerses) == 0 and len(footnotedVerses_en_ulb) == 0:
            if not footnotes.preScanned(sourcedir):
                reportStatus(f"Scanning source text for footnotes...")
            footnotedVerses = footnotes.getFootnotedVerses(sourcedir)
            if len(footnotedVerses) == 0:
                footnotedVerses_en_ulb = set(footnotes.footnotedVerses_en_ulb)

        # Then parse the usfm for the current book.
        sourcepath = os.path.join(sourcedir, fname)
        if os.path.isfile(sourcepath):
            reportStatus(f"Loading source text...")
            scanSourceFile(sourcepath)

refkey_re = re.compile(r'(\w+) (\d+):(\d+)')
# Returns sort key for the specified item.
def referencekey(sref):
    if ref := refkey_re.match(sref):
        chap = int(ref.group(2))
        verse = int(ref.group(3))
        schap = format(chap, "03d")
        sverse = format(verse, "03d")
        sref = f"{ref.group(1)} {schap}:{sverse}"
    return sref

# Writes the verse lengths data to a file.
def dumpLengths():
    global lengths_src
    global lengths
    books = state.IDs
    path = None
    config = ToolsConfigManager()
    workdir = config.get('VerseLength', 'work_dir')
    sourcedir = config.get('VerseLength', 'compare_dir')
    # sourcelength = len(state.sourcetext[state.reference])

    if len(books) == 1:
        path = os.path.join(workdir, f"verselengths-{books[0]}.tsv")
    elif len(books) > 1:
        path = os.path.join(workdir, "verselengths.tsv")
    if path:
        references = list(lengths.keys() | lengths_src.keys())

        with io.open(path, "tw", encoding='utf-8', newline = '\n') as file:
            file.write(f"Reference\tSource\tTarget\tRatio\n")
            file.write(f"\t{sourcedir}\t{workdir}\t\n")
            for ref in sorted(references, key=referencekey):
                srclength = lengths_src[ref] if ref in lengths_src else 1
                targetlength = lengths[ref] if ref in lengths else 0
                ratio = targetlength / srclength
                file.write(f"{ref}\t{srclength}\t{targetlength}\t{ratio}\n")

psalmv1_re = re.compile(r'PSA \d+:1$')

# Returns (length of verse) / (expected length)
# Based on (1) length of verse in source text, and (2) overall book length.
# Returns 1.0 for the first verse of every Psalm.
# Returns 1.0 if the verse isn't in the source text.
# Returns (length of verse) / 100 if the verse is less than 12 characters and is not in the list of known short verses.
def relative_length(ref):
    rlen = 1.0
    sourcelength = len(state.sourcetext[state.reference]) if state.reference in state.sourcetext else 1
    txln_len = state.getTextLength()
    if not psalmv1_re.match(ref):
        if sourcelength > 1:
            rlen = txln_len / (sourcelength * (state.booklength / state.booklength_src))
        elif txln_len < 12 and not usfm_verses.isShortVerse(state.reference):
            rlen = txln_len / 100.0
    return rlen

# Compares current verse to the source text
# Returns Jaccard Similarity value, and number of words of length > 2 in common.
def similarToSource():
    similarity = 0
    n = 0
    if state.sourcetext and state.reference in state.sourcetext:
        A = set(state.sourcetext[state.reference].split())
        if state.reference in state.sourcefootnote:
            A.update(state.sourcefootnote[state.reference].split())
        B = set(state.versetext.split())
        wordsincommon = [w for w in A&B if len(w) > 2 and w.islower()]
        n = len(wordsincommon)
        similarity = n / len(A|B)
    return (similarity, n)

# Reportverse fragment or all ASCII text, in previous verse
def previousVerseCheck():
    if state.verse != 0:
        if state.getTextLength() > 0:
            rel = relative_length(state.reference)
            if rel < 0.4:
                msg = f"Translation is very short compared to {state.source_id} source: {state.reference}"
                if usfm_verses.isOptional(state.reference):
                    msg += ", but the verse is optional."
                reportError(msg, 2)
            # elif rel > 3.2:     # not safe, at least until chunks and verse bridges are supported
            #     reportError(f"Translation is long compared to {state.source_id} source: {state.reference}.", 2.5)
    (sim, n) = similarToSource()
    if sim > 0.4:
        reportError(f"Verse may be untranslated (based on words in common with source text): {state.reference}", 3.5)

# Verifies correct number of verses for the current chapter.
# This method is called just before the next chapter begins.
def verifyVerseCount():
    if state.chapter > 0 and state.verse != nVerses_niv(state.ID, state.chapter):
        # Acts may have 40 or 41 verses, normally 41.
        # 2 Cor. may have 13 or 14 verses, normally 14.
        # 3 John may have 14 or 15 verses, normally 14.
        # Revelation 12 may have 17 or 18 verses, normally 17.
        n = state.nVerses_source()
        if n == 0 and state.reference not in {'REV 12:18', '3JN 1:15', '2CO 13:13', 'ACT 19:40'}:
            reportError(f"Chapter usually has {nVerses_niv(state.ID, state.chapter)} verses: {state.reference}", 8)
        elif n > 0 and state.verse != n:
            reportError(f"Chapter has {n} verses in the {state.source_id} text: {state.reference}", 8.1)

# Checks whether the entire file was empty or unreadable
def verifyNotEmpty(filename):
    if not state.ID or (state.chapter == 0 and state.verse == 0):
        if not state.ID in {'FRT','BAK'}:
            reportError("File may be empty, or open in another program: " + str(filename), 11)

def verifyChapterCount():
    nExpected = nChapters(state.ID)
    if nExpected > 0 and state.ID and state.chapter != nExpected:
        reportError("There should be " + str(nExpected) + " chapters in " + state.ID + " but " + str(state.chapter) + " chapters are found.", 12)

# \b is used to indicate additional white space between paragraphs.
# No text or verse marker should follow this marker
# and it should not be used before or after titles to indicate white space.
def takeB():
    state.addB()

# Processes a chapter tag
def takeC(c):
    if c != "1":
        # Report missing text in previous verse
        previousVerseCheck()
    if not c.isnumeric():
        reportError("Missing or invalid chapter number after " + state.reference, 13.1)
    else:
        state.addChapter(c)
        if state.chapter < 1 or state.chapter > nChapters(state.ID):
            reportError(f"Invalid chapter number ({c}) is found after {state.lastRef}", 13)
        if state.chapter < state.lastChapter:
            reportError("Chapter out of order: " + state.reference, 14)
        elif state.chapter == state.lastChapter:
            reportError("Duplicate chapter: " + state.reference, 15)
        elif state.chapter > state.lastChapter + 2:
            reportError("Missing chapters before: " + state.reference, 16)
        elif state.chapter > state.lastChapter + 1:
            reportError("Missing chapter(s) between: " + state.lastRef + " and " + state.reference, 17)

# xyz_re = re.compile(r'(\d+\s+)([^\d]+?)(\s+\d+)')
# yz_re = re.compile(r'(.+?)(\s+\d+)')
# xy_re = re.compile(r'(\d+\s+)(.+)')

# Handles all the footnote and endnote token types
def takeFootnote(token: usfmReader.Token):
    if token.type in {'f','rq'}:
        if state.footnote_starts != state.footnote_ends:
            reportError(f"Footnote starts before previous one is terminated at {state.reference}", 18)
        state.addFootnoteStart()
    elif token.type == 'fe':
        if state.endnote_starts != state.endnote_ends:
            reportError(f"Endnote starts before previous one is terminated at {state.reference}", 19)
        state.addEndnoteStart()
    elif token.type in {'f*','rq*'}:
        state.addFootnoteEnd()
    elif token.type == 'fe*':
        state.addEndnoteEnd()
    if token.value: # Prevent a problem with trying to take text where there is none
        takeText(token.value, footnote=True)

def takeID(id):
    if len(id) < 3:
        reportError("Invalid ID: " + id, 22)
    id = id[0:3].upper()
    if id in state.IDs:
        reportError("Duplicate ID: " + id, 23)
    state.addID(id)

def takeP(type):
    if type in {'nb'}:
        state.addUncountedParagraph()
    else:
        state.addParagraph()

def takeQ(type, value):
    state.addPoetry(value)

def takeS5():
    state.addS5()

def takeSection(tag):
    state.addSection(tag)

def takeTitle(token: usfmReader.Token):
    if token.type == 'toc3':
        state.addToc3(token.value)
    else:
        state.addTitle(token.value)

vv_re = re.compile(r'([0-9]+)-([0-9]+)')
vinvalid_re = re.compile(r'[^\d\-]')

# Receives a string containing a verse number or range of verse numbers.
# Reports missing text in previous verse.
# Reports errors related to the verse number(s), such as missing or duplicated verses.
def takeV(vstr):
    if vstr != "1" and vstr[0:2] != "1-":
        previousVerseCheck()   # Checks previous verse
    vlist = []
    if vstr.find('-') > 0:
        vv_range = vv_re.search(vstr)
        if vv_range:
            vnStart = int(vv_range.group(1))
            vnEnd = int(vv_range.group(2))
            for vn in range(vnStart, vnEnd + 1):
                vlist.append(vn)
        else:
            reportError("Problem in verse range near " + state.reference, 34)
    elif not vstr:
        reportError("Unnumbered verse after " + state.reference, 35)
    else:
        vlist.append(int(vstr))

    for vn in vlist:
        # v = str(vn)
        state.addVerse(str(vn))
        if state.chapter == 0:
            reportError("Missing chapter tag: " + state.reference, 36)
        if state.needQQ:
            state.resetPoetry()
        if state.verse < state.lastVerse and state.addError(state.lastRef):
            reportError("Verse out of order: " + state.reference + " after " + state.lastRef, 39)
            state.addError(state.reference)
        elif state.verse == state.lastVerse:
            reportError("Duplicated verse number: " + state.reference, 40)
        elif state.verse == state.lastVerse + 2 and not usfm_verses.isOptional(state.reference, True):
            if state.addError(state.lastRef):
                reportError("Missing verse between: " + state.lastRef + " and " + state.reference, 41)
        elif state.verse > state.lastVerse + 2 and state.addError(state.lastRef):
            reportError("Missing verses between: " + state.lastRef + " and " + state.reference, 41.1)

reference_re = re.compile(r'[\d]+[\s]*:[\s]*[\d]+', re.UNICODE)
bracketed_re = re.compile(r'\[ *([^\]]+) *\]', re.UNICODE)
parenNumber_re = re.compile(r'\([\d, ]{0,11}\)')
parenAmen_re = re.compile(r'\( *[AE]m[ei]+n[aei\. ]*\)')

# Returns None if nothing looking like a footnote occurs in the specified verse text.
# In a verse that often has footnotes, even the presence of parens is flagged.
# Returns the flag character or string that starts the possible footnote.
def findFootnote(text, reference):
    global footnotedVerses
    flag = None
    if ref := reference_re.search(text):
        flag = ref.group(0)
    elif ('(' in text or ')' in text) and (usfm_verses.isOptional(reference) or\
          reference in footnotedVerses or reference in footnotedVerses_en_ulb):
        # Don't suspect numbers in parens as being a footnote
        matches1 = parenNumber_re.findall(text)
        matches2 = parenAmen_re.findall(text)
        if text.count('(') > len(matches1) + len(matches2):  # not every paren includes a simple number
            flag = '('
    elif "[" in text:
        fn = bracketed_re.search(text)
        if not fn or ' ' in fn.group(1):    # orphan [, or more than one word between brackets
            flag = '['
    return flag

# Returns True if the text contains a single, matching pair of brackets, with
# at least a verse reference in between.
def validBracketedFootnote(text):
    valid = False
    fn = bracketed_re.search(text)
    if fn and reference_re.search(fn.group(0)):
        valid = True
    return valid

# Looks for possible verse references and footnotes in the text.
# This function is only called when parsing a piece of verse text.
def reportFootnotes(text):
    global footnotedVerses
    reference = state.reference
    if trigger := findFootnote(text, reference):
        if ':' in trigger:
            if not validBracketedFootnote(text):
                reportError(f"Probable chapter:verse reference ({trigger}) at {reference} belongs in a footnote", 43)
        if reference in footnotedVerses:
            reportError(f"Bracket or parens in {reference} ({state.source_id} has a footnote there)", 43.1)
        elif usfm_verses.isOptional(reference):
            reportError(f"Bracket or parens in {reference} may indicate optional or alternative text", 43.2)
        elif reference in footnotedVerses_en_ulb:
            reportError(f"Bracket or parens in {reference} (footnotes are common there)", 43.3)
        else:
            reportError(f"Optional text or untagged footnote at {reference}", 43.4)

badmarker_re = re.compile(r'\\\w+')

# Performs checks on some text, at most a verse in length.
def takeText(t, footnote=False):
    if bad := badmarker_re.search(t):
        reportError(f'Unsupported USFM marker ({bad.group(0)}) near {state.reference}', 53)
    if not state.textOkay() and not isTextCarryingToken(state.lastToken):
        reportError("Missing verse marker or extra text near " + state.reference, 54)
        if state.lastToken:
            reportError("  preceding Token was \\" + state.lastToken.type, 0)
        else:
            reportError("  top of file", 0)
    if "Conflict Parsing Error" in t:
        reportError("BTT Writer artifact in " + state.reference, 57)
    if state.lastToken and state.inVerse and not state.inFootnote() and not state.aligned_usfm:
        reportFootnotes(t)
    state.addText(t)

endpunc = ".።,፣:፥;፤!?+-[]{}()<>'\"‹«“‘’”»›`*/"
midpunc_re = re.compile(   r"[\d.።,፣:፥;፤!?+\\\[\]{}()<>\"‹«“‘’”»›*]")
quoteend_re = re.compile(  r"[.።,፣:፥;፤!?+-\\\[\]{}()<>'\"‹«“‘’”»›`*/]'$")    # punct ' EOL
quotebegin_re = re.compile(r"'[.።,፣:፥;፤!?+-\\\[\]{}()<>'\"‹«“‘’”»›`*/]")    # ' punct
notnumberinfootnote_re = re.compile(r'[^\d:\-.,]')

# Returns True if the specified token is followed by a *separate text token
def isTextCarryingToken(token):
    if token:
        result = token.type in {'b','m'} or token.isSpecialText() or \
           token.isFootnote() or token.isCrossRef() or token.isPoetry() or token.isIntro()
            # or token.isD() or token.isSP()    these tokens have their own text attached as a value
    else:
        result = False
    return result

# Returns True if the token value should be checked for Arabic numerals
# def isNumericCandidate(token):
#     return token.type in {'text','cl','cp','ft'} or token.isTitleToken()

def take(token: usfmReader.Token):
    if token.type == 'text':
        takeText(token.value, state.inFootnote())

    if token.type == 'id':
        takeID(token.value)
    elif token.type == 'v':
        takeV(token.value)
    elif token.type == 'c':
        verifyVerseCount()  # for the preceding chapter
        if not state.ID:
            reportError("Missing book ID: " + state.reference + " Cannot check this file.", 62.1)
            state.canContinue = False
            return
        takeC(token.value)
    elif token.type in {'p','pi','pc','nb','m'}:
        takeP(token.type)
        if token.value:     # paragraph markers can be followed by text
            reportError("Unexpected: text returned as part of paragraph token." +  state.reference, 63)
            takeText(token.value)
    elif token.isFootnote():
        takeFootnote(token)
    elif token.type == 's5':
        takeS5()
    elif token.type in {'s','s1','s2','mr','ms','sp'}:
        takeSection(token.type)
    elif token.type == 'qa':
        state.addAcrosticHeading()
    elif token.isPoetry():
        takeQ(token.type, token.value)
    elif token.type == 'b':
        takeB()
    elif token.type == 'ide':
        if token.value != 'UTF-8':
            reportError(f"Unsupported character encoding in {state.reference}: \\ide {token.value}", 64)
    elif token.isTitleToken():
        takeTitle(token)
    elif token.type == 'usfm' and token.value.isnumeric():   # non-standard USFM token used by UnfoldingWord software
        state.setUsfmVersion( int(token.value[0]) )
    state.advance(token)

embeddedquotes_re = re.compile(r"\w'\w")

# Receives the text of an entire book as input.
# Verifies things that are better done as a whole file.
def verifyWholeFile(contents, path):
    if not contents.startswith("\\id "):
        reportError(f"USFM file does not start with book id: {shortname(path)}", 74.1)

    lines = contents.split('\n')
    verifyLineByLine(lines, path)

usfm_re = re.compile(r'\\([a-z][a-z1-5]*\*?)(\s+.*)?')
cvnumber_re = re.compile(r'[1-9][-0-9]*')

# Simplistically parses a single line as usfm.
# Assumes markers occur only at beginning of line, and syntax is always good.
# Returns a single tuple of (marker, payload)
# Either marker or payload may be an empty string.
# This function is duplicated in usfm_cleanup.
def parseLine(line):
    marker = ""
    if usfm := usfm_re.match(line):
        marker = usfm.group(1)
        payload = usfm.group(2).strip() if usfm.group(2) else ""
        if marker in {'c', 'v'}:
            if cvnumber := cvnumber_re.match(payload):
                payload = cvnumber.group(0)
            else:
                marker = ""
    if not marker:
        payload = line
    return (marker, payload)

conflict_re = re.compile(r'<+ HEAD')   # conflict resolution tag

# Reports lines of text that may contain section headings.
# Also determines whether the text is primarily ASCII.
def verifyLineByLine(lines, path):
    localstate = State()
    nAscii = 0
    for line in lines:
        if not line.strip():
            continue
        marker, payload = parseLine(line)
        match marker:
            case 'id':
                localstate.addID(payload[0:3].upper())
            case 'c':
                localstate.addChapter(payload)
            case 'v':
                vs = payload.split('-')
                localstate.addVerse(vs[-1])
        if conflict_re.search(line):
            reportError(f"Unresolved translation conflict near {localstate.reference}", 76.2)
        elif marker not in {'id','c'}:
            if line.isascii():
                nAscii += 1

    global primarily_ascii
    primarily_ascii = (nAscii / len(lines) > 0.05)
    global nFiles
    nFiles += 1

usfmname_re = re.compile(r'([0-9AB][0-9])-(\w\w\w)\.')
# Returns True if the specified fname is a peripheral usfm (back matter, etc.)
def peripheral(fname):
    periph = False
    if usfmname := usfmname_re.match(fname):
        periph = (nChapters(usfmname.group(2).upper()) < 1)
    return periph

wjwj_re = re.compile(r' \\wj +\\wj\*', flags=re.UNICODE)

def verifyFile(path):
    with io.open(path, "tr", encoding="utf-8-sig") as input:
        try:
            contents = input.read(-1)
        except UnicodeDecodeError as e:
            reportError("File appears to not be UTF-8: " + shortname(path), 79.2 )
            reportError(str(e))   # 0x92 is Windows encoding for right single quote mark; 0x92 is invalid in UTF-8.
            return

    if wjwj_re.search(contents):
        reportError("Empty \\wj \\wj* pair(s) in " + shortname(path), 77)
    if '\x00' in contents:
        reportError("Null bytes found in " + shortname(path), 79)
        if contents.count('\x00') == len(contents):
            reportError("File is entirely null bytes: " + shortname(path), 79.1)
            return

    state.setAlignedUsfm("lemma=" in contents or "x-occurrences" in contents)
    if state.aligned_usfm:
        contents = usfm_utils.unalign_usfm(contents)
    state.booklength = len(contents) if len(contents) > 0 else 1

    state.canContinue = True

    if len(contents) < 100:
        reportError("Incomplete file: " + shortname(path), 80)
    elif peripheral(os.path.basename(path)):
        reportError(f"Peripheral file not checked: {shortname(path)}", 80.1)
    else:
        state.scanning = True
        load_source(os.path.basename(path))
        reportProgress(f"Checking {shortname(path)}...")
        sys.stdout.flush()
        state.scanning = False
        verifyWholeFile(contents, shortname(path))
        tokens = usfmReader.parseString(contents)
        for token in tokens:
            take(token)
            if not state.canContinue:
                state.addID("")
                sys.stderr.flush()
                return
        previousVerseCheck()       # checks last verse in the file
        verifyNotEmpty(path)
        verifyVerseCount()      # for the last chapter
        verifyChapterCount()
        global lengths
        lengths[state.ID] = state.booklength
        lengths[' All'] += state.booklength
        state.addID("")
        sys.stderr.flush()

# Verifies all .usfm files under the specified folder.
def verifyDir(workdir):
    dirpath = Path(workdir)
    for path in dirpath.iterdir():
        if path.name[0] != '.':         # ignore hidden files
            if path.is_dir():
                # It's a directory, recurse into it
                verifyDir(path)
            elif path.is_file() and path.name[-3:].lower() == 'sfm':
                verifyFile(path)

# Called once each time this script runs.
def initializeGlobals():
    global nFiles
    nFiles = 0
    global state
    state = State()
    global issues
    issues = dict()
    global footnotedVerses
    footnotedVerses.clear()
    global lengths_src
    lengths_src[' All'] = 1
    global lengths
    lengths[' All'] = 1

# Serializes issues list, word list.
def saveResults():
    dumpLengths()
    global issuesFile
    if issuesFile:
        reportIssues()
        issuesFile.close()
        issuesFile = None
    else:
        reportStatus("No issues to report.")

def main(app=None):
    global gui
    gui = app
    initializeGlobals()
    config = ToolsConfigManager()
    workdir = config.get('VerseLength', 'work_dir')
    file = config.get('VerseLength', 'filename')
    if file:
        path = os.path.join(workdir, file)
        if os.path.isfile(path):
            verifyFile(path)
        else:
            reportError(f"No such file: {path}")
    else:
        verifyDir(workdir)
    saveResults()
    reportStatus("\nDone.")
    if gui:
        gui.event_generate('<<ScriptEnd>>', when="tail")

if __name__ == "__main__":
    main()
