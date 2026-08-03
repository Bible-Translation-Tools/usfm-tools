# -*- coding: utf-8 -*-
# This script converts text files from tStudio to USFM Resource Container format.
#    Gets the book ID, contributors, sources, etc from manifest.json files.
#    Generates a manifest.yaml file in the new project folder.
#    Outputs a project information file in the parent folder.
#    Finds and parses title.txt to get the book title.
#    Populates the USFM headers.
#    Standardizes the names of .usfm files. For example 41-MAT.usfm and 42-MRK.usfm.
#    Converts multiple books at once if there are multiple books.

from configmanager import ToolsConfigManager
from projectinfo import ProjectInfo
from pathlib import Path
import sentences
import section_titles
import usfm_verses
import re
import io
import os
import sys
import usfmWriter
from manifestjson import ManifestJson
from usfm_utils import unicodeBlock
# from line_profiler import LineProfiler

projectInfo = None
gui = None
nConverted = 0
precleanup_file = None
postcleanup_file = None

chapMarker_re = re.compile(r'\\c *[\d]{1,3}', re.UNICODE)

def reportError(msg):
    reportToGui(msg, '<<ScriptMessage>>')
    sys.stderr.write(msg + '\n')
    sys.stderr.flush()

# Sends a progress report to the GUI.
# To be called only if the gui is set.
def reportStatus(msg):
    reportToGui(msg, '<<ScriptMessage>>')
    print(msg)

def reportProgress(msg):
    reportToGui(msg, '<<ScriptProgress>>')
    print(msg)

def reportToGui(msg, event):
    if gui:
        with gui.progress_lock:
            gui.progress = msg if not gui.progress else f"{gui.progress}\n{msg}"
        gui.event_generate(event, when="tail")

def open_diagnostic_files():
    global precleanup_file
    global postcleanup_file

    if not precleanup_file:
        work_dir = getWorkDir()
        path = os.path.join(work_dir, "precleanup.txt")
        precleanup_file = io.open(path, "tw", encoding='utf-8-sig')
    if not postcleanup_file:
        work_dir = getWorkDir()
        path = os.path.join(work_dir, "postcleanup.txt")
        postcleanup_file = io.open(path, "tw", encoding='utf-8-sig')

def close_diagnostic_files():
    global precleanup_file
    global postcleanup_file
    if precleanup_file:
        precleanup_file.close()
        precleanup_file = None
    if postcleanup_file:
        postcleanup_file.close()
        postcleanup_file = None

ptag_re = re.compile(r'\\p\s*')

# Does preliminary cleanup on the chunk of text.
# verserange is a list of verse number strings that should exist in the file.
# Returns a string with the (possibly improved) contents of the .txt file.
def cleanupText(text, chap, verserange, firstchunk):
    text = ptag_re.sub('', text)    # Remove \p markers (added artificially by versions of BTTW up thru 1.5.3).
    if unicodeBlock(text) == 'ARABIC':
        text = text.replace('.', '۔')   # Replace period with Arabic full stop
    text = fixVerseMarkers(text)
    if firstchunk:
        text = fixChapterMarkers(text, chap)
    text = fixPunctuationSpacing(text)
    text = fixVerseOrder(text, chap, verserange)
    # #if language_code == "ior":
    #     #text = fixInorMarkers(text, verserange)
    return text

# Reads the text from the specified file and does some cleanup.
def cleanupChunk(path, chap, verserange, firstchunk):
    with io.open(path, "tr", encoding='utf-8-sig') as input:
        text = input.read()
    return cleanupText(text, chap, verserange, firstchunk)

verseMarker_re = re.compile(r'\s*\\v *([\d]{1,3})', re.UNICODE)

# Returns True if there is no valid chapter marker before the first verse marker.
# Returns False if a valid chapter marker precedes first verse marker.
def lacksChapter(text):
    verseMarker = verseMarker_re.search(text)
    if verseMarker:
        text = text[0:verseMarker.start()]
    return (not chapMarker_re.search(text))

# numberMatch_re = re.compile(r'[ \n\t]*([\d]{1,3}[ \n])', re.UNICODE+re.DOTALL)
# untaggednumber_re =     re.compile(r'[^v][ \n]([\d]{1,3}[ \n])', re.UNICODE+re.DOTALL)
widowtags_re = re.compile(r'\\v +[^1-9]')   # widows verse tags

