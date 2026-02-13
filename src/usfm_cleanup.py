# -*- coding: utf-8 -*-
# This program cleans up common issuss in USFM files.
# Backs up the .usfm files being modified.
# Outputs .usfm files of the same name in the same location.
#
# Moves standalone \p \m and \q markers which occur just before an \s# marker
#    to the next line after the \s# marker.
# Promote straight quotes to open and closed quotes. (optional)
# Capitalizes first word in sentences.

from configmanager import ToolsConfigManager
import re
import io
import os
import shutil
import sys
import substitutions
import quotes
import usfmReader
import sentences
import section_titles_new
from manifestyaml import ManifestYaml
from scripturebook import ScriptureBook
import usfm_utils
import usfmWriter
from datetime import date

gui = None
enable = [True]*9
'''
enable[1] to add space after periods, around parens, etc.
enable[2] to fix punctuation
enable[3] to promote double stright quotes
enable[4] to promote all straight quotes
enable[5] to capitalize sentences
enable[6] to remove \\s5 markers
enable[7] to mark section titles
enable[8] to fix chapter titles
'''
std_title = ""
nChanged = 0
aligned_usfm = False
needcaps = True
in_footnote = False
issuesFile = None
corrupt_file = False
saidwords = []
sourcebook = None

# Manages the state for a single usfm file. Used when converting by token.
# @TODO Move needcaps and in_footnote into the State object.
class State:
    def __init__(self):
        self.initBook()

    def initBook(self):
        self.bookId = ""
        self.strChapter = ""    # current chapter
        self.strVerse = ""      # current verse
        self.reference = ""
        self.source_id = ""
        self.currMarker = None
        self.prevMarker = None

    def addToken(self, token):
        if token.type == 'c':
            self.strChapter = token.value
            self.reference = self.bookId + " " + token.value
        elif token.type == 'v':
            self.strVerse = token.value
            self.reference = self.bookId + " " + self.strChapter + ":" + token.value
        elif token.type == 'id':
            self.bookId = token.value
            self.reference = token.value + " header/intro"

        self.prevMarker = self.currMarker
        self.currMarker = token.type

    def addLine(self, line):
        marker, value, remainder = usfm_utils.parseLine(line)
        match marker:
            case 'id':
                self.bookId = remainder[0:3].upper()
                self.reference = self.bookId + " header/intro"
            case 'c':
                self.strChapter = value
                self.reference = self.bookId + " " + value
            case 'v':
                self.strVerse = value
                self.reference = self.bookId + " " + self.strChapter + ":" + value

state = State()

def shortname(longpath):
    work_dir = getWorkDir()
    shortname = str(longpath)
    if shortname.startswith(work_dir):
        shortname = os.path.relpath(shortname, work_dir)
    return shortname

# Writes message to gui, stderr, and issues.txt.
def reportError(msg):
    reportToGui('<<ScriptMessage>>', msg)
    sys.stderr.write(msg + "\n")
    if issues := openIssuesFile():
        issues.write(msg + "\n")

# Sends a progress report to the GUI, and to stdout.
def reportProgress(msg):
    reportToGui('<<ScriptProgress>>', msg)
    print(msg)

# Sends a status message to the GUI, and to stdout.
def reportStatus(msg):
    reportToGui('<<ScriptMessage>>', msg)
    print(msg)

def reportToGui(event, msg):
    if gui:
        with gui.progress_lock:
            gui.progress = msg if not gui.progress else f"{gui.progress}\n{msg}"
        gui.event_generate(event, when="tail")

# If issues.txt file is not already open, opens it for writing.
# Overwrites existing issues.txt file, if any.
# Returns new file pointer.
def openIssuesFile():
    global issuesFile
    if not issuesFile:
        work_dir = getWorkDir()
        if os.path.isdir(work_dir):
            path = os.path.join(work_dir, "issues.txt")
            issuesFile = io.open(path, "tw", buffering=4096, encoding='utf-8', newline='\n')
            issuesFile.write(f"Issues detected by usfmCleanup, {date.today()}, {work_dir}\n-------------------\n")
    return issuesFile

