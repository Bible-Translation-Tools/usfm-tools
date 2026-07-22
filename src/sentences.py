# -*- coding: utf-8 -*-
# Utility functions for detecting end of sentence, and for capitalizing the first word in sentences.
# Supports hyphenated words.
# Note that these functions do not work if there are USFM markers in the input strings.

import re

"""
Special characters:
\u0964 is the Devangari Danda । character that terminates a sentence.
\u0965 is the Devangari Danda ॥ character that terminates a section or paragraph.
\u1361 is the Ethiopic Wordspace ፡ character that is often doubled up to use in place of \u1362.
\u1362 is the Ethiopic Full Stop ። character that terminates a sentence.
\u061F is the Arabic question mark ؟
\u06D4 is the Arabic full stop
\u2013 is an en dash
\u2014 is an em dash
"""
endsentence_re = re.compile(r'([.?!\u0964\u0965\u1361\u1362\u061F\u06D4])[^\w]*$')
badquoted_re = re.compile(r'[?!\u1361\u1362\u061F\u06D4]+[«“‘\-\u2014\u2013]')

# Returns the sentence-ending punctuation mark if the text ends a sentence.
# Returns '' if the text does not end with sentence-ending punctuation.
# An open quote mark following any of !?፡። introduces some uncertainty.
# So if checkquotes is True, this function returns:
#    '' when an opening quote or dash follows the sentence-ending punctuation
def endsSentence(s, checkquotes=False):
    ends = ''
    if ending := endsentence_re.search(s):
        ends = ending.group(1)
        if checkquotes and badquoted_re.match(s[ending.start():ending.start()+3]):
            ends = ''
    return ends

word_re = re.compile(r'(\w+-\w+|\w+)')

# Returns the first word in the string.
def firstword(s):
    word = ''
    if first := word_re.search(s):
        word = first.group(1)
    return word

# Returns the last word in the string.
def lastword(s):
    word = ""
    for item in reversed(s.split()):
        if words := word_re.findall(item):
            word = words[-1]
            break
    return word

endsent_re = re.compile(r'[.?!\u0964\u0965\u1361\u1362\u061F\u06D4].*?(\w+-\w+|\w+)', re.DOTALL)

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
    nextword = word_re.search(str)
    while nextword:
        yield nextword.start()
        endsent = endsent_re.search(str, nextword.end())
        while endsent and badquoted_re.match(endsent.group(0)):
            endsent = endsent_re.search(str, endsent.end())
        nextword = word_re.search(str, endsent.start()+1) if endsent else None

# Capitalizes the first word in each sentence in the string.
# Capitalizes the first word in the string if startsSentence is True.
# Returns the string with changes as needed.
def capitalize(str, startsSentence=True):
    if startsSentence:
        if first := word_re.search(str):
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

startword_re = re.compile(r'[\w "‘“\'\()]')

# Intended for single words, and may not work correctly for phrases.
# Differs from str.istitle() in how apostrophes and hyphens are treated.
# Considered numbers to be uncapitalized words.
# istitle("Paul's") returns False.
# _isCapitalized("Paul's") returns True.
# _isCapitalized("E'Besusaida") returns True.
# Hyphenated words like Two-sided and Two-Sided return True.
def isCapitalized(word:str):
    if not startword_re.match(word):
        result = False
    elif word.istitle():
        result = True
    else:
        strings = re.split("['’-]", word)
        result = strings[0].istitle()
        if result:
            for i in range(1,len(strings)):
                if not (strings[i].islower() or strings[i].istitle()):
                    result = False
    return result