# Adds the specified verse number after the first widowed \v marker found,
# or adds a \v before the orphan verse number if found,
# or reverses a situation where the stranded \v is preceded by the verse number.
def fixStrandedTag(text, vstr):
    widowtag = widowtags_re.search(text)
    widow_pos = -1 if not widowtag else widowtag.end() - 1
    startc = startc_re.match(text)
    startlook = 0 if not startc else startc.end()
    orphanv_pos = text.find(vstr, startlook)
    if orphanv_pos == 0 or (orphanv_pos > 0 and text[orphanv_pos-1] not in '123456789'):
        endpos = orphanv_pos + len(vstr)
        if endpos < len(text) and text[endpos] in '0123456789':
            orphanv_pos = -1
    else:
        endpos = -1
    if endpos > orphanv_pos > -1 and 0 < widow_pos - endpos < 6:    # reverse situation, e.g. 4 /v
        preorphan = 0 if orphanv_pos == 0 else orphanv_pos - 1
        marker = '\\v ' if preorphan == 0 else ' \\v '
        text = text[0:preorphan].rstrip() + marker + vstr + ' ' + text[widow_pos:]
    elif widow_pos > 0:
        text = text[0:widow_pos-1] + ' ' + vstr + ' ' + text[widow_pos:]
    elif endpos > orphanv_pos > -1:
        text = text[0:orphanv_pos] + '\\v ' + text[orphanv_pos:]
    return text

sub0_re = re.compile(r'[\\/]+ *[vV] *[1-9]')    # should match every plausible verse marker
sub1_re = re.compile(r'\S\\v ')     # non-space character before \v
sub2_re = re.compile(r'\\?\s+v\s+([1-9][0-9\-]*)\s+')   # isolated v -- \ v 10 or   v 10
sub3_re = re.compile(r'(\\v [1-9][0-9\-]*)[^0-9\- ]')    # nonspace character after verse number
sub4_re = re.compile(r'(\\v [0-9\-]+ +)\\v +[^1-9]')   # \v 10 \v The...
sub5_re = re.compile(r'\\v\s*(\\v [0-9\-]+ +)')         # \v \v 10
sub6_re = re.compile(r'(\\v [1-9][0-9\-]*)\s*(\\v [1-9][0-9\-]*)')   # \v 10 \v 10
sub7_re = re.compile(r'(^|\s+)v [1-9]')              # missing backslash
sub8_re = re.compile(r'(.*\s*)(\\v [0-9\-]+ +)([.!?,:;)])')   # Punctuation after verse marker
sub9_re = re.compile(r'\\v ([1-9][0-9\-]*)\s+([1-9][0-9\-]*)')   # \v 10 10
vatend_re = re.compile(r'\\v [1-9][0-9\-]*$')   # \v 10 at end of string

# Ensures single space after the verse number.
def spaceVerseNo(text):
    found = sub3_re.search(text)
    while found:
        text = text[0:found.start()] + found.group(1) + " " + text[found.end()-1:].lstrip()
        found = sub3_re.search(text, found.end()+1)
    return text

# Fixes malformed verse markers in a single chunk of text.
def fixVerseMarkers(text):
    found = sub0_re.search(text)
    while found:
        text = text[0:found.start()] + "\\v " + text[found.end()-1:]
        found = sub0_re.search(text, found.start()+3)

    found = sub2_re.search(text)
    while found:
        text = text[0:found.start()] + "\\v " + found.group(1) + text[found.end()-1:]
        found = sub2_re.search(text, found.end())

    found = sub1_re.search(text)    # no space before \v
    while found:
        text = text[0:found.start()+1] + " " + text[found.end()-3:]
        found = sub1_re.search(text, found.start()+3)

    text = spaceVerseNo(text)

    found = sub4_re.search(text)
    while found:
        text = text[0:found.start()] + found.group(1) + text[found.end()-1:]
        found = sub4_re.search(text)

    found = sub5_re.search(text)
    while found:
        text = text[0:found.start()] + found.group(1) + text[found.end():]
        found = sub5_re.search(text)

    found = sub6_re.search(text)
    while found:
        if found.group(1) == found.group(2):
            text = text[0:found.start()] + found.group(1) + text[found.end():]
        found = sub6_re.search(text, found.start()+4)

    found = sub7_re.search(text)
    while found:
        if found.group(1):
            text = text[0:found.start()] + " \\v " + text[found.end()-1:]
        else:
            text = "\\v " + text[found.end()-1:]
        found = sub7_re.search(text)

    # Move or remove the phrase-ending punctuation character found right after a verse marker.
    found = sub8_re.search(text)
    while found:
        before_backslash = found.group(1).rstrip()
        if before_backslash:
            if before_backslash[-1] not in ".,:;?!" and not vatend_re.search(before_backslash):
                before_backslash = f'{before_backslash}{found.group(3)} '
            else:
                before_backslash += ' '
        text = before_backslash + found.group(2) + text[found.end():].lstrip()
        found = sub8_re.search(text, 0)

    found = sub9_re.search(text)
    while found:
        if found.group(1) == found.group(2):
            pos = found.end()+1 if text[found.end()] == ' ' else found.end()
            text = text[0:found.start(2)] + text[pos:]
        found = sub9_re.search(text, found.end(1))

    return text