# Returns information about the resource in the specified folder.
def identifyResource(dir):
    srcmy = ManifestYaml()
    errors = srcmy.load(dir)
    resource = dict()
    if not errors:
        resource['language_id'] = srcmy.getLanguageId()
        resource['resource_id'] = srcmy.getResourceId()
        resource['version'] = srcmy.getVersion()
    return resource

# Returns information about the resource in the specified folder, as a string.
def strResource(dir):
    if resource := identifyResource(dir):
        id = resource['language_id'] + "_" + resource['resource_id'] + " " + resource['version']
    else:
        id = ""
    return id

# Loads the source text for the current book if compare_dir is set.
# It parses a usfm file and stores verse text in a dict.
def load_source(fname):
    sourcedir = ToolsConfigManager().get('UsfmCleanup', 'compare_dir')
    if sourcedir:
        state.source_id = strResource(sourcedir)

        # Then parse the usfm for the current book.
        sourcepath = os.path.join(sourcedir, fname)
        if os.path.isfile(sourcepath):
            global sourcebook
            sourcebook = ScriptureBook(sourcepath)

# Sets the global saidwords list, assuming language_code is available.
def getSaidWords(work_dir):
    from projectinfo import ProjectInfo
    global saidwords
    pi = ProjectInfo(work_dir, ToolsConfigManager().get('UsfmCleanup', 'language_code'))
    saidwords = pi.getWords(mincount=4)

# This function is to be used only by unit tests.
def _setSaidWords(words):
    global saidwords
    saidwords = words

addp_re = re.compile(r'(\\s[1-5]? .*?\n)(\n*\\v )')

# Add \p between section heading and verse marker, where missing.
def usfm_add_p(str):
    newstr = ""
    found = addp_re.search(str)
    while found:
        newstr += str[0:found.start()] + found.group(1) + "\\p\n" + found.group(2)
        str = str[found.end():]
        found = addp_re.search(str)
    newstr += str
    return newstr

#  Move paragraph marker before section marker to follow the section marker
movepq_re = re.compile(r'\n(\\[pqm][i1-4]? *)\n+(\\s[1-5]? .*?)\n', flags=re.DOTALL)

# Moves standalone \p \m and \q markers which occur just before an \s# marker
#    to the next line after the \s# marker.
def usfm_move_pq(str):
    newstr = ""
    found = movepq_re.search(str)
    while found:
        newstr += str[0:found.start()] + '\n' + found.group(2) + '\n' + found.group(1) + '\n'
        str = str[found.end():]
        found = movepq_re.search(str)
    newstr += str
    return newstr

# losepq_re = re.compile(r'\\[pqm][i1-9]? *\n*(\\[^v])')
losepq_re = re.compile(r'\\[pqm][i1-9]? *\n*(\\[a-z][a-z1-5]*\*?)')

# Remove paragraph markers not followed by verse marker or \s5 or \rem.
# Other markers that follow a paragraph marker invalidate the paragraph marker.
def usfm_remove_pq(str):
    newstr = ""
    found = losepq_re.search(str)
    while found:
        if found.group(1) not in {'\\v', '\\rem', '\\s5'}:
            newstr += str[:found.start()] + found.group(1)
        else:
            newstr += str[:found.end()]
        str = str[found.end():]
        found = losepq_re.search(str)
    newstr += str
    return newstr

s5_re = re.compile(r'\n\\s5 *?\n', flags=re.UNICODE+re.DOTALL)

# Removes lines that contain only an \s5 marker (w possible trailing spaces)
def usfm_remove_s5(str):
    newstr = ""
    found = s5_re.search(str)
    while found:
        newstr += str[:found.start()] + "\n"
        str = str[found.end():]
        found = s5_re.search(str)
    newstr += str
    return newstr

# Finds \toc, \h and \mt lines, and changes the title on those lines to title case.
def fix_booktitles_x(str, compiled_expression):
    pos = 0
    title_line = compiled_expression.search(str, pos)
    while title_line:
        pos = title_line.start()
        title = title_line.group(2)
        title = title.rstrip(". ")
        title = " ".join(title.split())  # eliminates consecutive spaces and trailing white space
        if not title.istitle():     # not title case already
            title = title.title().replace("Iii", 'III')
            title = title.replace("Ii", 'II')
        str = str[:pos] + title_line.group(1) + title + str[title_line.end()-1:]
        pos += 5
        title_line = compiled_expression.search(str, pos)
    return str

