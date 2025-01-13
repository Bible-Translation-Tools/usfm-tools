# -*- coding: utf-8 -*-
# Utility functions for detecting section titles.

import re
import sentences
import quotes

expect_allcaps = True
expect_titlecase = True
expect_parens = True

def consider_allcaps(consider=True):
    global expect_allcaps
    expect_allcaps = consider

def consider_titlecase(consider=True):
    global expect_titlecase
    expect_titlecase = consider

def consider_parens(consider=True):
    global expect_parens
    expect_parens = consider

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

pphrase_re = re.compile(r'\(([\w\- ]+)\)')

# Returns a number indicating position of the first parenthesized heading in the line
# 0 means no heading found
# 2 means the heading is found in the 2nd parenthesized phrase
# def has_parenthesized_heading(line):
#     n = posn = 0
#     for possible_hd in pphrase_re.finditer(line):
#         n += 1
#         str = possible_hd.group(0).strip("() ")
#         if str.isupper() or percentTitlecase(str) >= 0.5:
#         # if str.isupper() or (" " in str and percentTitlecase(str) >= 0.5): # exclude single-word non-headings in parens
#             posn = n
#             break
#     return posn

# Returns substring of line that is a parenthesized heading.
# Returns None if no parenthesized heading is found.
def find_parenthesized_heading(line):
    pheading = None
    for possible_hd in pphrase_re.finditer(line):
        possible_heading = possible_hd.group(0)
        if is_heading(possible_heading.strip('()'), threshold = 0.5):
            pheading = possible_heading
            break
    return pheading

anyMarker_re = re.compile(r'\\[a-z]+[a-z1-5]* ?[0-9]*')

# Returns True if the string looks like a section heading.
# Any USFM markers or quote marks in the string disqualify it.
# No more than one sentence.
def is_heading(str, threshold=0.51):
    confirmed = False
    str = str.strip(' ')
    # Initial qualification
    possible = (len(str) > 3 and not anyMarker_re.search(str) and sentences.sentenceCount(str) == 1) and\
                not '\n' in str and quotes.quotepos(str) == -1
    if possible and not confirmed and expect_allcaps:
        confirmed = str.isupper()
    if possible and not confirmed and expect_titlecase:
        confirmed = (percentTitlecase(str) >= threshold)
    if possible and expect_parens:
        threshold = 0.5
        confirmed = str[0] == '(' and str[-1] == ')' and (str.isupper() or percentTitlecase(str[1:-1]) >= threshold)
    return confirmed