# chap0_re = re.compile(r'[\\/]+ *[cC] *[1-9]')
chap0_re = re.compile(r'[\\/]+ *[cC] *')    # plausible chapter marker
chap1_re = re.compile(r'\\c *\\')  # missing chapter number
chap3_re = re.compile(r'\\c +([0-9]+)([^0-9\s])')       # no space after chapter number
chap7_re = re.compile(r'(^|\s+)c\s+[1-9]')        # missing backslash
chap8_re = re.compile(r'\\c [0-9]+ +[.!?,:;)]')   # Punctuation after chapter marker

# Fixes missing and malformed chapter markers.
def fixChapterMarkers(text, chap):
    if found := chap0_re.search(text):
        text = text[0:found.start()] + "\\c " + text[found.end():]

    if found := chap1_re.search(text):
        text = text[0:found.start()] + "\\c " + str(int(chap)) + text[found.end()-1:]

    if found := chap3_re.search(text):
        if found.group(2):
            text = text[0:found.start()] + "\\c " + found.group(1) + " " + text[found.end()-1:]
        else:
            text = text[0:found.start()] + "\\c " + found.group(1)

    if found := chap7_re.search(text):
        text = text[0:found.end(1)] + "\\c " + text[found.end()-1:]

    # Move or remove the phrase-ending punctuation character found right after a chapter marker.
    if found := chap8_re.search(text):
        text = text[0:found.end()-1] + text[found.end()-1:].strip()

    if lacksChapter(text):
        text = "\\c " + str(int(chap)) + " " + text.lstrip()

    return text

startc_re = re.compile(r'\s*\\c +[0-9]+\s*')
widowv_re = re.compile(r'\s*\\v +[^1-9]')
vv_re = re.compile(r'([0-9]+)-([0-9]+)')
vmarker_whole_re = re.compile(r'\s*\\v +([1-9][0-9\-]*)')

# Inserts missing verse marker or bridge at the beginning of a string.
def insertMissingVerseMarkers(text, verserange):
    vnumbers_found = find_vnumbers(text)
    miss = -1
    i = 0
    while i < len(verserange) and verserange[i] not in vnumbers_found:
        miss = i
        i += 1
    if miss >= 0:
        insert = verserange[0]
        if miss > 0:
            insert += '-' + verserange[miss]
        startc = startc_re.match(text)
        insertpos = 0 if not startc else startc.end()
        if vmarker := vmarker_whole_re.match(text, insertpos):
            if not '-' in vmarker.group(1):
                insert = verserange[miss] + '-' + vmarker.group(1)
                remainpos = vmarker.end()
            else:
                insertpos = -1
        elif widowv := widowv_re.search(text, insertpos):
            insertpos = widowv.start()
            remainpos = widowv.end() - 1
        else:
            remainpos = insertpos
        if insertpos >= 0:
            vtag = '\\v ' if insertpos == 0 else ' \\v '
            text = text[0:insertpos].rstrip() + vtag + insert + ' ' + text[remainpos:].lstrip()
    return text

vnumbers_re = re.compile(r'\\v ([1-9][0-9\-]*)')

# Returns list of verse numbers/bridges preceded by \v .
def find_vnumbers(text):
    vnumbers_found = [v.group(1) for v in vnumbers_re.finditer(text)]
    vnumbers_found = debridge(vnumbers_found)
    return vnumbers_found

unbridged_re = re.compile(r'(\\v\s+)([1-9][0-9]*)\s+(\\v\s+|)([1-9][0-9]*)')

# Creates a verse bridge where there is an empty verse marker followed by
# another verse marker or just another verse number.
# Moves an empty verse marker to the end of the string if it is at the
# end of the verse range.
def moveEmpty(text, verserange):
    if unbridged := unbridged_re.search(text):
        v1 = unbridged.group(2)
        v2 = unbridged.group(4)
        if int(v2) == int(v1) + 1:
            text = text[0:unbridged.end(2)] + "-" + text[unbridged.start(4):]
        elif len(verserange) == 2 and int(v1) == int(v2) + 1:
            text = text[0:unbridged.start()] + text[unbridged.start(3):unbridged.end(4)] + '-' + v1 + text[unbridged.end():]
        elif v2 in verserange and v1 == verserange[-1] and v2 != v1:
            text = text[0:unbridged.start()] + text[unbridged.start(3):] + " \\v " + unbridged.group(2)
    return text

