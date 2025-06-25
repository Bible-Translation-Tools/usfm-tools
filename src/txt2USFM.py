# -*- coding: utf-8 -*-
# This script converts text files from tStudio to USFM Resource Container format.
#    Parses manifest.json to get the book ID, contributors, sources, etc.
#    Outputs a project information file in the parent folder.
#    Outputs list of contributors and sources gleaned from all manifest.json files.
#    Finds and parses title.txt to get the book title.
#    Populates the USFM headers.
#    Standardizes the names of .usfm files. For example 41-MAT.usfm and 42-MRK.usfm.
#    Converts multiple books at once if there are multiple books.

import configmanager
from projectinfo import ProjectInfo
from pathlib import Path
import sentences
import section_titles
import usfm_verses
import re
import io
import os
import sys
import json
import usfmWriter
# from line_profiler import LineProfiler

config = configmanager.ToolsConfigManager()
projectInfo = None
gui = None

verseTags_re = re.compile(r'\\v +[^1-9]', re.UNICODE)
numberstart_re = re.compile(r'([\d]{1,3})[ \n]', re.UNICODE)
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

numbers_re = re.compile(r'[ \n]([\d]{1,3})[ \n]', re.UNICODE)
verseMarker_re = re.compile(r'[ \n\t]*\\v *([\d]{1,3})', re.UNICODE)

# Does preliminary cleanup on the text file, prior to conversion.
# Calls ensureMarkers() to put in missing chapter and verse markers.
# verserange is a list of verse number strings that should exist in the file.
# Returns a string with the (possibly improved) contents of the .txt file.
def cleanupTextFile(path, chap, verserange):
    vn_start = int(verserange[0])
    vn_end = int(verserange[-1])
    with io.open(path, "tr", encoding='utf-8-sig') as input:
        origtext = input.read()
    text = fixVerseMarkers(origtext)
    text = fixChapterMarkers(text, vn_start == 1)
    text = fixPunctuationSpacing(text)

    missing_chapter = ""
    if vn_start == 1 and lacksChapter(text):
        missing_chapter = chap.lstrip('0')
    missing_verses = lackingVerses(text, verserange, numbers_re)
    missing_markers = lackingVerses(text, verserange, verseMarker_re)
    if missing_chapter or missing_verses or missing_markers:
        if verseTags_re.search(text):
            if missing_verses:
                text = ensureNumbers(text, missing_verses)
                missing_verses = lackingVerses(text, verserange, numbers_re)
        text = ensureMarkers(text, missing_chapter, vn_start, vn_end, missing_verses, missing_markers)
    #if language_code == "ior":
        #text = fixInorMarkers(text, verserange)
    return text

# Returns True unchanged if there is no \c marker before the first verse marker.
# Returns False if \c marker precedes first verse marker.
def lacksChapter(text):
    verseMarker = verseMarker_re.search(text)
    if verseMarker:
        text = text[0:verseMarker.start()]
    return (not chapMarker_re.search(text))

# Searches for the expected verse numbers in the string using the specified expression.
# Returns list of verse numbers (marked or unmarked) missing from the string
def lackingVerses(str, verserange, expr_re):
    missing_verses = []
    numbers = expr_re.findall(str)
#    if len(numbers) < len(verserange):     # not enough verse numbers
    versenumbers_found = []
    for vn in numbers:
        if vn in verserange:
            versenumbers_found.append(vn)
    for verse in verserange:
        if not verse in versenumbers_found:
            missing_verses.append(verse)
    return missing_verses

numberMatch_re = re.compile(r'[ \n\t]*([\d]{1,3}[ \n])', re.UNICODE+re.DOTALL)
untaggednumber_re =     re.compile(r'[^v][ \n]([\d]{1,3}[ \n])', re.UNICODE+re.DOTALL)

