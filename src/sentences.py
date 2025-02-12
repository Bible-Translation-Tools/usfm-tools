# -*- coding: utf-8 -*-
# Utility functions for detecting end of sentence, and for capitalizing the first word in sentences.
# Supports hyphenated words.
# Note that these functions do not work if there are USFM markers in the input strings.

import re

endsentence_re = re.compile(r'[.?!\u0964\u1361\u1362][^\w]*$')
badquoted_re = re.compile(r'[?!\u1361\u1362]+[«“‘\-\u2014\u2013]')

"""
Special characters:
\u0964 is the Devangari Danda । character that terminates a sentence.
\u1361 is the Ethiopic Wordspace ፡ character that is often doubled up to use in place of \u1362.
\u1362 is the Ethiopic Full Stop ። character that terminates a sentence.
\u2013 is an en dash
\u2014 is an em dash
"""

# Returns True if the specified text ends with sentence-ending punctuation.
# However, an open quote mark following any of !?፡። introduces some uncertainty.
# So if checkquotes is True, this function returns:
#    False when opening quotes follow the sentence-ending punctuation
#    True when closed quotes, straight quotes or no quotes follow the sentence-ending punctuation.
def endsSentence(str, checkquotes=False):
    ending = endsentence_re.search(str)
    if ending and checkquotes:
        ends = (badquoted_re.match(str[ending.start():ending.start()+3]) == None)
    else:
        ends = (ending != None)
    return ends

firstword_re = re.compile(r'(\w+-\w+|\w+)')

# Returns the first word in the string.
def firstword(str):
    word = ''
    if first := firstword_re.search(str):
        word = first.group(1)
    return word

endsent_re = re.compile(r'[.?!\u0964\u1361\u1362].*?(\w+-\w+|\w+)', re.DOTALL)

# Generator function to yield the first word in each sentence in str,
# ***not counting*** the first word in the string, even if it starts a sentence.
def nextfirstwords(str):
    next = endsent_re.search(str)
    while next:
        if not badquoted_re.match(str[next.start():next.start()+2]):
            yield next.group(1)
        next = endsent_re.search(str, next.end())

# Generator function to yield the starting position of each sentence
# or partial sentence in str.
# @TODO Modify function to ignore periods in verse references.
def nextstartpos(str):
    nextword = firstword_re.search(str)
    while nextword:
        yield nextword.start()
        endsent = endsent_re.search(str, nextword.end())
        while endsent and badquoted_re.match(endsent.group(0)):
            endsent = endsent_re.search(str, endsent.end())
        nextword = firstword_re.search(str, endsent.start()+1) if endsent else None

# Capitalizes the first word in each sentence in the string.
# Capitalizes the first word in the string if startsSentence is True.
# Returns the string with changes as needed.
def capitalize(str, startsSentence):
    if startsSentence:
        if first := firstword_re.search(str):
            i = first.start()
            if str[i].islower():
                str = str[0:i] + str[i].upper() + str[i+1:]
    next = endsent_re.search(str)
    while next:
        i = str.find(next.group(1), next.start())
        if str[i].islower():
            if not badquoted_re.match(str[next.start():next.start()+2]):
                str = str[0:i] + str[i].upper() + str[i+1:]
        next = endsent_re.search(str, next.end())
    return str

# Returns the number of sentences or partial sentences in the string.
def sentenceCount(str):
    startposlist = [pos for pos in nextstartpos(str)]
    return len(startposlist)