# Returns the integer value of the first verse number in the string.
def firstInt(vstr):
    try:
        if bridge := vv_re.match(vstr):
            vn = int(bridge.group(1))
        else:
            vn = int(vstr)
    except ValueError as e:
        vn = 0
    return vn

emptyv_re = re.compile(r'\\v\s+[1-9][0-9\-]*\s*(\\|$)')

# Makes the verses numbers in ascending order.
# Does nothing if the text is beyond repair.
def reorderVerseMarkers(text):
    origmarkers = [v for v in vnumbers_re.finditer(text)]
    vnumbers_orig = [firstInt(v.group(1)) for v in origmarkers]
    sorted_list = sorted(vnumbers_orig)

    # Throw out hopeless cases
    if not sorted_list or sorted_list[-1] - sorted_list[0] >= len(sorted_list):
        return text
    if emptyv_re.search(text):
        return text

    if sorted_list != vnumbers_orig:
        i = len(sorted_list) - 1
        while i >= 0:
            pos = origmarkers[i].start() + 3
            endpos = origmarkers[i].end()
            xi = vnumbers_orig.index(sorted_list[i])
            text = text[0:pos] + origmarkers[xi].group(1) + " " + text[endpos:].lstrip()
            i -= 1
    return text

# Many chunks contain verses numbered in reverse, or omit verse numbers, etc.
# This all happens because it is difficult to place the verse bubbles correctly in BTTW.
# This function can fix verse markers in some of these situations.
def fixVerseOrder(text, chap, verserange):
    if precleanup_file:
        precleanup_file.write(text + '\n')

    vnumbers_found = find_vnumbers(text)
    skipchunk = False
    for v in vnumbers_found:
        if not v in verserange:
            skipchunk = True
            reportError(f"Verse number '{v}' out of range {verserange} in chapter {chap}")

    if not skipchunk:
        for v in verserange:
            if not v in vnumbers_found:
                text = fixStrandedTag(text, v)
        text = insertMissingVerseMarkers(text, verserange)
        text = moveEmpty(text, verserange)
        text = reorderVerseMarkers(text)
        text = spaceVerseNo(text)

    if postcleanup_file:
        postcleanup_file.write(text + '\n')

    return text

# Returns a list of individual verse numbers represented in the rawlist.
def debridge(rawlist):
    vlist = []
    for vstr in rawlist:
        vv_range = vv_re.search(vstr)
        if vv_range:
            vnStart = int(vv_range.group(1))
            vnEnd = int(vv_range.group(2))
            for vn in range(vnStart, vnEnd + 1):
                vlist.append(str(vn))
        else:
            vlist.append(vstr)
    return vlist

cvExpr = re.compile(r'\\[cv] +[0-9]+')

# Adds chunk marker before first completed \c or \v marker.
# Returns modified section.
def mark_chunk(section):
    if marker := cvExpr.search(section):
        section = section[0:marker.start()] + '\\s5\n' + section[marker.start():]
    return section

parenthesized_re = re.compile(r'\s*\(.*\)\s*$')

def remove_parens(str):
    if str and parenthesized_re.match(str):
        str = str.strip(' ()\n')
    return str

chapter_re = re.compile(r'\\c\s+([0-9]+)[\s]*')
verse1_re = re.compile(r'\\v\s+1(\s|$)')

# Searches for likely section heading at the beginning of a chunk,
# before the first verse marker.
# If chunk includes a \c markers, section title must come before \v 1.
# Inserts \s before unmarked section heading, if found.
def mark_section_heading_bos(strChunk):
    vpos = strChunk.find("\\v")
    if vpos >= 0:
        chap = chapter_re.search(strChunk)   # valid chapter marker
        cendpos = chap.end() if chap else 0
        if cendpos > 0:
            verse1 = verse1_re.search(strChunk)
            vpos = verse1.start() if verse1 else 0
    if vpos >= 0 and vpos >= cendpos:
        candidate = strChunk[cendpos:vpos] if vpos == len(strChunk) else strChunk[cendpos:vpos-1]
        candidate = remove_parens(candidate)
        if section_titles.prob_heading(candidate) >= 0.1:
            heading = candidate.rstrip('.\u0964\u0965\u1362\u06D4')
            strChunk = section_titles.insert_heading(strChunk[0:cendpos], heading, strChunk[vpos:])
    return strChunk

anyMarker_re = re.compile(r'\\[a-z]+[a-z1-5]* ?[0-9]*')