# Finds \toc, \h and \mt lines, and changes the title on those lines to title case.
def fix_booktitles(str):
    str = fix_booktitles_x(str, re.compile(r'(\\toc[12] )([^\n]+\n)'))
    str = fix_booktitles_x(str, re.compile(r'(\\h )([^\n]+\n)'))
    str = fix_booktitles_x(str, re.compile(r'(\\mt1? )([^\n]+\n)'))
    return str

spacey3_re = re.compile(r'\\v [0-9\-]+ +([\(\[\'"«“‘])\s')    # verse starts with free floating punctuation
jammedleftparen_re = re.compile(r'[^\s][\(\[\{]')
jammedrightparen_re = re.compile(r'[\)\]\}]\w')

# 1. Replaces substrings from substitutions module
# 2. Reduces double periods to single.
# 3. Fixes free floating punctuation after verse marker.
# 4. Adds space before left paren/bracket where needed.
def fix_punctuation(str):
    for pair in substitutions.subs:
        str = str.replace(pair[0], pair[1])
    pos = str.find("..", 0)
    while pos >= 0:
        if pos != str.find("...", pos):
            str = str[:pos] + str[pos+1:]
        pos = str.find("..", pos+2)
    bad = spacey3_re.search(str)
    while bad:
        pos = bad.end()
        str = str[:pos-1] + str[pos:]
        bad = spacey3_re.search(str, pos)
    bad = jammedleftparen_re.search(str)
    while bad:
        pos = bad.start() + 1
        str = str[:pos] + ' ' + str[pos:]
        bad = jammedleftparen_re.search(str)
    bad = jammedrightparen_re.search(str)
    while bad:
        pos = bad.start() + 1
        str = str[:pos] + ' ' + str[pos:]
        bad = jammedrightparen_re.search(str)
    return str

# spacing_list is a list of compiled expressions where a space needs to be inserted
# after the first matched character.
spacing_list = [re.compile(r'[\.,;:)\]][\w]'),
                re.compile(r'[^\s][(\[]') ]

# Adds spaces where needed. spacing_list controls what happens.
# spacing_list may need to be customized for every language.
def add_spaces(s):
    for sub_re in spacing_list:
        found = sub_re.search(s, 0)
        while found:
            pos = found.start()
            second = pos+1
            if s[pos] not in ".,:" or not s[second].isdigit() or (pos>0 and not s[pos-1].isdigit()):
                s = s[:second] + ' ' + s[second:]
            found = sub_re.search(s, second)
    return s

# Rewrites file and returns True if any changes are made.
def convert_wholefile(path):
    global aligned_usfm
    global corrupt_file

    with io.open(path, "tr", encoding="utf-8-sig") as input:
        try:
            alltext = input.read()
            corrupt_file = (len(alltext) < 100)
            if corrupt_file:
                reportError("File is truncated: " + shortname(path))
        except UnicodeDecodeError as e:
            reportError("File appears to not be UTF-8: " + shortname(path))
            reportError(str(e))    # 0x92 is Windows encoding for right single quote mark; 0x92 is invalid in UTF-8.
            corrupt_file = True
    if corrupt_file:
        return False

    origtext = alltext
    aligned_usfm = ("lemma=" in alltext)
    changed = False

    if enable[6]:
        alltext = usfm_remove_s5(alltext)
    alltext = usfm_move_pq(alltext)
    alltext = usfm_remove_pq(alltext)
    alltext = usfm_add_p(alltext)
    alltext = fix_booktitles(alltext)
    if not aligned_usfm:
        if enable[2]:
            alltext = fix_punctuation(alltext)
    if alltext != origtext:
        with io.open(path, "tw", buffering=1, encoding='utf-8', newline='\n') as output:
            output.write(alltext)
        changed = True
    return changed

