# -*- coding: utf-8 -*-
# Script for verifying proper USFM.
# Reports errors to the GUI, stderr, and issues.txt.
# Uses these config values, set via ConfigManager:
#   source_dir - location of files to be checked.
#       This is an unfortunate name, because source_dir contains the translated text, not the source text.
#   compare_dir - location of files containing the source text,
#       against which the translated text may be compared.
#   filename  (optional, checks all files if omitted)
#   standard_chapter_title (optional)
#   suppress[1]  - (removed: Suppress all warnings about numbers. (possible verse number in verse, space in number, number prefix/suffix, etc.))
#   suppress[2]  - (removed: Suppress warnings about missing paragraph marker before verse 1.)
#   suppress[3]  - Suppress most warnings about punctuation
#   suppress[4]  - Suppress warnings about invalid placement of paragraph/poetry markers
#   suppress[5]  - (removed: Suppress checks for verse counts)
#   suppress[6]  - Suppress warnings about straight double and single quotes
#   suppress[7]  - Suppress warnings about straight single quotes  (report straight double quotes only)
#   suppress[8]  - Suppress warnings about UPPER CASE BOOK TITLES
#   suppress[9]  - Suppress warnings about ASCII content
#   suppress[10] - Suppress "First word not capitalized" warnings; report totals only
#   suppress[11] - Suppress "Punctuation missing at end of paragraph" warnings; report totals only'
#   suppress[12] - Suppress warnings about Mixed-case words.
# Detects whether files are aligned USFM.

config = {}
suppress = [False]*13
std_titles = []
gui = None
listener = None # Reuben sets this externally
issuesFile = None
issues: dict = {}   # Can't put in State because we want to accumulate issues across all files.
wordlist = dict()
footnotedVerses = {}
footnotedVerses_en_ulb = {}
nFiles = 0  # number of .usfm files verified
nSectionHeadings = 0
nNoPAfterC = 0

from configmanager import ToolsConfigManager
import os
from pathlib import Path
import sys
import usfmReader
import io
import footnotes
import usfm_verses
import re
from projectinfo import SaidWords
import usfm_utils
import sentences
import section_titles
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
        self.asciiVerse = True
        self.textOkayHere = False
        self.sentenceEnd = True
        self.quotedSentenceEnd = False
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
        self.nSectionHeadings = 0

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
        self.versetext = ""
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
        self.sentenceEnd = True
        self.prevItemCategory = self.currItemCategory
        self.currItemCategory = PP

    def addPoetry(self, value):
        self.nPoetry += 1
        self.needQQ = False
        self.needPP = False
        self.textOkayHere = True
        self.prevItemCategory = self.currItemCategory
        if value:
            self.needVerseText = False
        self.currItemCategory = OTHER if value else QQ

    def addSection(self, tag):
        self.prevItemCategory = self.currItemCategory
        self.currItemCategory = S
        self.inVerse = False
        if tag != 's5':
            global nSectionHeadings
            nSectionHeadings += 1
            self.nSectionHeadings += 1

    # Records the start of a new chunk
    def addS5(self):
        self.startChunkVerse = self.verse + 1
        self.startChunkRef = self.ID + " " + str(self.chapter) + ":" + str(self.startChunkVerse)

    # Returns False if there is a unwanted repetition of tokens.
    def okMarker(self, token):
        cat = category(token)
        okay = (cat == OTHER or cat != self.currItemCategory)
        # self.prevMarker = self.currMarker
        # self.currMarker = token.type
        return okay

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
        self.asciiVerse = True   # until proven False
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

    def needCaps(self):
        return self.sentenceEnd and not self.quotedSentenceEnd

    def sentenceEnded(self):
        return self.sentenceEnd

    def getTextLength(self):
        return len(self.versetext)

    def addText(self, text):
        self.prevItemCategory = self.currItemCategory
        self.currItemCategory = OTHER
        self.needVerseText = False
        if text and text not in '-+':
            self.versetext += text + " "
        self.textOkayHere = True
        if not text.isascii():
          self.asciiVerse = False

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

    # Specifies whether the current piece of text ends a sentence.
    def endSentence(self, end):
        self.sentenceEnd = end
    def endQuotedSentence(self, end):
        self.sentenceEnd = end
        self.quotedSentenceEnd = end

    def reportedUpperCase(self):
        self.upperCaseReported = True

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
    workdir = Path(config['source_dir'])
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