# Searches for likely section heading at end of line, after last usfm marker.
# Inserts \s before unmarked section heading, if found.
def mark_section_heading_eos(section):
    marker = None
    bslist = [bs.start() for bs in anyMarker_re.finditer(section)]
    for pos in reversed(bslist):
        if marker := anyMarker_re.match(section[pos:]):
            break
    lmpos = pos + marker.end() if marker else 0
    lmpos += len(section[lmpos:]) - len(section[lmpos:].lstrip())
    sentence_starts = [pos + lmpos for pos in sentences.nextstartpos(section[lmpos:])]
    if len(sentence_starts) > (1 if marker else 0):
        startpos = sentence_starts[-1]
        candidate = None
        if startpos > 0 and section[startpos-1] == '(':
            startpos -= 1
            candidate = section_titles.find_parenthesized_heading(section, 0.499)
            candidate = remove_parens(candidate)
        elif startpos - lmpos > 15:  # avoid marking headings that would leave a very short verse
            candidate = section[startpos:]  # last "sentence" in the line
        if candidate and section_titles.prob_heading(candidate) > 0.7:
            heading = candidate.rstrip('.\u0964\u0965\u1362\u06D4')
            section = section_titles.insert_heading(section[0:startpos], heading, "")
    return section

lbi_re = re.compile(r'^[^\\\n]+$', re.MULTILINE)

# Marks likely section heading on a line by itself.
# lastref is the verse reference of the last verse in the section.
# lastchunk specifies whether the section is the last chunk in a chapter.
def mark_section_heading_lbi(section, lastref, lastchunk):
    lbi = lbi_re.search(section)
    while lbi:
        if lbi.end() >= len(section) and (lastchunk or lastref in section_titles.exclude_eol_checks):
            break
        candidate = remove_parens(lbi.group(0))
        if section_titles.prob_heading(candidate) > 0.1:
            startpos = lbi.start() + (len(candidate) - len(candidate.lstrip(' ')))
            heading = candidate.rstrip('.\u0964\u0965\u1362\u06D4')
            section = section_titles.insert_heading(section[0:startpos], heading, section[lbi.end():])
            break
        lbi = lbi_re.search(section, lbi.end())
    return section

# Inserts \s before any section heading that can be identified.
# Chunks at the end of a chapter (lastchunk=True) are treated slightly differently.
# Currently searches for headings only:
#   before the first \v marker
#   after the last sentence after the last usfm marker
#   on lines with no usfm markers
# Marks at most one section heading.
# Returns the chunk text, modified or not.
# @param lastref is the verse reference of the last verse in the chunk
# @param lastchunk is True when it is the last chunk in the chapter
def mark_section_headings(strChunk, lastref, lastchunk):
    orig_section = strChunk
    strChunk = mark_section_heading_bos(strChunk)
    if not lastchunk and lastref not in section_titles.exclude_eol_checks:
        strChunk = mark_section_heading_eos(strChunk)
    if strChunk == orig_section:
        strChunk = mark_section_heading_lbi(strChunk, lastref, lastchunk)
    return strChunk

vtag_re = re.compile(r'([\\p\s]*)\\v\s')

# Called only for the first chunk in a chapter.
# Inserts chapter label if needed.
# Returns modified section.
def augmentChapter(schap, section, chapterTitle):
    if chap := chapter_re.search(section):  # valid chapter marker
        pos = chap.end()
    else:
        pos = 0
    label = chapterTitle.strip()
    clstr = ""
    if label and label != schap:
        clstr = "\n\\cl " + label
        section = section[:pos].rstrip() + clstr + "\n" + section[pos:].lstrip()
    # Ensure \p before first verse
    if v1 := vtag_re.search(section):
        if not v1.group(1).endswith("\\p\n"):
            preceding = v1.group(1)
            ipos = v1.start() + len(preceding)
            section = section[:ipos] + "\\p\n" + section[ipos:]
    return section

space1_re = re.compile(r' +([.?!;:,)\]].*)', re.DOTALL)    # space before clause-ending punctuation
space2_re = re.compile(r'[¿¡\[\(] +.*', re.DOTALL)    # space after clause-starting punctuation
jammed1_re = re.compile(r'[.?!;:,)][\w¿¡\[\(]')  # no space between clause-ending punctuation and next word -- but \w matches digits also
jammed2_re = re.compile(r'\w[¿¡\[\(]')        # no space before clause-starting punctuation

# Removes extraneous space before clause ending punctuation and adds space after
# sentence/clause end if needed.
def fixPunctuationSpacing(section):
    # Remove space before phrase-ending punctuation
    found = space1_re.search(section)
    while found:
        remainder = found.group(1)
        if len(remainder) <= 1 or remainder[1] != '.':
            section = section[0:found.start()] + remainder
        found = space1_re.search(section, found.start()+1)

    # Remove space after phrase-starting punctuation
    found = space2_re.search(section)
    while found:
        section = section[0:found.start()+1] + section[found.start()+2:]
        found = space2_re.search(section, found.start())

    # Add space between clause-ending punctuation and next word.
    match = jammed1_re.search(section)
    while match:
        if not section[match.end()-1].isdigit():
            section = section[:match.start()+1] + ' ' + section[match.end()-1:]
        match = jammed1_re.search(section, match.end())

    # Add space before clause-starting punctuation.
    match = jammed2_re.search(section)
    while match:
        section = section[:match.start()+1] + ' ' + section[match.end()-1:]
        match = jammed2_re.search(section, match.end())

    return section

