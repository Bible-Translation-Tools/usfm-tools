# -*- coding: utf-8 -*-
# Utility functions for detecting section titles.
# The following factors are useful in recognizing possible section titles:
#   Do we expect headings at all.
#   Short phrases or sentences, especially if it has no sentence-ending punctuation.
#   No more than one sentence-final punctuation.
#   On a line by itself (as opposed to appended to verse text).
#   Not split over two lines.
#   Title Case or ALL CAPS.
#   Parentheses or braces.
#   Distance from previous section heading.
#   At the beginning or end of a chunk.
#   More likely before verse 1 of a chapter.

import re
import sentences

exclude_eol_checks = ['LEV 18:5','LEV 19:4',
    'MAT 15:31', 'LUK 2:11', 'JHN 19:19', 'ACT 16:20', 'COL 3:22', '2TI 4:18', 'REV 22:9', 'REV 22:20']

expect_allcaps = True
expect_titlecase = True
expect_parens = True

# # Sets a global variable that informs this module whether to give special
# # weight to strings that are ALL CAPS.
# def consider_allcaps(consider=True):
#     global expect_allcaps
#     expect_allcaps = consider

# # Sets a global variable that informs this module whether to give special
# # weight to strings that are Title Case.
# def consider_titlecase(consider=True):
#     global expect_titlecase
#     expect_titlecase = consider

# # Sets a global variable that informs this module whether to give special
# # weight to strings that are in surrounded by parentheses.
# def consider_parens(consider=True):
#     global expect_parens
#     expect_parens = consider

startword_re = re.compile(r'[\w "‘“\'\()]')

# Intended for single words, and may not work correctly for phrases.
# Differs from str.istitle() in how apostrophes are treated.
# Considered numbers to be uncapitalized words.
# istitle("Paul's") returns False.
# isCapitalized("Paul's") returns True.
# isCapitalized("E'Besusaida") returns True.
# Hyphenated words like Two-sided and Two-Sided return True.
def isCapitalized(word):
    if not word or not startword_re.match(word):
        result = False
    else:
        strings = re.split("['’-]", word)
        result = strings[0].istitle()
        if result:
            for i in range(1,len(strings)):
                if not (strings[i].islower() or strings[i].istitle()):
                    result = False
    return result

# Returns the fraction of words in the string which are title case.
# Consider numbers to be uncapitalized.
def percentTitlecase(s):
    n = 0
    words = s.split()
    for word in words:
        if isCapitalized(word):
            n += 1
    percent = n / (len(words) if words else 1)
    return percent

# bphrase_re = re.compile(r'\{[\s]*([\w\- ]+)[\s]*\}')
pphrase_re = re.compile(r'\([\s]*([\w\- ]+)[\s]*\)\s*$', re.MULTILINE)

# Returns that portion of the specified line that is most likely a heading.
# A single word in parentheses fails the test.
# Returns None if no parenthesized heading is found.
def find_parenthesized_heading(line):
    pheading = None
    for possible_hd in pphrase_re.finditer(line):
        possible_heading = possible_hd.group(0).strip()
        if is_heading(possible_heading):
            nextword = sentences.firstword(line[possible_hd.end():])
            if not nextword or (nextword and not nextword.islower()):
                pheading = possible_heading
                break
    return pheading

# Returns likely heading at end of line.
# Returns None if no heading is found at end of line.
def find_eol_heading(line):
    candidate = None
    sentence_starts = [pos for pos in sentences.nextstartpos(line)]
    if len(sentence_starts) > 0:
        startpos = sentence_starts[-1]
        if startpos > 0 and line[startpos-1] == '(':
            startpos -= 1
        if is_heading(line[startpos:]):    # last "sentence" in the line
            candidate = line[startpos:]
    return candidate

# Returns True if the string looks like a section heading.
# Any backslash markers or quote marks in the string disqualify it.
# See comments at the top of this file for factors that are considered.
# The threshold parameter specifies the minimum percentage of capitalized words
#    in a string that is partly title case.
def is_heading(s):
    s = s.strip(' \n')
    threshold = _titlecase_threshold(s)
    return qualifies(s, threshold)

def is_possible_heading(s):
    s = s.strip(' \n')
    threshold = _titlecase_threshold(s) - 0.21
    if threshold < 0.45:
        threshold = 0.45
    return qualifies(s, threshold)

anyMarker_re = re.compile(r'\\[a-z]+[a-z1-5]* ?[0-9]*')
amen_re = re.compile(r'[AE][mM][eiEI]+[nN]')
selah_re = re.compile(r'Selah')
forbidden_re = re.compile(r'["“‘‹«”›»]')
singleWordInParens_re = re.compile(r'\(\s*\w+\s*\)')

# Returns True if the string qualifies as a section heading given the specified threshold of capitalized words.
def qualifies(s, threshold):
    confirmed = False
    firstword = sentences.firstword(s)
    # Initial qualification
    possible = (threshold <= 1 and not '\n' in s and\
                not anyMarker_re.search(s) and not amen_re.search(s) and not selah_re.search(s) and\
                (firstword.isupper() or isCapitalized(firstword)) and\
                # not quotes.partialQuote(s) and\
                not forbidden_re.search(s) and\
                not singleWordInParens_re.match(s) and\
                sentences.sentenceCount(s) == 1)
    if possible and not confirmed and expect_allcaps:
        confirmed = s.isupper()
    if possible and not confirmed and expect_titlecase:
        confirmed = (percentTitlecase(s) >= threshold)
    if possible and not confirmed and expect_parens:
        confirmed = s[0] == '(' and s[-1] == ')' and (s.isupper() or percentTitlecase(s[1:-1]) >= threshold)
    return confirmed

goodstart_re = re.compile(r'[\w\(]')
# Calculates the Title Case threshold (percentage of words that must be capitalized)
# based on characteristics of the string.
# Assumes that the specified string has already been stripped of leading and trailing white space.
def _titlecase_threshold(s):
    if not s or len(s) < 5:
        adj = 2
    else:
        adj = 0.51
        if s[-1] in "'’,":
            adj = 1.2
        if ',' in s:
            adj += 0.16
        if len(s) > 40:
            adj += 0.01 * (len(s) - 40)
        if s.startswith('(') and s.endswith(')'):
            adj -= 0.03
        if not goodstart_re.match(s):
            adj += 0.18
        for i in range(len(s)-3,len(s)):
            if s[i] in ".\u0964\u0965\u1361\u1362!?;":    # sentence ending punctuation
                adj += 0.16
                if _wordcount(s) == 1:
                    adj = 1.01
                elif s[i] in "!?;":
                    adj = 0.99
        lastword = _lastword(s)
        if not isCapitalized(lastword) and not lastword.isupper():
            adj += 0.24
    return adj

def _lastword(s):
    words = s.split()
    return words[-1] if words else ''

def _wordcount(s):
    return len(s.split())

# Inserts the section heading between two parts, including newlines.
def insert_heading(preheading, heading, postheading):
    if preheading == None or heading == None or postheading == None:
        return ''
    preheading = preheading.rstrip()
    if heading:
        heading = '\\s ' + heading.strip() + '\n\\p\n'
        if preheading:
            preheading += '\n'
    postheading = postheading.lstrip()
    while postheading.startswith("\\p"):
        postheading = postheading[2:].lstrip()
    return preheading + heading + postheading.lstrip()