# If issues.txt file is not already open, opens it for writing.
# First saves existing issues.txt file to another name.
# Returns file pointer.
def openIssuesFile():
    global issuesFile
    if not issuesFile:
        config = ToolsConfigManager()
        workdir = config.get('VerifyUSFM', 'source_dir')
        path = os.path.join(workdir, "issues.txt")
        if os.path.exists(path):
            timestamp = get_timestamp(path)
            bakpath = os.path.join(workdir, f"issues-{timestamp}.txt")
            if not os.path.exists(bakpath):
                os.rename(path, bakpath)
        issuesFile = io.open(path, "tw", encoding='utf-8', newline='\n')
        issuesFile.write(f"Issues detected by verifyUSFM version {config.get('UsfmWizard', 'version')}, {date.today()}, {workdir}\n")
        if compare_dir := config.get('VerifyUSFM', 'compare_dir'):
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

def reportSuppressedIssues():
    any = False
    for val in suppress[1:9]:
        if val:
            any = True
    for val in suppress[10:]:
        if val:
            any = True
    if any:
        issuesfile = openIssuesFile()
        issuesfile.write(f"But these kinds of warnings were suppressed:\n")
        # if suppress[1]:
        #     issuesfile.write(f"    Irregular numbers.\n")
        if suppress[3]:
            issuesfile.write(f"    Punctuation.\n")
        if suppress[11]:
            issuesfile.write(f"    Paragraph-final punctuation. (Only the total counts were reported.)\n")
        # if suppress[2]:
        #     issuesfile.write(f"    Missing paragraph marker after chapter marker.\n")
        if suppress[4]:
            issuesfile.write(f"    Invalid placement of paragraph/poetry markers.\n")
        # if suppress[5]:
        #     issuesfile.write(f"    Unexpected verse counts per chapter.\n")
        if suppress[6]:
            issuesfile.write(f"    Straight quotes.\n")
        elif suppress[7]:
            issuesfile.write(f"    Straight single quotes.\n")
        if suppress[8]:
            issuesfile.write(f"    Upper case book titles.\n")
        if suppress[10]:
            issuesfile.write(f"    Capitalization. (Only the total counts were reported.)\n")
        if suppress[12]:
            issuesfile.write(f"    Mixed case words.\n")

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
    reportSuppressedIssues()

# Writes the word list to a file.
def dumpWords():
    books = state.IDs
    hapaxcount = 0
    oldpath = path = None
    if len(books) > 1:
        path = os.path.join(config['source_dir'], "wordlist.tsv")
        oldpath = os.path.join(config['source_dir'], "wordlist.txt")
    if path:
        with io.open(path, "tw", encoding='utf-8', newline = '\n') as file:
            file.write(f"Word\tOccurrences\tReference\n")
            for entry in sorted(wordlist.items(), key=wordkey):
                line = f"{entry[0]:20}\t{entry[1][0]}"
                if entry[1][0] == 1:
                    line = line + "\t" + entry[1][1]
                    hapaxcount += 1
                file.write(line + '\n')
        if oldpath and os.path.isfile(oldpath):
            os.remove(oldpath)
    if hapaxcount > 0 and not config['filename']:
        percent = int(hapaxcount * 100 / len(wordlist))
        reportError(f"{len(wordlist)} unique words. {hapaxcount} ({percent}%) of them occur only once.", 0.2)

punct_table = str.maketrans('', '', "'’\"-_()–&")

# Returns True if s is a mixed case word.
def isMixed(word):
    global trans
    mixed = False
    if len(word) > 1 and not (word.islower() or word.istitle() or word.isupper()):
        w2 = word.translate(punct_table)
        if len(w2) > 1 and not (w2.islower() or w2.istitle() or w2.isupper()):
            mixed = True
    return mixed

# Scans the word list for mixed case words.
def reportMixedCase():
    mcwords = []
    limit = 20
    nSingleMixed = 0
    for entry in wordlist.items():
        if len(mcwords) > limit:
            break
        if entry[1][0] == 1:
            if isMixed(entry[0]):
                nSingleMixed += 1
                reportError(f"Mixed case word in {entry[1][1]}: {entry[0]}", 0.4)
        elif entry[1][0] < 5:
            if isMixed(entry[0]):
                mcwords.append(entry[0])
    if len(mcwords) > 0:
        start = "Other mixed" if nSingleMixed > 0 else "Mixed"
        reportError(f"{start} case words occur more than once each: {mcwords[0:limit]}", 0.5)
        if len(mcwords) >= limit:
            reportError("Too many mixed case words; reporting cancelled", 0.6)

def reportSections():
    if nFiles > 2 and nSectionHeadings > 0:
        if nSectionHeadings < (6 if nFiles > 5 else 4):
            reportError(f"Possible error: sparse section headings (only {nSectionHeadings}).", 0.7)

# Returns sort key for the specified item.
def wordkey(item):
    word = item[0].lstrip("'")
    return str.lower(word)

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
    sourcedir = config['compare_dir']
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

psalmv1_re = re.compile(r'PSA \d+:1(-|$)')

