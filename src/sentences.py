# -*- coding: utf-8 -*-
# Utility functions for detecting end of sentence, and for capitalizing the first word in sentences.
# Note that these functions do not work if there are USFM markers in the input strings.

import re

firstword_re = re.compile(r'([\w]+)')
nextsent_re = re.compile(r'[.?!\u0964\u1361\u1362].*?([\w]+)')
specialquoted_re = re.compile(r'[?!\u0964\u1361\u1362][\'"’”»\-——]')    # exception to sentence ending
endsentence_re = re.compile(r'[.?!\u0964\u1361\u1362][^\w]*$')

"""
Special characters:
\u0964 is the Devangari Danda । character that terminates a sentence.
\u1361 is the Ethiopic Wordspace character that is often used doubled up to use in place of \u1362.
\u1362 is the Ethiopic Full Stop ። character that terminates a sentence.
"""

# Returns True if the specified text ends with sentence-ending punctuation:
#    period, question mark, exclamation mark, or the Indian character । (\u0964)
def endsSentence(str):
    return endsentence_re.search(str)

# Returns True if the specified text ends with sentence-ending punctuation
# followed by a closed quote or straight quote or dash.
def endsQuotedSentence(str):
    ends = False
    if ending := endsentence_re.search(str):
        if specialquoted_re.match(str[ending.start():ending.start()+2]):
           ends = True
    return ends

# Returns the first word in the string.
def firstword(str):
    word = None
    if first := firstword_re.search(str):
        word = first.group(1)
    return word

# Generator function to yield the first word in each sentence in str,
# not counting the first word in the string, even if it starts a sentence.
def nextfirstwords(str):
    next = nextsent_re.search(str)
    while next:
        if not specialquoted_re.match(str[next.start():next.start()+2]):
            yield next.group(1)
        next = nextsent_re.search(str, next.end())

# Generator function to yield the starting position of each sentence
# or partial sentence in str.
def nextstartpos(str):
    next = firstword_re.search(str)
    while next:
        nextpos = next.start(1)
        yield nextpos
        next = nextsent_re.search(str, nextpos+1)

# Capitalizes the first word in each sentence in the string.
# Capitalizes the first word in the string if startsSentence is True.
# Returns the string with changes as needed.
def capitalize(str, startsSentence):
    if startsSentence:
        if first := firstword_re.search(str):
            i = first.start()
            if str[i].islower():
                str = str[0:i] + str[i].upper() + str[i+1:]
                changed = True
    next = nextsent_re.search(str)
    while next:
        i = str.find(next.group(1), next.start())
        if str[i].islower():
            if not specialquoted_re.match(str[next.start():next.start()+2]):
                str = str[0:i] + str[i].upper() + str[i+1:]
                changed = True
        next = nextsent_re.search(str, next.end())
    return str