# Writes chapter marker at beginning of file if needed.
# Write initial verse marker and number at beginning of file if needed.
# Finds orphaned verse numbers and inserts \v before them.
# missingVerses is a list of verse numbers (in string format) not found in the string
# missingMarkers is a list of verse markers (e.g. "\v 1") not found in the string
# Returns corrected string.
def ensureMarkers(text, missingChapter, vn_start, vn_end, missingVerses, missingMarkers):
    goodstr = ""
    if missingChapter:
        goodstr = "\\c " + missingChapter + '\n'
    if not (missingVerses or missingMarkers):
        goodstr += text
    else:
        chap = chapMarker_re.search(text)
        if chap:
            goodstr += text[0:chap.end()] + '\n'
            text = text[chap.end():]

        verseAtStart = numberstart_re.match(text)
        if (missingVerses or missingMarkers) and not verseAtStart:
            verseAtStart = verseMarker_re.match(text)
        if not verseAtStart:
            startVV = missingStartVV(vn_start, vn_end, text)
            text = startVV + text      # insert initial verse marker
        number = numberMatch_re.match(text)          # matches orphaned number at beginning of the string
        if not number:
            number = untaggednumber_re.search(text)          # finds orphaned number anywhere in string
        while number:
            # verse = number.group(1)
            verse = number.group(1)[0:-1]
            if verse in missingMarkers:         # outputs \v then the number
                goodstr += text[0:number.start(1)] + "\\v " + number.group(1)
            else:
                goodstr += text[0:number.end()]   # leave untagged number as is and move on
            text = text[number.end():]
            number = untaggednumber_re.search(text)
        goodstr += text
    return goodstr

# Generates a string like "\v 1"  or "\v 1-3" which should be prepended to the specified text
# start_vn is the starting verse number
def missingStartVV(vn_start, vn_end, text):
    firstVerseFound = verseMarker_re.search(text)
    if firstVerseFound:
        firstVerseNumberFound = int(firstVerseFound.group(1))
    else:
        firstVerseNumberFound = 999
    vn = vn_start
    while vn < firstVerseNumberFound - 1 and vn < vn_end:
        vn += 1
    if vn_start == vn:
        startVV = "\\v " + str(vn_start) + " "
    else:
        startVV = "\\v " + str(vn_start) + "-" + str(vn) + " "
    return startVV

def ensureNumbers(text, missingVerses):
    missi = 0
    while missi < len(missingVerses):
        versetag = verseTags_re.search(text)
        if versetag:
            text = text[0:versetag.end()-1] + missingVerses[missi] + " " + text[versetag.end()-1:]
        missi += 1
    return text

sub0_re = re.compile(r'[\\/]+ *[vV] *[1-9]')
sub1_re = re.compile(r'[^\n ]\\v ')     # non-space character before \v
sub3_re = re.compile(r'\\v +([1-9][0-9\-]*)([^0-9\-\s])')       # no space after verse number
sub4_re = re.compile(r'(\\v +[0-9\-]+ +)\\v +[^1-9]')   # \v 10 \v The...
sub5_re = re.compile(r'\\v\s*(\\v +[0-9\-]+ +)')         # \v \v 10
sub7_re = re.compile(r'(^|\s+)v [1-9]')              # missing backslash
sub8_re = re.compile(r'(^|.)\s*(\\v [0-9\-]+ +)([.!?,:;)])')   # Punctuation after verse marker

# Fixes malformed verse markers in a single chunk of text.
def fixVerseMarkers(text):
    found = sub0_re.search(text)
    while found:
        text = text[0:found.start()] + "\\v " + text[found.end()-1:]
        found = sub0_re.search(text, found.start()+3)

    found = sub1_re.search(text)    # no space before \v
    while found:
        text = text[0:found.start()+1] + " " + text[found.end()-3:]
        found = sub1_re.search(text, found.start()+3)

    found = sub3_re.search(text)
    while found:
        if found.group(2):
            text = text[0:found.start()] + "\\v " + found.group(1) + " " + text[found.end()-1:]
        else:
            text = text[0:found.start()] + "\\v " + found.group(1)
        found = sub3_re.search(text, found.end()+1)

    found = sub4_re.search(text)
    while found:
        text = text[0:found.start()] + found.group(1) + text[found.end()-1:]
        found = sub4_re.search(text)

    found = sub5_re.search(text)
    while found:
        text = text[0:found.start()] + found.group(1) + text[found.end():]
        found = sub5_re.search(text)

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
        if not found.group(1):  # match starts at beginning of line
            before_backslash = ""
        elif found.group(1) not in ".,:;?!":
            before_backslash = text[0:found.start()+1] + found.group(3) + " "
        else:
            before_backslash = text[0:found.start()+1] + " "    # just delete the stray punctuation
        text = before_backslash + found.group(2) + text[found.end():].lstrip()
        found = sub8_re.search(text, found.end()-1)

    return text

chap0_re = re.compile(r'[\\/]+ *[cC] *[1-9]')
chap3_re = re.compile(r'\\c +([0-9]+)([^0-9\s])')       # no space after chapter number
chap7_re = re.compile(r'(^|\s+)c [1-9]')              # missing backslash
chap8_re = re.compile(r'\\c [0-9]+ +[.!?,:;)]')   # Punctuation after chapter marker