# Returns (length of verse) / (expected length)
# Based on (1) length of verse in source text, and (2) overall book length.
# Returns 1.0 for the first verse of every Psalm.
# Returns 1.0 if the verse isn't in the source text.
# Returns (length of verse) / 100 if the verse is less than 12 characters and is not in the list of known short verses.
def relative_length(ref):
    rlen = 1.0
    if not psalmv1_re.match(ref):
        sourcelength = len(state.sourcetext[state.reference]) if state.reference in state.sourcetext else 1
        txln_len = state.getTextLength()
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

# Report empty verse, verse fragment or all ASCII text, in previous verse
def previousVerseCheck():
    empty = False
    if not usfm_verses.isOptional(state.reference) and state.verse != 0:
        if state.getTextLength() == 0:
            reportError("Empty verse: " + state.reference, 1)
            empty = True
        else:
            rel = relative_length(state.reference)
            if rel < 0.4:
                reportError(f"Translation is very short compared to {state.source_id} source: {state.reference}", 2)
            # elif rel > 3.2:     # not safe, at least until chunks and verse bridges are supported
            #     reportError(f"Translation is long compared to {state.source_id} source: {state.reference}.", 2.5)
    if not suppress[9] and state.asciiVerse and not empty:
        reportError("Verse is entirely ASCII: " + state.reference, 3)
    (sim, n) = similarToSource()
    if sim > 0.4:
        reportError(f"Verse may be untranslated (based on words in common with source text): {state.reference}", 3.5)

# def longChunkCheck():
#     max_chunk_length = 400  # set lower if this is ever needed again
#     if not state.aligned_usfm and state.verse - (max_chunk_length-1) > state.startChunkVerse:
#         reportError("Long chunk: " + state.startChunkRef + "-" + str(state.verse) + "   (" + str(state.verse-state.startChunkVerse+1) + " verses)", 4)

# Verifies that at least one book title is specified, other than the English book title.
# This method is called just before chapter 1 begins, so there has been every
# opportunity for the book title to be specified.
def verifyBookTitle():
    title_ok = False
    en_name = bookTitleEnglish(state.ID)
    for title in state.booktitles:
        if title and title != en_name:
            title_ok = True
    if not title_ok:
        reportError("Book title matches English: " + en_name, 5)

# Reports inconsistent chapter titling
def verifyChapterTitles():
    global std_titles
    if len(state.chaptertitles) > 1 and len(state.chaptertitles) != len(std_titles):
        reportError(f"Inconsistent chapter titling: {state.chaptertitles} in {state.ID}", 6)
    if state.nChapterLabels > 1 and state.nChapterLabels < state.chapter:
        reportError(f"Some chapters do not have chapter labels but {state.nChapterLabels} do.", 7)

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

def verifyFootnotes():
    if state.footnote_starts != state.footnote_ends:
        reportError("Mismatched footnote tags (" + str(state.footnote_starts) + " started and " + str(state.footnote_ends) + " ended) in " + state.ID, 9)
    if state.endnote_starts != state.endnote_ends:
        reportError("Mismatched endnote tags (" + str(state.endnote_starts) + " started and " + str(state.endnote_ends) + " ended) in " + state.ID, 10)

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
        # longChunkCheck()
    # if state.currItemCategory == S:
    #     reportError(f"Chapter ends with a section heading: {state.reference}", 13.2)
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

xyz_re = re.compile(r'(\d+\s+)([^\d]+?)(\s+\d+)')
yz_re = re.compile(r'(.+?)(\s+\d+)')
xy_re = re.compile(r'(\d+\s+)(.+)')

# Extracts the word for "Chapter" or other chapter label in the string.
#
def parseChapterLabel(value, nchapter):
    value = value.strip()
    name = value
    if xyz := xyz_re.match(value):
        if decimal_value(xyz.group(3)) == nchapter:
            name = xyz.group(1) + xyz.group(2)
        elif decimal_value(xyz.group(1)) == nchapter:
            name = xyz.group(2) + xyz.group(3)
    elif yz := yz_re.match(value):
        if decimal_value(yz.group(2)) == nchapter:
            name = yz.group(1)
    elif xy := xy_re.match(value):
        if decimal_value(xy.group(1)) == nchapter:
            name = xy.group(2)
    return name

# Processes a chapter label
def takeCL(value):
    global std_titles
    # Report missing text in previous verse
    name = parseChapterLabel(value, state.chapter)
    state.addChapterLabel(name)
    if len(std_titles) > 0 and name not in std_titles:
        reportError(f"Non-standard chapter label at {state.reference}: {value}", 42)

def takeD():
    if not suppress[4]:
        reportSectionPrecedentErrors('d')
    reportParagraphMarkerErrors('d')
    state.addUncountedParagraph()