stripcv_re = re.compile(r'\s*\\([cv])\s*\d+\s*', re.UNICODE)

'''
The next few functions are specific to a situation where
the verse markers are listed at the beginning of the
chunk but are empty, immediately followed by the first verse, followed by the next verse number and
verse, followed by the next verse number and verse, and so on.
See Inor (ior) language, Matt 13:36-39 for example.
This code goes back to 2020, and is not very good. But as of 7/14/25, the code is still useful for Inor.
I have not encountered the situation in any other language.
'''
# # Returns the string with \v markers removed at beginning of chunk.
# def stripInitialMarkers(text):
#     marker = stripcv_re.match(text)
#     while marker:
#         text = text[marker.end():]
#         marker = stripcv_re.match(text)
#     return text

# Returns True if the string contains all the verse numbers in verserange and there are no \v tags
# def fitsInorPattern(str, verserange):
#     fits = not ("\\v" in str)
#     if fits:
#         for v in verserange:
#             if not v in str:
#                 fits = False
#                 break
#     return fits

# This method is only called for the Inor language.
# Fixes very common error in Inor translations where the verse markers are listed at the beginning of the
# chunk but are empty, immediately followed by the first verse, followed by the next verse number and
# verse, followed by the next verse number and verse, and so on.
# def fixInorMarkers(text, verserange):
#     saveChapterMarker = ""
#     if c := chapMarker_re.search(text):
#         saveChapterMarker = text[c.start():c.end()]
#     str = stripInitialMarkers(text)
#     if not str.startswith(verserange[0]):
#         str = verserange[0] + " " + str
#     if fitsInorPattern(str, verserange):
#         for v in verserange:
#             pos = str.find(v)
#             if pos == 0:
#                 str = "\\v " + str[pos:]
#             else:
#                 str = str[0:pos] + "\n\\v " + str[pos:]
#         if saveChapterMarker:
#             str = saveChapterMarker + "\n" + str

#         # Ensure space after verse markers
#         found = sub3_re.search(str)
#         while found:
#             pos = found.end()-1
#             if str[pos] == '.':
#                 pos += 1
#             str = str[0:found.end()-1] + " " + str[pos:]
#             found = sub3_re.search(str, pos+1)
#     else:
#         str = text
#     return str

marker_re = re.compile(r' \\([a-z]+[a-z1-5]*)')

def newline_markers(s:str):
    pos = 0
    for match in marker_re.finditer(s, pos):
        if match.group(1) in usfmWriter.startline_tags:
            pos = match.start()
            s = s[:pos] + '\n' + s[pos+1:]
            pos += 2
    return s

condense_re = re.compile(r'[ \t][ \t]+')
conflict_re = re.compile(f'<<< +HEAD|>>>>>|=====')

# Converts the section string by adding chapter, label, chunk, and p parkers where needed.
# Starts each usfm marker on a new line.
# Fixes white space, such as converting tabs to spaces and removing trailing spaces.def
def convertChunk(schap, strChunk, firstinchapter, lastref, chapterTitle, lastchunk):
    strChunk = re.sub(condense_re, ' ', strChunk)
    strChunk = newline_markers(strChunk)
    strChunk = strChunk.replace(" \n", "\n")

    config = ToolsConfigManager()
    if config.getboolean('Txt2USFM', 'section_headings') and not conflict_re.search(strChunk):
        strChunk = mark_section_headings(strChunk, lastref, lastchunk)

    if config.getboolean('Txt2USFM', 'mark_chunks'):
        strChunk = mark_chunk(strChunk)

    if firstinchapter:
        strChunk = augmentChapter(schap, strChunk, chapterTitle)
    return strChunk

# Returns True if the specified directory is one with text files to be converted
def isChapter(dirname):
    isChap = False
    if dirname != '00' and re.match(r'\d{2,3}$', dirname):
        isChap = True
    return isChap

# Returns True if the specified path looks like a collection of chapter folders
def isBookFolder(path):
    chapterPath = os.path.join(path, '01')
    return os.path.isdir(chapterPath)