# Fixes certain malformed chapter markers.
def fixChapterMarkers(text, firstverse):
    if found := chap0_re.search(text):
        text = text[0:found.start()] + "\\c " + text[found.end()-1:]

    if found := chap3_re.search(text):
        if found.group(2):
            text = text[0:found.start()] + "\\c " + found.group(1) + " " + text[found.end()-1:]
        else:
            text = text[0:found.start()] + "\\c " + found.group(1)

    if firstverse:
        if found := chap7_re.search(text):
            if found.group(1):
                text = text[0:found.start()] + " \\c " + text[found.end()-1:]
            else:
                text = "\\c " + text[found.end()-1:]

    # Move or remove the phrase-ending punctuation character found right after a chapter marker.
    if found := chap8_re.search(text):
        text = text[0:found.end()-1] + text[found.end()-1:].strip()

    return text

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

chapter_re = re.compile(r'\\c\s+([0-9]+)[\s]*', re.UNICODE)

# Searches for likely section heading at the beginning of a section,
# before the first verse marker.
# Inserts \s before unmarked section heading, if found.
def mark_section_heading_bos(section):
    chap = chapter_re.search(section)
    cendpos = chap.end() if chap else 0
    vpos = section.find("\\v")
    if vpos < 0:
        vpos = len(section)
    if cendpos > vpos:
        cendpos = 0
    candidate = section[cendpos:vpos] if vpos == len(section) else section[cendpos:vpos-1]
    candidate = remove_parens(candidate)
    if section_titles.is_heading(candidate):
        section = section_titles.insert_heading(section[0:cendpos], candidate, section[vpos:])
    return section

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
            candidate = section_titles.find_parenthesized_heading(section)
            candidate = remove_parens(candidate)
        else:
            candidate = section[startpos:]  # last "sentence" in the line
        if candidate and section_titles.is_heading(candidate):
            section = section_titles.insert_heading(section[0:startpos], candidate, "")
    return section

lbi_re = re.compile(r'^[^\\\n]+$', re.MULTILINE)

# Marks likely section heading on a line by itself.
# lastchunk specifies whether the section is the last chunk in a chapter.
def mark_section_heading_lbi(section, lastchunk):
    lbi = lbi_re.search(section)
    while lbi:
        if lastchunk and lbi.end() >= len(section):
            break
        candidate = remove_parens(lbi.group(0))
        if section_titles.is_heading(candidate):
            startpos = lbi.start() + (len(candidate) - len(candidate.lstrip(' ')))
            section = section_titles.insert_heading(section[0:startpos], candidate, section[lbi.end():])
            break
        lbi = lbi_re.search(section, lbi.end())
    return section

# Inserts \s before any section heading that can be identified.
# Sections at the end of a chapter (lastchunk=True) are treated slightly differently.
# Currently searches for headings only:
#   before the first \v marker
#   after the last sentence after the last usfm marker
#   on lines with no usfm markers
# Marks at most one section heading.
# Returns the section, modified or not.
def mark_section_headings(section, lastchunk):
    orig_section = section
    section = mark_section_heading_bos(section)
    if not lastchunk:
        section = mark_section_heading_eos(section)
    if section == orig_section:
        section = mark_section_heading_lbi(section, lastchunk)
    return section

verse1_re = re.compile(r'([\\p\s]*)\\v\s+1[\-\s]')

# Inserts chapter label if needed.
# Returns modified section.
def augmentChapter(section, chapterTitle):
    if chap := chapter_re.search(section):
        label = chapterTitle.strip()
        clstr = ""
        if label and label != chap.group(1):
            clstr = "\n\\cl " + label
        section = section[:chap.end()].rstrip() + clstr + "\n" + section[chap.end():].lstrip()
    # Ensure \p before verse 1
    if v1 := verse1_re.search(section):
        if not v1.group(1).endswith("\\p\n"):
            preceding = v1.group(1)
            ipos = v1.start() + len(preceding)
            section = section[:ipos] + "\\p\n" + section[ipos:]
    return section

spacedot_re = re.compile(r'[^0-9] [.?!;:,][^\.]')    # space before clause-ending punctuation
jammed = re.compile(r'[.?!;:,)][\w]', re.UNICODE)     # no space between clause-ending punctuation and next word -- but \w matches digits also