# Handles all the footnote and endnote token types
def takeFootnote(token: usfmReader.Token):
    if token.type in {'f','rq'}:
        if state.footnote_starts != state.footnote_ends:
            reportError(f"Footnote starts before previous one is terminated at {state.reference}", 18)
        state.addFootnoteStart()
    elif token.type == 'fe':
        if state.endnote_starts != state.endnote_ends:
            reportError(f"Endnote starts before previous one is terminated at {state.reference}", 19)
        reportError(f"Warning: endnote \\fe ... \\fe* at {state.reference} may break USFM Converter and Scripture App Builder.", 20)
        state.addEndnoteStart()
    elif token.type in {'f*','rq*'}:
        state.addFootnoteEnd()
    elif token.type == 'fe*':
        state.addEndnoteEnd()
    else:
        if not state.inFootnote():
            reportError(f"Footnote marker ({token.type}) not between \\f ... \\f* pair at {state.reference}", 21)
    if token.value: # Prevent a problem with trying to take text where there is none
        takeText(token.value, footnote=True)

def takeID(id):
    if len(id) < 3:
        reportError("Invalid ID: " + id, 22)
    id = id[0:3].upper()
    if id in state.IDs:
        reportError("Duplicate ID: " + id, 23)
    state.addID(id)

def reportParagraphMarkerErrors(type):
    if state.currItemCategory in {QQ,PP} and not suppress[4]:
        reportError("Warning: back to back paragraph/poetry markers near: " + state.reference, 24)
    if type == 'p' and state.needText() and not usfm_verses.isOptional(state.reference):
        reportError("Paragraph marker after verse marker, or empty verse: " + state.reference, 25)
    if type == 'nb' and state.currItemCategory != C:
        reportError("\\nb marker should follow chapter marker: " + state.reference, 25.1)

def takeP(type):
    reportParagraphMarkerErrors(type)
    if not state.aligned_usfm and not suppress[3] and not state.sentenceEnded() and type != 'm':
        if state.verse > 0:
            reportError(f"Check paragraph-ending punctuation at: {state.reference}", 26, suppress[11])
        elif state.reference != "ACT 22":
            reportError(f"Punctuation missing at end of chapter before {state.reference}", 26.1, suppress[11])
    if type in {'nb'}:
        state.addUncountedParagraph()
    else:
        state.addParagraph()

def takeQ(type, value):
    reportParagraphMarkerErrors(type)
    state.addPoetry(value)

def takeS5():
    state.addS5()
    if state.currItemCategory == S:
        reportError(f"Back to back section markers after {state.reference}", 29.5)

def reportSectionPrecedentErrors(tag):
    if state.currItemCategory == PP:
        reportError(f"Warning: useless paragraph (p,m,nb) marker before \\{tag} marker at: {state.reference}", 27)
    elif state.currItemCategory == QQ:
        reportError(f"Warning: useless \\q before \\{tag} marker at: {state.reference}", 28)
    elif state.currItemCategory == B:
        reportError(f"\\b may not be used before or after section heading. {state.reference}", 29)

def takeSection(tag):
    if tag != 's5' and not suppress[4]:
        reportSectionPrecedentErrors(tag)
    if state.currItemCategory == S:
        reportError(f"Back to back section markers after {state.reference}", 29.5)
    state.addSection(tag)

def takeTitle(token: usfmReader.Token):
    if token.type == 'toc3':
        state.addToc3(token.value)
    else:
        state.addTitle(token.value)
    if token.type in {'mt','mt1'} and token.value.isascii() and not suppress[9]:
        reportError("mt token has ASCII value in " + state.reference, 30)
    if token.value.isupper() and not state.upperCaseReported and not suppress[8]:
        reportError("Upper case book title in " + state.reference, 31)
        state.reportedUpperCase()
    if token.value.startswith("Ii"):
        reportError(f"Mixed case roman numerals in \\{token.type} field", 31.1)
    if state.currItemCategory == B:
        reportError("\\b may not be used before or after titles or headings. " + state.reference, 32)

vv_re = re.compile(r'([0-9]+)-([0-9]+)')
vinvalid_re = re.compile(r'[^\d\-]')

# Receives a string containing a verse number or range of verse numbers.
# Reports missing text in previous verse.
# Reports errors related to the verse number(s), such as missing or duplicated verses.
def takeV(vstr):
    if state.currItemCategory == B:
        reportError(f"\\b should be used only between paragraphs. {state.reference}", 33)
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
        if state.verse == 1 and state.needPP:
            global nNoPAfterC
            nNoPAfterC += 1
            if nNoPAfterC < 31:
                reportError("Need paragraph marker before: " + state.reference, 37, (nNoPAfterC > 30))
            elif nNoPAfterC == 31:
                reportError("Reporting of missing \\p after \\c is cancelled; too many occurrences.", 37.1)
        if state.needQQ:
            reportError("Need \\q or \\p after acrostic heading before: " + state.reference, 38)
            state.resetPoetry()
        if state.prevItemCategory == S:
            reportError(f"Section heading should be followed by paragraph marker at {state.reference}", 38.5)
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