# Returns the position of the closing quote matching the open quote at line[pos].
# @param all means consider straight single and double quotes
# @param double means consider straight double quotes
# If neither all nor double are set, only find match for curly quotes.
def find_matching_closequote(line: str, pos: int, all, double):
    closepos = -1
    quote = line[pos] if pos >= 0 else ''
    if quotes.is_open(quote):
        opens = 1
        closequote = quotes.matechar(quote)
        for i in range(pos+1, len(line)):
            if line[i] == quote:
                opens += 1
            elif line[i] == closequote:
                opens -= 1
            if opens == 0:
                closepos = i
                break
    elif quotes.is_straight(quote, all):
        closepos = line.find(quote, pos+1)
        for i in range(pos, closepos-1): # exclude straight pairs which have a directional quote between them
            if line[i] in '«“‘»”’':
                closepos = -1
                break
    return closepos

# Returns the position of the open quote matching the closed quote at line[pos].
# @param singles means consider straight single quotes
# Returns -1 if no match, or if line[pos] is not a quote mark.
def find_matching_openquote(line: str, pos: int, singles):
    openpos = -1
    quote = line[pos] if 0 < pos < len(line) else ''
    if quotes.is_closed(quote):
        closes = 1
        openquote = quotes.matechar(quote)
        for i in range(pos-1, -1, -1):
            if line[i] == quote:
                closes += 1
            elif line[i] == openquote:
                closes -= 1
            if closes == 0:
                openpos = i
                break
    elif quotes.is_straight(quote, singles):
        openpos = line.rfind(quote, 0, pos)
        for i in range(openpos, pos-1): # exclude straight pairs which have a directional quote between them
            if line[i] in '«“‘»”’':
                openpos = -1
                break
    return openpos

q1_re = re.compile(r'(\w+)[.?!;:,](["\'«“‘’”»])\w')    # adjacent punctuation where second char is a quote mark
q2_re = re.compile(r'(\w+)[.?!;:,](["«“‘’”»])\w')

# Finds sequences of phrase-ending punctuation followed by a quote,
#   adjacent to word-forming characters on both sides.
# Locates matching quote in the same line.
# Inserts space before or after the quote, as appropriate.
# Returns line, including any changes made.
def change_quote_medial(line, singles):
    pos = 0
    quotemedial_re = q1_re if singles else q2_re

    bad = quotemedial_re.search(line)
    while bad:
        pos = bad.end(1) + 1
        if bad.group(1) in saidwords and (quotes.is_straight(line[pos], singles) or quotes.is_open(line[pos])):
            line = line[:pos] + ' ' + line[pos:]
        else:
            matepos = find_matching_openquote(line, pos, singles)
            if 0 <= matepos < pos:
                line = line[:pos+1] + ' ' + line[pos+1:]
            else:
                matepos = find_matching_closequote(line, pos, singles, True)
                if matepos > pos:
                    line = line[:pos] + ' ' + line[pos:]
        bad = quotemedial_re.search(line)
        if bad and bad.start() <= pos:
            break
    return line

# Returns a list of (openpos, closepos) tuples, each of which represents
# the positions of a matching pair of quotes in the given string.
def pair_up_quotes(line, singles):
    double = True
    if line.count('"') % 2 == 1:
        singles = double = False
    if singles and line.count("'") % 2 == 1:
        singles = False

    pairs = []
    for i in range(len(line)-1, 0, -1):
        if i not in [pair[0] for pair in pairs]:
            if line[i] == '"' and not double:   # disregard " if odd number of them
                continue
            openpos = find_matching_openquote(line, i, singles)
            if openpos >= 0:
                pairs.append((openpos, i))
    return pairs

said_re = re.compile(r'(\w+)[,:]? ["\'«“‘]( )')

# Removes space on right side of quote if preceded by a "said" word.
def fix_saids(line):
    saidquote = said_re.search(line)
    while saidquote:
        if saidquote.group(1) in saidwords:
            pos = saidquote.start(2)
            line = line[0:pos] + line[pos+1:]
        else:
            pos = saidquote.end()
        saidquote = said_re.search(line, pos)
    return line