# Removes extraneous space before clause ending punctuation and adds space after
# sentence/clause end if needed.
def fixPunctuationSpacing(section):
    # First remove space before most punctuation
    found = spacedot_re.search(section)
    while found:
        section = section[0:found.start()+1] + section[found.end()-2:]
        found = spacedot_re.search(section)

    # Then add space between clause-ending punctuation and next word.
    match = jammed.search(section, 0)
    while match:
        if section[match.end()-1] not in "0123456789":
            section = section[:match.start()+1] + ' ' + section[match.end()-1:]
        match = jammed.search(section, match.end())
    return section

stripcv_re = re.compile(r'\s*\\([cv])\s*\d+\s*', re.UNICODE)

# Returns the string with \v markers removed at beginning of chunk.
def stripInitialMarkers(text):
    marker = stripcv_re.match(text)
    while marker:
        text = text[marker.end():]
        marker = stripcv_re.match(text)
    return text

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

# Many chunks contain verses numbered in reverse. This happens because it
# is difficult to place the verse marker bubbles correctly in BTT-Writer.
def fixVerseOrder(section):
    # bslist = [bs.start() for bs in anyMarker_re.finditer(section)]
    return section

condense_re = re.compile(r'[ \t][ \t]+')

# Converts the section string to a single
# USFM section by adding chapter label, chunk marker, and paragraph marker where needed.
# Starts each usfm marker on a new line.
# Fixes white space, such as converting tabs to spaces and removing trailing spaces.def
def convertSection(section, chapterTitle, lastchunk):
    section = re.sub(condense_re, ' ', section)
    section = section.replace(" \\", "\n\\")
    section = section.replace(" \n", "\n")
    # section = fixVerseOrder(section)

    if config.getboolean('Txt2USFM', 'section_headings'):
        section = mark_section_headings(section, lastchunk)

    if config.getboolean('Txt2USFM', 'mark_chunks'):
        section = mark_chunk(section)

    section = augmentChapter(section, chapterTitle)
    return section

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

# Extracts information from the specified manifest.json file.
# Adds information to ProjectInfo.
# Returns book ID.
def parseManifest(path):
    bookId = ""
    try:
        jsonFile = io.open(path, "tr", encoding='utf-8-sig')
    except IOError as e:
        reportError("   Can't open: " + path + "!")
    else:
        # global contributors
        try:
            manifest = json.load(jsonFile)
        except ValueError as e:
            reportError("   Can't parse: " + path + ".")
        else:
            global projectInfo
            assert projectInfo
            language_id = manifest['target_language']['id']
            if config.get('Txt2USFM', 'language_code') != language_id:
                reportError(f"Language code ({config.get('Txt2USFM', 'language_code')}) does not match Language Id ({language_id}) in {shortname(path)}.")
            projectInfo.setLanguage(manifest['target_language']['name'], manifest['target_language']['direction'])
            bookId = manifest['project']['id']
            # contributors += [x.title() for x in manifest['translators']]
            projectInfo.addContributors(manifest['translators'])
            for source in manifest['source_translations']:
                projectInfo.addSource(source['language_id'], source['resource_id'], source['version'])
            projectInfo.setResourceType(manifest['resource']['id'])
        jsonFile.close()
    return bookId.upper()

# Parses all manifest***.json files in the current folder.
# Return upper case bookId, or empty string if failed to retrieve.
# Also parses other information out of the manifest.
def getBookId(folder):
    bookId = ""
    for fname in os.listdir(folder):
        if re.match(r'manifest.*\.json$', fname):
            path = os.path.join(folder, fname)
            if os.path.isfile(path):
                bookId = parseManifest(path)
    if not bookId:
        language_code = config.get('Txt2USFM', 'language_code')
        matchstr = language_code + "_([a-zA-Z1-3][a-zA-Z][a-zA-Z])_"
        if okname := re.search(matchstr, os.path.basename(folder)):
            bookId = okname.group(1).upper()
    return bookId