# Warns when a paragraph break appears in what seems to be the middle of a sentence.
# Warns when the specified string is supposed to start a sentence but the first word is not capitalized.
# Warns when a sentence later in the string does not start with a capital letter.
def reportCaps(s):
    if state.needCaps():
        word = sentences.firstword(s)
        if word and word[0].islower():
            if state.currItemCategory == PP or state.prevItemCategory == PP:
                reportError(f"First word of paragraph not capitalized near {state.reference}", 44, suppress[10])
            else:
                reportError(f"First word in sentence is not capitalized: \"{word}\" at {state.reference}", 44.1, suppress[10])
    for word in sentences.nextfirstwords(s):
        if word[0].islower():
            reportError(f"First word in sentence is not capitalized: \"{word}\" in {state.reference}", 44.1, suppress[10])

# Returns a string containing text preceding specified start position and following end position
def context(text, start, end):
    start = 0 if start < 0 else 1 + text.rfind(' ', 0, start)
    end = text.find(' ', end, -1)
    return text[start:end] if end > start else text[start:]

#adjacent_re = re.compile(r'([\.\?!;\:,][\.\?!;\:,])', re.UNICODE)
punctuation_re = re.compile(r'([.?!;:,][^\s\u200b\)\]\'"’”»›])', re.UNICODE)   # phrase ending punctuation that doesn't actually end the phrase
# note: \u200b indicates word boundaries in scripts that do not use explicit spacing, but is used (seemingly incorrectly) like a space in Laotian
spacey_re = re.compile(r'[\s\n]([\.\?!;\:,\)’”»›])', re.UNICODE)    # space before phrase-ending mark
# Indonesian TBI version of this expression:
# spacey_re = re.compile(r'[\s\n]([\.\?!;\:,\)’»›])', re.UNICODE)    # space before phrase-ending mark
# Kuku REG version of this expression:
spacey2_re = re.compile(r'[\s][\[\]\(\'"«“‘’”»›][\s]')
spacey3_re = re.compile(r'[\(\'"«“‘’”»›][\s]', re.UNICODE)       # quote-space at beginning of verse
spacey4_re = re.compile(r'[\s][\(\'"«“‘’”»›]$', re.UNICODE)       # quote-space at end of verse
wordmedial_punct_re = re.compile(r'[\w][.?!;:,()\[\]"«“‘”»›][.?!;:,()\[\]\'"«“‘’”»›]*[\w]')
outsidequote_re = re.compile(r'([\'"’”»›][\.!])', re.UNICODE)   # Period or exclamation outside closing quote.
backs_re = re.compile(r'\\(\s|$)')

def reportPunctuation(text):
    if bad := punctuation_re.search(text):
        i = bad.start()
        if text[i:i+3] != '...' or text[i:i+4] == "....":
            chars = bad.group(1)
            if not (chars[0] in ',.' and chars[1] in "0123456789"):   # it's a number
                if not (chars[0] == ":" and chars[1] in "0123456789"):
                    reportError("Check the punctuation at " + state.reference + ": " + chars, 45)
                # elif not state.lastToken or not (state.inFootnote() or state.lastToken.getType().startswith('io') \
                #           or state.lastToken.getType().startswith('ip')):
                #     s = context(text, bad.start()-2, bad.end()+1)
                #     reportError(f"Untagged footnote (probable) at {state.reference}: {s}", 46)
                # 3/17/25: this warning is unnecessary. Was always followed by 'Probable chapter:verse' warning.
    if bad := spacey_re.search(text):
        reportError("Space before phrase ending mark at " + state.reference + ": " + bad.group(1), 48)
    if bad := outsidequote_re.search(text):
        i = bad.start()
        if text[i+1:i+4] != "...":
            reportError(f"Punctuation after quote mark at {state.reference}: {bad.group(1)}", 50)

    if bad := spacey2_re.search(text):
        s = context(text, bad.start()-2, bad.end()+2)
    elif bad := spacey3_re.match(text):
        s = context(text, 0, bad.end()+2)
    elif bad := spacey4_re.search(text):
        s = context(text, bad.start()-2, len(text))
    if bad:
        reportError(f"Free floating mark at {state.reference}: {s}", 49)

    if "''" in text or '""' in text:
        reportError("Repeated quotes at " + state.reference, 51)
    bad = wordmedial_punct_re.search(text)
    if bad and text[bad.end()-1] not in "0123456789":
        s = context(text, bad.start(), bad.end())
        reportError(f"Word medial punctuation in {state.reference}: {s}", 52)
    if '/' in text:
        reportError(f"Forward slash in {state.reference}", 52.1)
    if backs_re.search(text):
        reportError(f"Backslash (\\) near {state.reference}", 52.2)
    if '=' in text:
        reportError(f"Equals sign (=) in {state.reference}", 52.3)

