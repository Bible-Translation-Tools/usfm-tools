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
import quotes

expect_allcaps = True
expect_titlecase = True
expect_parens = True

# Sets a global variable that informs this module whether to give special
# weight to strings that are ALL CAPS.
def consider_allcaps(consider=True):
    global expect_allcaps
    expect_allcaps = consider

# Sets a global variable that informs this module whether to give special
# weight to strings that are Title Case.
def consider_titlecase(consider=True):
    global expect_titlecase
    expect_titlecase = consider

# Sets a global variable that informs this module whether to give special
# weight to strings that are in surrounded by parentheses.
def consider_parens(consider=True):
    global expect_parens
    expect_parens = consider

# Differs from str.istitle() in how apostrophes are treated.
# istitle("Paul's") returns False.
# isCapitalized("Paul's") returns True.
def isCapitalized(word):
    result = word.istitle()
    if not result:
        result = word.replace("'", "").istitle()
    return result

# Returns the fraction of words in the string which are title case.
# Words containing quotation marks are considered non-title case.
# But returns 0 if the first word is not capitalized.
def percentTitlecase(str):
    percent = 1 if str.istitle() else 0
    if percent != 1:
        n = 0
        words = str.split()
        if words and isCapitalized(words[0]):
            for word in words:
                if isCapitalized(word):
                    n += 1
            percent = n / len(words)
    return percent

# Returns True if the first and last word in the string are title case.
# def firstAndLastTitlecase(str):
    # words = str.split()
    # return (words[0].istitle() and words[-1].istitle()) if words else False

# Returns that portion of the specified line that is most likely a heading,
# based characteristics of the text between the start and end characters.
# Typically a parenthesized heading.
# Returns the parentheses and everything in between.
# Returns None if no parenthesized heading is found.
# def find_parenthesized_heading(line, start='(', end =')'):
#     pheading = None
#     pattern = "\\" + start + "[\s]*([\w\- ]+)[\s]*" + "\\" + end
#     for possible_hd in re.finditer(pattern, line):
#         possible = possible_hd.group(0)
#         stripchars = start + end + " \n"
#         if is_heading(possible.strip(stripchars)):
#             pheading = possible
#             break
#     return pheading

pphrase_re = re.compile(r'\([\s]*([\w\- ]+)[\s]*\)')
# bphrase_re = re.compile(r'\{[\s]*([\w\- ]+)[\s]*\}')

# Returns that portion of the specified line that is most likely a heading,
# based characteristics of the text between a pair of parentheses in the line.
# Returns None if no parenthesized heading is found.
def find_parenthesized_heading(line):
    pheading = None
    for possible_hd in pphrase_re.finditer(line):
        possible_heading = possible_hd.group(0)
        if is_heading(possible_heading.strip()):
            pheading = possible_heading
            break
    return pheading

anyMarker_re = re.compile(r'\\[a-z]+[a-z1-5]* ?[0-9]*')

# Returns True if the string looks like a section heading.
# Any backslash markers or quote marks in the string disqualify it.
# See comments at the top of this file for factors that are considered.
# The threshold parameter specifies the minimum percentage of capitalized words
#    in a string that is partly title case.
def is_heading(str):
    confirmed = False
    str = str.strip(' \n')
    threshold = titlecase_threshold(str)
    # Initial qualification
    possible = (len(str) > 3 and not '\n' in str and\
                not anyMarker_re.search(str) and sentences.sentenceCount(str) == 1)
    if possible and not confirmed and expect_allcaps:
        confirmed = str.isupper()
    if possible and not confirmed and expect_titlecase:
        confirmed = (percentTitlecase(str) >= threshold)
    if possible and not confirmed and expect_parens:
        confirmed = str[0] == '(' and str[-1] == ')' and (str.isupper() or percentTitlecase(str[1:-1]) >= threshold)
    return confirmed

# Calculates the Title Case threshold (percentage of words that must be capitalized)
# based on characteristics of the string.
def titlecase_threshold(str):
    adj = 0.51
    quotepos = quotes.quotepos(str)
    if quotepos >= 0:
        adj = 0.66 if str[quotepos] in "'’" else 1.5
    if ',' in str:
        adj += 0.05
    if len(str) > 40:
        adj += 0.01 * (len(str) - 40)
    if str.startswith('(') and str.endswith(')'):
        adj -= 0.03
    # if firstAndLastTitlecase(str):
    #     adj -= 0.01
    return adj

# Inserts the section heading between two parts, including newlines.
def insert_heading(preheading, heading, postheading):
    preheading = preheading.rstrip()
    if preheading:
        preheading += '\n'
    postheading = postheading.lstrip()
    if postheading:
        postheading = '\n' + postheading
    section = preheading + "\\s " + heading.strip() + "\n\\p" + postheading
    return section