# Copies information from the manifest.json to ProjectInfo.
def extractDataFromManifest(manifest):
    global projectInfo
    assert projectInfo
    language_id = manifest.getLanguageId()
    language_code = ToolsConfigManager().get('Txt2USFM', 'language_code')
    if language_code != language_id:
        reportError(f"Language code ({language_code}) does not match target_language Id ({language_id}) in {shortname(manifest.getPath())}.")
    projectInfo.setLanguage(manifest.getLanguageName(), locale='en', direction=manifest.getLanguageDirection())
    projectInfo.addContributors(manifest.getTranslators())
    for source in manifest.getSources():
        projectInfo.addSource(source['language_id'], source['resource_id'], source['version'])
    projectInfo.setResourceType(manifest.getResourceId())

# Attempts to determine the book ID from the folder name.
# Assumes folder name contains language code and book ID in the format.
def getBookIdFromFolderName(folder):
    bookId = ""
    language_code = ToolsConfigManager().get('Txt2USFM', 'language_code')
    matchstr = language_code + "_([a-zA-Z1-3][a-zA-Z][a-zA-Z])_"
    if okname := re.search(matchstr, os.path.basename(folder)):
        bookId = okname.group(1)
    return bookId

# Locates title.txt in either the front folder or 00 folder.
# Extracts the lines of that file as the book title.
# If neither file exists, return the book name in English.
def getBookTitle(folder, bookId):
    bookTitle = []
    path = os.path.join(folder, "front/title.txt")
    if not os.path.isfile(path):
        path = os.path.join(folder, "00/title.txt")
    if os.path.isfile(path):
        with io.open(path, "tr", 1, encoding='utf-8-sig') as f:
            lines = f.readlines()
        for line in lines:
            line = line.strip().rstrip(".")
            if line:
                line = " ".join(line.split())  # eliminates consecutive spaces
                if not line.istitle():
                    line = line.title().replace("Iii", 'III')
                    line = line.replace("Ii", 'II')
                bookTitle.append(line)
    elif bookId.upper() in usfm_verses.verseCounts:
        # As a last resort, use the English book title
        bookTitle.append(usfm_verses.verseCounts[bookId.upper()]['en_name'])
    else:
        reportError("   Can't open " + path + "!")
    return bookTitle

# Appends information about the current book to the global projects list.
# Ultimately adds to manifest.yaml.
def appendToProjects(bookId, bookTitle):
    global projectInfo
    assert projectInfo
    usfmPath = os.path.join(getWorkDir(), makeUsfmFilename(bookId))
    projectInfo.addProject(bookTitle, bookId, usfmPath)

def shortname(longpath):
    source_dir = ToolsConfigManager().get('Txt2USFM', 'source_dir')
    shortname = longpath
    if shortname == source_dir:
        shortname = os.path.basename(longpath)
    elif shortname.startswith(source_dir):
        shortname = os.path.relpath(shortname, source_dir)
    return shortname

# Converts one book folder if it can determine the book ID and title.
def convertFolder(folder):
    language_code = ToolsConfigManager().get('Txt2USFM', 'language_code')
    if language_code + '_' in os.path.basename(folder):
        global projectInfo
        assert projectInfo
        projectInfo.useManifest(docreate=True)  # Needed if this is the first project to be added
        mj = ManifestJson()
        if errors := mj.load(folder):
            for error in errors:
                reportError(error)
            bookId = ""
        else:
            bookId = mj.getBookId()
        if bookId:  # manifest.json was good
            extractDataFromManifest(mj)
        else:
            bookId = getBookIdFromFolderName(folder)
        bookTitle = getBookTitle(folder, bookId)

        if bookId and bookTitle:
            convertBook(folder, bookId.upper(), bookTitle)   # converts the pieces in the current folder
            # profile.print_stats()
            appendToProjects(bookId, bookTitle[0])
            global nConverted
            nConverted += 1
        else:
            if not bookId:
                reportError("Unable to determine book ID in " + shortname(folder))
            if not bookTitle:
                reportError("Unable to determine book title in " + shortname(folder))
    else:
        reportError(f"Book folder name ({os.path.basename(folder)}) does not correspond to language code ({language_code})")

# Returns file name for usfm file in current folder
def makeUsfmFilename(bookId):
    num = usfm_verses.verseCounts[bookId.upper()]['usfm_number']
    filename = num + '-' + bookId.upper() + '.usfm'
    return filename

def writeHeader(usfm, bookId, bookTitle):
    usfm.writeUsfm("id", bookId)
    usfm.writeUsfm("ide", "UTF-8")
    usfm.writeUsfm("h", bookTitle[0])
    usfm.writeUsfm("toc1", bookTitle[0])
    usfm.writeUsfm("toc2", bookTitle[0])
    usfm.writeUsfm("toc3", bookId.lower())
    level = 1
    for line in bookTitle:
        usfm.writeUsfm(f"mt{level}", line)
        level += 1