numberembed_re = re.compile(r'[^\s,:\."\d\(\[\-]+[\d]+[^\s,;\."\d\)\]]+')
numberprefix_re = re.compile(r'[^\s,\."\d\(\[]\d+', re.UNICODE)
numbersuffix_re = re.compile(r'\d+[^\s,;:."\-?!"\d\)\]]', re.UNICODE)
unsegmented_re = re.compile(r'[\d][\d][\d][\d]+')
numberformat_re = re.compile(r'[\d]+[.,]?\s[.,]?[\d]+')    # space between digits
leadingzero_re = re.compile(r'[\s]0[0-9,]*', re.UNICODE)
number_re = re.compile(r'[^\d(](\d+)[^\d,]')       # possible verse number in text
chapverse_re = re.compile(r'(\d+)([:\-])(\d+)')

def reportNumbers(t, footnote):
    verseflag = False
    if state.chapter > 0 and not footnote:
        if t.startswith(str(state.verse) + " "):
            reportError("Verse number in text (probable): " + state.reference, 59)
            verseflag = True
        elif v := number_re.search(t):
            while v:
                if v.group(1) == str(state.verse) or v.group(1) == str(state.verse+1):
                    reportError(f"Possible verse number ({v.group(1)}) in text at {state.reference}", 59.1)
                    verseflag = True
                v = number_re.search(t, v.end()-1)
        if not verseflag:
            chapverse = chapverse_re.search(t)
            while chapverse:
                if chapverse.group(2) == ":" or int(chapverse.group(3)) > int(chapverse.group(1)):
                    reportError(f"Likely verse reference ({chapverse.group(0)}) in text at {state.reference}", 59.2)
                    verseflag = True
                chapverse = chapverse_re.search(t, chapverse.end())
    if embed := numberembed_re.search(t):
        reportError(f"Embedded number in word: {embed.group(0)} at {state.reference}", 60)
    elif not verseflag:
        if suffixed := numbersuffix_re.search(t):
            if state.chapter > 0 and not footnote:
                reportError(f"Invalid number suffix: {suffixed.group(0)} at {state.reference}", 60.2)
        if prefixed := numberprefix_re.search(t):
            if (state.chapter > 0 and not footnote) or (prefixed.group(0)[0] not in {':','-'}):
                reportError(f"Invalid number prefix: {prefixed.group(0)} at {state.reference}", 60.1)
    if unsegmented := unsegmented_re.search(t):
        if len(unsegmented.group(0)) > 4:
            reportError(f"Unsegmented number: {unsegmented.group(0)} at {state.reference}", 61)
    if fmt := numberformat_re.search(t):
        reportError(f"Space between digits {fmt.group(0)} at {state.reference}", 61.1)
    elif leadzero := leadingzero_re.search(t):
        reportError(f"Invalid leading zero: {leadzero.group(0)} at {state.reference}", 61.2)

period_re = re.compile(r'[\s]*[\.,;:!\?]')  # detects phrase-ending punctuation standing alone or starting a phrase
badmarker_re = re.compile(r'\\\w+\*?')
conflict_re = re.compile(f'<<<|>>>|===')

# Performs checks on some text, at most a verse in length.
def takeText(t, footnote=False):
    if not conflict_re.match(t):
        if bad := badmarker_re.search(t):
            reportError(f'Unsupported USFM marker ({bad.group(0)}) near {state.reference}', 53)
        if not state.textOkay() and not isTextCarryingToken(state.lastToken):
            reportError("Missing verse marker or extra text near " + state.reference, 54)
            if state.lastToken:
                reportError("  preceding Token was \\" + state.lastToken.type, 0)
            else:
                reportError("  top of file", 0)
        if state.textOkay() and state.verse == 0 and state.chapter > 0:
            reportError(f"Unmarked text before {state.reference + ':1'}", 54.1)
        if ("<" in t) ^ (">" in t) and not conflict_re.search(t) and not ">>>" in t:
            reportError("Unmatched angle bracket at " + state.reference, 56)
        if "Conflict Parsing Error" in t:
            reportError("BTT Writer artifact in " + state.reference, 57)
        if not suppress[3] and not state.aligned_usfm:    # report punctuation issues
            reportPunctuation(t)
        if period := period_re.match(t):    # text starts with a period
            if len(t) <= period.end() + 1:
                reportError(f"Orphaned punctuation at {state.reference}", 58)
            else:
                reportError("Text begins with phrase-ending punctuation in " + state.reference, 58.1)
        if state.lastToken and state.inVerse and not state.inFootnote() and not state.aligned_usfm:
            reportFootnotes(t)
        # if not suppress[1]:
        reportNumbers(t, footnote)
        if not footnote:
            reportCaps(t)
            state.endSentence( sentences.endsSentence(t) )
    addWords(t)
    state.addText(t)