quotefloat_re = re.compile(r'(^|\s)(["\'«“‘’”»])(\s|$)')

# Removes space on right side of quote if preceded by a "said" word.
# Removes space on one side of floating quotes if there are matching quotes.
# Returns the line including any changes made.
def change_floating_quotes(line, all):
    if quotefloat_re.search(line):    # if there exist any floating quotes in this line
        line = fix_saids(line)
        quotepairs = pair_up_quotes(line, all)
        closepositions = [p[1] for p in quotepairs]
        openpositions = [p[0] for p in quotepairs]
        if quotes := closepositions + openpositions:
            quotes.sort(reverse=True)
            for pos in quotes:
                if pos in closepositions:
                    while pos > 0 and line[pos-1] == ' ':
                        line = line[0:pos-1] + line[pos:]
                        pos -= 1
                elif pos in openpositions:
                    while len(line) > pos+1 and line[pos+1] == ' ':
                        line = line[0:pos+1] + line[pos+2:]
    return line

def find_section_heading(line, chap, verse, prevline, sentenceended):
    pheading = ""
    if verse == 0 or prevline.strip() == '' or sentenceended:
        if section_titles_new.prob_heading(line) >= 0.1:
            pheading = line.lstrip()
    if not pheading and sourcebook and sourcebook.has_section(chap, verse):
        if not pheading and section_titles_new.prob_heading(line) >= 0.1:
            pheading = line.lstrip()
        if not pheading:
            pheading = section_titles_new.find_parenthesized_heading(line, 0.249)
        if not pheading and sentences.sentenceCount(line) > 1:
            if not state or state.reference not in section_titles_new.exclude_eol_checks:
                pheading = section_titles_new.find_eol_heading(line, 0.100)
    return pheading

chap_re = re.compile(r'\\c +([0-9]+)')
verse_re = re.compile(r'\\v +([0-9]+)')
section_re = re.compile(r'\\s[1-4]? +(.+)$')

# Called for every line in the file, if section titles fixes are enabled.
# If the specified line is a section heading, returns (True, line), the line being modified.
# Line modification consists of prepending "\s " and possibly inserting newline before/after heading.
# Otherwise, returns (False, line), the line being unchanged.
def mark_sections(line):
    if not hasattr(mark_sections, "prevline") or line.startswith("\\id "):
        mark_sections.prevline = "xx"
        mark_sections.chapter = 0
        mark_sections.verse = 0
        mark_sections.sentenceended = True
        mark_sections.lasttitleverse = 0

    changed = False
    if c := chap_re.search(line):
        mark_sections.chapter = int(c.group(1))
        mark_sections.verse = 0
        mark_sections.lasttitleverse = -1
    if v := verse_re.search(line):
        mark_sections.verse = int(v.group(1))
    elif section_re.match(line):
        mark_sections.lasttitleverse = mark_sections.verse
        origlen = len(line)
        line = line.rstrip(". \\।\n")  # strip trailing spaces, periods and danda
        changed = (len(line) < origlen)

    pheading = ""
    if mark_sections.chapter > 0 and mark_sections.lasttitleverse != mark_sections.verse:
        pheading = find_section_heading(line, mark_sections.chapter, mark_sections.verse, mark_sections.prevline, mark_sections.sentenceended)
    if pheading:
        mark_sections.lasttitleverse = mark_sections.verse
        startpos = line.find(pheading)
        endpos = startpos + len(pheading)
        assert startpos >= 0 and endpos <= len(line)
        pheading = pheading.strip('().\u0964\u0965\u1362\u06D4 \n')
        line = section_titles_new.insert_heading(line[0:startpos].rstrip('( '), pheading, line[endpos:])
        changed = True

    mark_sections.prevline = line
    mark_sections.sentenceended = changed or (sentences.endsSentence(line, checkquotes=True) != '')
    return (changed, line)

vperiod_re = re.compile(r'\\v +[\d\-]+([).])([^\s]?)')