# This method returns a list of chapter folders in the specified directory.
# This list is returned in numeric order.
def listChapters(bookdir):
    list = []
    for directory in os.listdir(bookdir):
        if isChapter(directory):
            list.append(directory)
    if len(list) > 99:
        list.sort(key=int)
    return list

txtfile_re = re.compile(r'(\d{2,3})\.txt$', re.IGNORECASE)

# This method lists the chunk names (just the digits, without the .txt extension)
# in the specified folder.
# The list is returned in numeric order.
def listChunks(chap):
    list = []
    longest = 0
    for filename in os.listdir(chap):
        chunky = txtfile_re.match(filename)
        if chunky and chunky.group(1) != '00':
            chunk = chunky.group(1)
            list.append(chunk)
            if len(chunk) > longest:
                longest = len(chunk)
    if longest > 2:
        list.sort(key=int)
    return list

# Compiles a list of verse number strings that should be in the specified chunk
def makeVerseRange(chunks, i, bookId, chapter):
    if i < len(chunks) and chapter <= usfm_verses.verseCounts[bookId]['chapters']:
        verserange = [ chunks[i].lstrip('0') ]
        if i+1 < len(chunks):
            limit = int(chunks[i+1])
        else:           # last chunk
            limit = usfm_verses.verseCounts[bookId]['verses'][chapter-1] + 1
        v = int(chunks[i]) + 1
        while v < limit:
            verserange.append(str(v))
            v += 1
    else:
        verserange = []
    return verserange

# Tries to find front/title.txt or 00/title.txt.
# Returns the content of that file if it exists, or an empty string.
def getChapterTitle(chapterpath):
    title = ""
    titlepath = os.path.join(chapterpath, "title.txt")
    if os.path.isfile(titlepath):
        with io.open(titlepath, 'tr', encoding='utf-8-sig') as titlefile:
            title = titlefile.read()
    return title

# Converts all the text files under the specified folder to USFM.
# profile = LineProfiler()
def convertBook(folder, bookId, bookTitle):
    reportProgress(f"CONVERTING {shortname(folder)}")
    sys.stdout.flush()

    # Open output USFM file for writing.
    usfmPath = os.path.join(getWorkDir(), makeUsfmFilename(bookId))
    usfm = usfmWriter.usfmWriter(usfmPath)
    writeHeader(usfm, bookId, bookTitle)

    for chap in listChapters(folder):
        chapterpath = os.path.join(folder, chap)
        chapterTitle = getChapterTitle(chapterpath)
        schap = str(int(chap))
        chunks = listChunks(chapterpath)
        firstchunk = True
        for i in range(len(chunks)):
            filename = chunks[i] + ".txt"
            txtPath = os.path.join(chapterpath, filename)
            verserange = makeVerseRange(chunks, i, bookId, int(chap))
            section = cleanupChunk(txtPath, chap, verserange, firstchunk)
            lastref = f"{bookId} {schap}:{verserange[-1]}"
            section = convertChunk(schap, section, firstchunk, lastref, chapterTitle, i+1 >= len(chunks)).rstrip()
            usfm.writeStr('\n' + section)
            firstchunk = False
    usfm.close()

# Converts the book or books contained in the specified folder
def convert(dir):
    if isBookFolder(dir):
        convertFolder(dir)
    else:       # presumed to be a folder containing multiple books
        for directory in os.listdir(dir):
            folder = os.path.join(dir, directory)
            if isBookFolder(folder):
                convertFolder(folder)

# Temporary function, until all references to "target_dir" are removed.
def getWorkDir():
    config = ToolsConfigManager()
    return config.get('Txt2USFM', 'work_dir')

# Processes each directory and its files one at a time
def main(app = None):
    global gui
    gui = app
    work_dir = getWorkDir()

    Path(work_dir).mkdir(exist_ok=True)
    config = ToolsConfigManager()
    global projectInfo
    projectInfo = ProjectInfo(work_dir, config.get('Txt2USFM', 'language_code'))
    projectInfo.useManifest(docreate=False)
    projectInfo.resetSources()
    projectInfo.setGenerator("Txt2USFM", config.get('UsfmWizard', 'version'))

    if config.getboolean('Txt2USFM', 'diagnostics'):
        open_diagnostic_files()

    convert(config.get('Txt2USFM', 'source_dir'))
    if nConverted > 0:
        is_valid, msg = projectInfo.save()
        if not is_valid:
            reportError(f"Error saving {msg}")
        else:
            reportStatus("\nDone.")
    if gui:
        gui.event_generate('<<ScriptEnd>>', when="tail")

    close_diagnostic_files()

if __name__ == "__main__":
    main()