# Locates title.txt in either the front folder or 00 folder.
# Extracts the first line of that file as the book title.
# If neither file exists, return the book name in English.
def getBookTitle(folder, bookId):
    bookTitle = ""
    path = os.path.join(folder, "front/title.txt")
    if not os.path.isfile(path):
        path = os.path.join(folder, "00/title.txt")
    if os.path.isfile(path):
        with io.open(path, "tr", 1, encoding='utf-8-sig') as f:
            lines = f.readlines()
        for line in lines:
            if bookTitle := line.strip().rstrip("."):
                break
        bookTitle = " ".join(bookTitle.split())  # eliminates consecutive spaces
        if not bookTitle.istitle():
            bookTitle = bookTitle.title().replace("Iii", 'III')
            bookTitle = bookTitle.replace("Ii", 'II')
    elif bookId in usfm_verses.verseCounts:
        # As a last resort, use the English book title
        bookTitle = usfm_verses.verseCounts[bookId]['en_name']
    else:
        reportError("   Can't open " + path + "!")
    return bookTitle

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
    assert projectInfo
    projectInfo.addProject(project)

def shortname(longpath):
    source_dir = config.get('Txt2USFM', 'source_dir')
    shortname = longpath
    if shortname == source_dir:
        shortname = os.path.basename(longpath)
    elif shortname.startswith(source_dir):
        shortname = os.path.relpath(shortname, source_dir)
    return shortname

def convertFolder(folder):
    language_code = config.get('Txt2USFM', 'language_code')
    if language_code + '_' in os.path.basename(folder):
        bookId = getBookId(folder)
        bookTitle = getBookTitle(folder, bookId)
        if bookId and bookTitle:
            convertBook(folder, bookId, bookTitle)   # converts the pieces in the current folder
            # profile.print_stats()
            appendToProjects(bookId, bookTitle)
        else:
            if not bookId:
                reportError("Unable to determine book ID in " + shortname(folder))
            if not bookTitle:
                reportError("Unable to determine book title in " + shortname(folder))
    else:
        reportError(f"Book folder name ({os.path.basename(folder)}) does not match language code ({language_code})")

# Returns file name for usfm file in current folder
def makeUsfmFilename(bookId):
    num = usfm_verses.verseCounts[bookId]['usfm_number']
    filename = num + '-' + bookId + '.usfm'
    return filename

def writeHeader(usfm, bookId, bookTitle):
    usfm.writeUsfm("id", bookId)
    usfm.writeUsfm("ide", "UTF-8")
    usfm.writeUsfm("h", bookTitle)
    usfm.writeUsfm("toc1", bookTitle)
    usfm.writeUsfm("toc2", bookTitle)
    usfm.writeUsfm("toc3", bookId.lower())
    usfm.writeUsfm("mt", bookTitle)

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

# Converts all the text files in the specified folder to USFM.
# profile = LineProfiler()
# @profile
def convertBook(folder, bookId, bookTitle):
    reportProgress(f"CONVERTING {shortname(folder)}")
    sys.stdout.flush()

    target_dir = config.get('Txt2USFM', 'target_dir')
    chapters = listChapters(folder)
    # Open output USFM file for writing.
    usfmPath = os.path.join(target_dir, makeUsfmFilename(bookId))
    usfm = usfmWriter.usfmWriter(usfmPath)
    writeHeader(usfm, bookId, bookTitle)

    for chap in chapters:
        chapterpath = os.path.join(folder, chap)
        chapterTitle = getChapterTitle(chapterpath)
        chunks = listChunks(chapterpath)
        for i in range(len(chunks)):
            filename = chunks[i] + ".txt"
            txtPath = os.path.join(chapterpath, filename)
            section = cleanupTextFile(txtPath, chap, makeVerseRange(chunks, i, bookId, int(chap)))
            section = convertSection(section, chapterTitle, i+1 >= len(chunks)).rstrip()
            usfm.writeStr('\n' + section)
    usfm.close()

# Converts the book or books contained in the specified folder
def convert(dir, target_dir):
    if isBookFolder(dir):
        convertFolder(dir)
    else:       # presumed to be a folder containing multiple books
        for directory in os.listdir(dir):
            folder = os.path.join(dir, directory)
            if isBookFolder(folder):
                convertFolder(folder)

# Processes each directory and its files one at a time
def main(app = None):
    global gui
    gui = app
    global config
    target_dir = config.get('Txt2USFM', 'target_dir')

    Path(target_dir).mkdir(exist_ok=True)
    global projectInfo
    projectInfo = ProjectInfo(target_dir, config.get('Txt2USFM', 'language_code'))
    projectInfo.useManifest()
    projectInfo.resetSources()
    convert(config.get('Txt2USFM', 'source_dir'), target_dir)
    projectInfo.save()
    reportStatus("\nDone.")
    if gui:
        gui.event_generate('<<ScriptEnd>>', when="tail")

if __name__ == "__main__":
    main()