# Removed periods or right parens after verse numbers.
def remove_periods(line):
    changed = False
    vperiod = vperiod_re.search(line)
    while vperiod:
        elide = vperiod.end(1)
        if vperiod.group(2):   # means the next character is not a space
            sp = ' '
        else:
            sp = ''
        line = line[0:elide-1] + sp + line[elide:]
        changed = True
        vperiod = vperiod_re.search(line, vperiod.end()-1)
    return (changed, line)

# Iterator, returns the next block in the file.
# Usually, a block is a single line.
# If multiple lines of pure text occur together, they are returned as a single block.
def nextblock(path):
    with io.open(path, "tr", encoding="utf-8-sig") as input:
        lines = input.readlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        marker, value, remainder = usfm_utils.parseLine(line)
        if marker == '' and not line.isspace():
            block = line
            i += 1
            while i < len(lines):
                nextline = lines[i]
                nextmarker, nextvalue, nextremainder = usfm_utils.parseLine(nextline)
                if nextmarker == '':
                    block += nextline
                    i += 1
                else:
                    break
            yield block
        else:
            yield line
            i += 1

# Rewrites the file line by line, making changes to individual lines
# Returns True if any changes are made
def convert_by_line(inputpath, path):
    state.initBook()
    output = usfmWriter.usfmWriter(path)
    changedfile = False
    changed3 = False

    for block in nextblock(inputpath):  # @TODO use usfm_utils.nextblock() once it is tested
        state.addLine(block)
        if enable[7]:
            (changed3, block) = mark_sections(block)
        (changed4, block) = remove_periods(block)
        if changed3 or changed4:
            changedfile = True
        output.writeStr(block)
    output.close()
    return (changedfile)

def takeFootnote(key, value, usfm):
    global in_footnote
    if key in {"f", "fr", "ft", "fp", "fe", "rq"}:
        in_footnote = True
    elif key in {"f*", "fe*", "rq*"}:
        in_footnote = False
    usfm.writeUsfm(key, value)

# Capitalizes the first word of each sentence in the string.
# Capitalizes the first word in the string if needcaps is True.
# Returns the string with changes as needed.
# As a side effect, sets the global needcaps variable.
def capitalizeAsNeeded(s):
    global needcaps
    s = sentences.capitalize(s, needcaps)
    needcaps = (sentences.endsSentence(s, checkquotes = True) != '')
    return s

cl_pattern = re.compile(r'(.*?)(\d+)(.*)')

def fix_chapter_label(label, schapter):
    global std_title
    lab = cl_pattern.match(label.strip())
    if lab:
        part1 = std_title + " " if len(lab.group(1)) > 0 else ""
        part2 = schapter if lab.group(2).isascii() else lab.group(2)
        if len(lab.group(3)) > 0 and len(lab.group(1)) > 0:
            part3 = lab.group(3)
        else:
            part3 = " " + std_title if len(lab.group(3)) > 0 else ""
        label = f"{part1}{part2}{part3}"
    return label

# May change the label.
# Writes the tag and label to the usfm file.
def takeCL(label, usfm):
    origlabel = label
    if enable[8]:
        label = fix_chapter_label(label, state.strChapter)
    usfm.writeUsfm("cl", label)
    return (label != origlabel)

def takeText(s, usfm):
    origstr = s
    global in_footnote
    if state.prevMarker == 'v' and s.startswith(state.strVerse):
        vlen = len(state.strVerse)
        if vlen < len(s) and s[vlen] in '.)':   # period or paren is stuck to verse number
            vlen += 1
        s = s[vlen:].lstrip()
    s = add_spaces(s)
    if enable[5] and not in_footnote:
        s = capitalizeAsNeeded(s)
    s = change_quote_medial(s, enable[4])
    s = change_floating_quotes(s, enable[4])
    if enable[4]:   # promote all straight quotes
        s = quotes.promoteQuotes(s)
    elif enable[3]:
        s = quotes.promoteDoubleQuotes(s)
    if state.prevMarker == 'text':
        usfm.newline()
    s = s.rstrip(' ')
    usfm.writeStr(s)
    return (s != origstr)

