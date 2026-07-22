# -*- coding: utf-8 -*-
# Utility functions for detecting section titles, based on string content only.
# The following factors are useful in recognizing possible section titles:
#   Short phrases or sentences, especially if it has no sentence-ending punctuation.
#   No more than one sentence-final punctuation.
#   Title Case or ALL CAPS.
#   Parentheses or braces.

import re
import sentences
from usfm_utils import isCaseless

exclude_eol_checks = ['LEV 18:5','LEV 19:4',
    'MAT 15:31', 'LUK 2:11', 'LUK 17:32', 'JHN 19:19', 'ACT 16:20', 'COL 3:22', '2TI 4:18', 'REV 22:9', 'REV 22:20']

# The special Unicode characters are identified in sentences.py.
punct_re = re.compile(r'[()*+,./:;<=>!?@[\]^{|}~\u0964\u0965\u1361\u1362\u061F\u06D4]')

# Returns the number of punctuation characters in the string.
def nPunctuationChars(s):
    return len(punct_re.findall(s))

def percentTitleOrCaps(s):
    if s.istitle() or s.isupper():
        percent = 1.0
    else:
        n = 0
        words = s.split()
        for word in words:
            if sentences.isCapitalized(word) or word.isupper():
                n += 1
        percent = n / (len(words) if words else 1)
    return percent

# bphrase_re = re.compile(r'\{[\s]*([\w\- ]+)[\s]*\}')
# pphrase_re = re.compile(r'\([\s]*([\w\- ]+)[\s]*\)\s*$', re.MULTILINE)
pphrase_re = re.compile(r'\([^()\n\t]+\)\s*$', re.MULTILINE)

# Finds a probable parenthesized string in the line,
# at the required probability level based only on string characteristics.
# Returns "" if no probable parenthesized heading is found.
def find_parenthesized_heading(line, required_prob):
    pheading = ""
    for possible_hd in pphrase_re.finditer(line):
        possible_heading = possible_hd.group(0).strip()
        if prob_heading(possible_heading) >= required_prob:
            nextword = sentences.firstword(line[possible_hd.end():])
            if not nextword or (nextword and not nextword.islower()):
                pheading = possible_heading
                break
    return pheading

# Returns a probable heading at end of line,
# at the required probability level based only on string characteristics.
# Returns empty string if no probable heading is found at end of line.
def find_eol_heading(line, required_prob):
    candidate = ""
    sentence_starts = [pos for pos in sentences.nextstartpos(line)]
    if len(sentence_starts) > 0:
        startpos = sentence_starts[-1]
        if startpos > 0 and line[startpos-1] == '(':
            startpos -= 1
        candidate = line[startpos:]
        if prob_heading(candidate) < required_prob:
            candidate = ""
    return candidate

digit_re = re.compile(r'\d')
# Returns a probability of a given string being a section title, based on the available factors.
# Returns a number between 0.0 and 1.0.
def prob_heading(s):
    s = s.strip(' \n')
    if disqualified(s):
        prob = 0
    elif len(s) < 2 or quotes_re.search(s) or (sentences.sentenceCount(s) > 1 and not digit_re.search(s)):
        prob = 0.01
    else:
        caseless = isCaseless(sentences.firstword(s))
        if caseless:
            prob = 0.1
        else:
            if s.isupper():
                prob = 0.8
            else:
                percent = percentTitleOrCaps(s)
                diff = percent - _titlecase_threshold(s)
                if diff >= 0.0:
                    prob = 0.5
                    if percent >= 0.8:
                        prob = 0.75
                else:
                    prob = 0.04
        if s[0] == '(' and s[-1] == ')':
            prob += 0.15
        if digit_re.search(s) and ':' in s:
            prob -= 0.1
        if len(s) > 80:
            prob -= 0.002 * (len(s) - 80)
        if _wordcount(s) > 10:
            prob -= 0.005 * (_wordcount(s) - 10)
        prob -= 0.15 * s.count('\n')
        prob -= 0.03 * nPunctuationChars(s)
        if prob > 0.05 and s.endswith(','):
            prob = 0.05
        if prob > 0.1 and s.endswith(':'):
            prob = 0.1
        if sentences.endsSentence(s):
            prob -= 0.1
            prob -= 0.3 * (nPunctuationChars(s) - 1)
        if prob <= 0.01:
            prob = 0.01
    return prob

anyMarker_re = re.compile(r'\\[a-z]+[a-z1-5]* ?[0-9]*')
amen_re = re.compile(r'[AE]m[ei]+n', flags=re.IGNORECASE)
selah_re = re.compile(r'Selah', flags=re.IGNORECASE)
quotes_re = re.compile(r'["“‘‹«”›»]')
singleWordInParens_re = re.compile(r'\(\s*\w+\s*\)')

# Returns True if the string has any disqualifying characteristics.
def disqualified(s):
    disqual = (not s or\
               anyMarker_re.search(s) or s[0] == '\\' or\
               ((amen_re.search(s) or selah_re.search(s)) and _wordcount(s) == 1))
    return disqual

goodstart_re = re.compile(r'[\w\(]')

def _titlecase_threshold(s):
    if not s or len(s) < 2:
        adj = 0.99
    else:
        adj = 0.51
        if s[-1] in "'’,":
            adj = 0.99
        if ',' in s:
            adj += 0.16
        if len(s) > 80:
            adj += 0.01 * (len(s) - 80)
        if _wordcount(s) > 10:
            adj += 0.03 * (_wordcount(s) - 10)
        if s.startswith('(') and s.endswith(')') and s.count('(') == s.count(')') == 1:
            adj -= 0.03
        if not goodstart_re.match(s):
            adj += 0.18
        if ends := sentences.endsSentence(s):
            adj += 0.16
            if ends in "!?;":
                adj = 0.99
        else:
            firstword = sentences.firstword(s)
            if sentences.isCapitalized(firstword) or firstword.isupper():
                adj -= 0.24
        lastword = sentences.lastword(s)
        if sentences.isCapitalized(lastword) or lastword.isupper():
            adj -= 0.08
        if adj == 0.67:
            adj = 0.66
    return adj

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