def listwords(t):
    words = []
    for item in t.split():
        if '—' in item:
            words += item.split('—')
        else:
            words.append(item)
    return words

endpunc = ".።,፣:፥;፤!?+-[]{}()<>'\"‹«“‘’”»›`*/"
midpunc_re = re.compile(   r"[\d.።,፣:፥;፤!?+\\\[\]{}()<>\"‹«“‘’”»›*]")
quoteend_re = re.compile(  r"[.።,፣:፥;፤!?+-\\\[\]{}()<>'\"‹«“‘’”»›`*/]'$")    # punct ' EOL
quotebegin_re = re.compile(r"'[.።,፣:፥;፤!?+-\\\[\]{}()<>'\"‹«“‘’”»›`*/]")    # ' punct
notnumberinfootnote_re = re.compile(r'[^\d:\-.,]')

# Parses all the words out of the t string and adds them to the wordlist[].
def addWords(t):
    for item in listwords(t):
        word = item.strip(".።,፣:፥;፤!?+-\\[]{}()<>\"‹«“‘’”»›*/")
        if quoteend_re.search(word):
            word = word.rstrip(endpunc)
        if quotebegin_re.match(word):
            word = word.lstrip(endpunc)
        if word:
            if not state.inFootnote() or notnumberinfootnote_re.search(word):
                if any(c.isalpha() for c in word) and not midpunc_re.search(word):
                    (count, ref) = wordlist.get(word, (0, None))
                    ref = state.reference if count == 0 else ""
                    wordlist[word] = (count+1, ref)

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
    if token.type != 'text':
        if not state.okMarker(token):
            reportError(f"Back to back markers of type {token.type} at {state.reference}", 62)
    else:
        takeText(token.value, state.inFootnote())

    if token.type == 'id':
        takeID(token.value)
    elif token.type == 'v':
        takeV(token.value)
    elif token.type == 'c':
        # if not suppress[5]:
        verifyVerseCount()  # for the preceding chapter
        if not state.ID:
            reportError("Missing book ID: " + state.reference + " Cannot check this file.", 62.1)
            state.canContinue = False
            return
        if token.value == "1":
            verifyBookTitle()
        takeC(token.value)
    elif token.type == 'cl':
        takeCL(token.value)
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
    elif token.type == 'd':
        takeD()
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

    # if config['language_code'] in {"ur"} and isNumericCandidate(token) and re.search(r'[0-9]', token.value):
        # reportError("Arabic numerals in footnote at " + state.reference, 68)

# bad_chapter_re1 = re.compile(r'[^\n](\\c\s*\d+)', re.UNICODE)
bad_chapter_re2 = re.compile(r'(\\c[0-9]+)', re.UNICODE)
# bad_chapter_re3 = re.compile(r'(\\c\s*\d+)[^\d\s]+[\n\r]', re.UNICODE)
# bad_verse_re1 = re.compile(r'([^\n\r\s]\\v\s*\d+)', re.UNICODE)
bad_verse_re2 = re.compile(r'(\\v[0-9]+)', re.UNICODE)
bad_verse_re3 = re.compile(r'(\\v\s*[-0-9]+[^-\d\s])', re.UNICODE)

# Receives the text of an entire book as input.
# Reports bad patterns.
def verifyChapterAndVerseMarkers(text, path):
    for badactor in bad_chapter_re2.finditer(text):
        reportError("Missing space before chapter number: " + badactor.group(0) + " in " + path, 70)
    for badactor in bad_verse_re2.finditer(text):
        reportError("Missing space before verse number: " + badactor.group(0) + " in " + path, 73)
    for badactor in bad_verse_re3.finditer(text):
        s = badactor.group(1)
        reportError("Missing space after verse number: " + s + " in " + path, 74)

def verifyParagraphCounts():
    if state.chapter > 0:
        # if state.nParagraphs / state.chapter <= 2.5 and state.nPoetry / state.chapter <= 10:
        #     reportError(f"Low paragraph count ({state.nParagraphs + state.nPoetry}) for {state.ID}", 73.5)
        if state.nSectionHeadings == 1:
            reportError(f"Possible error: one lone section is marked in {state.ID}", 73.6)

embeddedquotes_re = re.compile(r"\w'\w")