def take(token: usfmReader.Token, usfm):
    state.addToken(token)

    changed = False
    if token.type == 'text':
        changed = takeText(token.value, usfm)
    elif token.type == 'cl':
        if takeCL(token.value, usfm):
            changed = True
    elif token.isFootnote():
        takeFootnote(token.type, token.value, usfm)
    else:
        usfm.writeUsfm(token.type, token.value)
    return 1 if changed else 0

# Parses and rewrites the usfm file with corrections to capitalization
# and/or chapter titles.
# Returns True if any changes are made.
def convert_by_token(path):
    changes = 0
    with io.open(path, "tr", 1, encoding="utf-8-sig") as input:
        contents = input.read(-1)
    state.initBook()
    usfm = usfmWriter.usfmWriter(path)
    # usfm.setInlineTags({"f", "ft", "f*", "rq", "rq*", "fe", "fe*", "fr", "fk", "fq", "fqa", "fqa*"})
    global needcaps
    needcaps = True
    tokens = usfmReader.parseString(contents)
    for token in tokens:
        changes += take(token, usfm)
    usfm.close()
    # sys.stdout.write(f"{changes} strings in {path} were changed by convert_by_token()\n")
    return (changes > 0)

# Corrects issues in the USFM file
def convertFile(path):
    global nChanged
    global corrupt_file
    corrupt_file = False
    load_source(os.path.basename(path))
    reportProgress(f"Checking {shortname(path)}")
    sys.stdout.flush()

    tmppath = path + ".tmp"
    if os.path.exists(tmppath):
        os.remove(tmppath)
    os.rename(path, tmppath)    # to preserve time stamp
    shutil.copyfile(tmppath, path)

    changed1 = convert_wholefile(path)
    changed2 = changed4 = False
    if not corrupt_file:
        changed2 = convert_by_line(tmppath, path)  # marks section titles, etc.
        if enable[7] and changed2:   # sections may have been added
            convert_wholefile(path)   # rerun
        changed4 = False
        if enable[5] or enable[8]:   # capitalization or chapter titles
            changed4 = convert_by_token(path)

    if changed1 or changed2 or changed4:
        nChanged += 1
        reportStatus(f"Changed {shortname(path)}")
        sys.stdout.flush()
        bakpath = path + ".orig"
        if not os.path.isfile(bakpath):
            os.rename(tmppath, bakpath)
        else:
            os.remove(tmppath)
    else:       # no changes to file
        os.remove(path)
        os.rename(tmppath, path)

# Recursive routine to convert all files under the specified folder
def convertFolder(folder):
    if aligned_usfm:
        return
    for entry in os.listdir(folder):
        if entry[0] != '.':
            path = os.path.join(folder, entry)
            if os.path.isdir(path):
                convertFolder(path)
            elif entry.lower().endswith("sfm"):
                convertFile(path)

# For unit testing only - test fix_chapter_title()
def set_std_title(title):
    global std_title
    std_title = title

# Temporary function, until all references to "source_dir" are removed.
def getWorkDir():
    config = ToolsConfigManager()
    workdir = config.get('UsfmCleanup', 'work_dir')
    if not workdir:
        workdir = config.get('UsfmCleanup', 'source_dir')    # the old name
    return workdir

def main(app = None):
    global gui
    global std_title
    global nChanged
    nChanged = 0
    gui = app
    config = ToolsConfigManager()

    std_title = config.get('UsfmCleanup', 'standard_chapter_title')
    work_dir = getWorkDir()
    if work_dir:
        getSaidWords(work_dir)
        for i in range(1, len(enable)):
            enable[i] = config.getboolean('UsfmCleanup', 'enable'+str(i))
        file = config.get('UsfmCleanup', 'filename')
        if file:
            path = os.path.join(work_dir, file)
            if os.path.isfile(path):
                convertFile(path)
            else:
                reportError(f"No such file: {path}")
        else:
            convertFolder(work_dir)
        reportStatus("\nDone. Changed " + str(nChanged) + " files.")

    if aligned_usfm:
        reportError("Sorry, cannot deal with aligned USFM.")
    if gui:
        gui.event_generate('<<ScriptEnd>>', when="tail")

# Processes all .usfm files in specified directory, one at a time
if __name__ == "__main__":
    main()
