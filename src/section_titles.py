# -*- coding: utf-8 -*-
# Utility functions for detecting section titles.

import re
import sentences

allcaps = True
titlecase = True
parens = True

def consider_allcaps(consider=True):
    global allcaps
    allcaps = consider

def consider_titlecase(consider=True):
    global titlecase
    titlecase = consider

def consider_parens(consider=True):
    global parens
    parens = consider

# Returns the fraction of words in the string which are title case.
# But returns 0 if the first word is not title case.
def percentTitlecase(str):
    percent = 1 if str.istitle() else 0
    if percent != 1:
        n = 0
        words = str.split()
        if words and words[0].istitle():
            for word in words:
                if word.istitle():
                    n += 1
            percent = n / len(words)
    return percent

pphrase_re = re.compile(r'(\([\w\- ]+\))')
# Returns a number indicating position of the first parenthesized heading in the line
# 0 means no heading found
def has_parenthesized_heading(line):
    n = posn = 0
    for possible_hd in pphrase_re.finditer(line):
        n += 1
        str = possible_hd.group(1).strip("()")
        if str.isupper() or percentTitlecase(str) >= 0.5:
        # if str.isupper() or (" " in str and percentTitlecase(str) >= 0.5): # exclude single-word non-headings in parens
            posn = n
            break
    return posn

anyMarker_re = re.compile(r'\\[a-z]+[a-z1-5]* ?[0-9]*')

# Returns True if the string qualifies as a section heading.
# Any USFM markers in the string disqualify it.
# Any quotation marks disqualify it.
# No more than one sentence.
def is_heading(str):
    confirmed = False
    str = str.strip()
    possible = (len(str) > 3 and not anyMarker_re.search(str) and sentences.sentenceCount(str) == 1)
    if possible and parens:
        confirmed = str[0] == '(' and str[-1] == ')' and has_parenthesized_heading(str)
    if possible and not confirmed and allcaps:
        confirmed = str.isupper()
    if possible and not confirmed and titlecase:
        confirmed = (percentTitlecase(str) > 0.5)
    return confirmed