# Receives the text of an entire book as input.
# Verifies things that are better done as a whole file.
def verifyWholeFile(contents, path):
    if not contents.startswith("\\id "):
        reportError(f"USFM file does not start with book id: {shortname(path)}", 74.1)
    verifyChapterAndVerseMarkers(contents, path)

    lines = contents.split('\n')
    verifyLineByLine(lines)

    if not suppress[6]:
        nembedded = len(embeddedquotes_re.findall(contents))
        nsingle = contents.count("'") - nembedded
        ndouble = contents.count('"')
        if ndouble > 0:
            if nsingle == 0 or suppress[7]:
                reportError(f"Straight quotes in {shortname(path)}: {ndouble} doubles.", 75)
            else:
                reportError(f"Straight quotes in {shortname(path)}: {ndouble} doubles, {nsingle} singles not counting {nembedded} word-medial.", 75)
        elif nsingle > 0 and not suppress[7]:
            reportError(f"Straight quotes in {shortname(path)}: {nsingle} singles not counting {nembedded} word-medial.", 75)

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

said_re = re.compile(r'(\w+)[,:] ["«“‘]\w')

# Returns a word in the line that introduces a quotation, or None.
# Only returns the first such word if there are more than one.
def said_word(line):
    word = None
    if line:
        if said := said_re.search(line):
            word = said.group(1)
    return word

fspace_re = re.compile(r' (\\fe?)\s')
def reportFootnoteSpacing(line, reference):
    if fspace := fspace_re.search(line):
        reportError(f"Space before footnote marker {fspace.group(1)} at {reference}", 78)

def reportSectionTitles(line, reference):
    if line[0] != '\\' and section_titles.is_possible_heading(line):
        reportError(f"Possible section title on a line by itself at {reference}", 76)
    elif reference not in section_titles.exclude_eol_checks:
        if section_titles.find_eol_heading(line):
            reportError(f"Possible section title at end of {reference}", 76.1)

conflict_head_re = re.compile(r'<+ HEAD')   # conflict resolution tag
# Performs checks that are best done on a line-by-line basis.
#   Reports lines of text that may contain section headings.
#   Determines whether to check for ASCII content, and sets suppress[9] accordingly.
#   Collects "said" words.
#   Reports problems with unresolved merge conflicts.
#   Reports problems with
def verifyLineByLine(lines):
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
        if conflict_head_re.search(line):
            reportError(f"Unresolved translation conflict near {localstate.reference}", 76.2)
        elif marker not in {'id','c'}:
            if line.isascii():
                nAscii += 1
            if word := said_word(line):
                saidwords.addWord(word)
            reportSectionTitles(line, localstate.reference)
            reportFootnoteSpacing(line, localstate.reference)

    suppress[9] = (nAscii / len(lines) > 0.05)
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
        if (state.usfm_version == 2 or state.aligned_usfm) and not state.toc3:
            reportError("No \\toc3 tag in " + shortname(path), 81)
        previousVerseCheck()       # checks last verse in the file
        verifyNotEmpty(path)
        # if not suppress[5]:
        verifyVerseCount()      # for the last chapter

        verifyChapterCount()
        verifyFootnotes()
        verifyChapterTitles()
        verifyParagraphCounts()
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
    global config
    global suppress
    global wordlist
    global nFiles
    global nSectionHeadings
    global nNoPAfterC

    nFiles = 0
    nSectionHeadings = 0
    nNoPAfterC = 0
    wordlist = dict()
    config = ToolsConfigManager().get_section('VerifyUSFM')
    if config:
        for i in range(1, len(suppress)):
            suppress[i] = config.getboolean('suppress'+str(i), fallback = False)
        global std_titles
        std_titles = [ config.get('standard_chapter_title', fallback = '') ]
        if std_titles == ['']:
            std_titles = []

        global state
        state = State()
        global issues
        issues = dict()
        global footnotedVerses
        footnotedVerses.clear()
        global saidwords
        saidwords = SaidWords(config['source_dir'], config['language_code'])

# Serializes issues list, word list, and saidwords.
def saveResults():
    dumpWords()

    global issuesFile
    if issuesFile:
        reportIssues()
        issuesFile.close()
        issuesFile = None
    else:
        reportStatus("No issues to report.")

    if saidwords:
        global nFiles
        saidwords.save(mincount = 4 if nFiles < 40 else 6)

def main(app=None):
    global gui
    gui = app
    initializeGlobals()
    if config:
        workdir = config['source_dir']
        file = config['filename']
        if file:
            path = os.path.join(workdir, file)
            if os.path.isfile(path):
                verifyFile(path)
            else:
                reportError(f"No such file: {path}")
        else:
            verifyDir(workdir)
        if not suppress[12]:
            reportMixedCase()
        reportSections()
        saveResults()
        reportStatus("\nDone.")
    if gui:
        gui.event_generate('<<ScriptEnd>>', when="tail")

if __name__ == "__main__":
    main()
