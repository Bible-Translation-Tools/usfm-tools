# -*- coding: utf-8 -*-
# Used by usfm_cleanup.py.
# Substitutions in this file convert straight quotes to curly quotes.
# These substitutions are applied after some regular expressions replacements have been made.

# subs is a list of tuples to be used for string substitutions.
subs = [
# Convert open quote marks
	("'“", "‘“"),
	("“'", "“‘"),
	('‘"', '‘“'),
	('"‘', '“‘'),

# Convert closing quote marks
	("'”", "’”"),
	("”'", "”’"),
	('’"', '’”'),
	('"’', '”’')
]

import re
quote0_re = re.compile(r'[^\w]([\'"]+)\w+([\'"]+)[^\w]')   # a single word in quotes
quote1_re = re.compile(r'[ \(\[][“‘]*([\'"]+)\w')     # SPACE|PAREN quotes word => open quotes
quote2_re = re.compile(r': +[“‘]*([\'"]+)[^\.!?)]')     # colon SPACE quotes ... => open quotes
quote3_re = re.compile(r'[,;][’”]*([\'"]+)[\)\]]')     # comma/semicolon quotes PAREN => close quotes
quote4_re = re.compile(r'[\.!\?][’”]*([\'"]+)')     # period/bang/question quotes => close quotes
quote5_re = re.compile(r'\w[’”]*([\'"]+)\s*$')        # word quotes EOS
quote6_re = re.compile(r'\w[\w ][’”]*([\'"]+\?)')       # quotes question => close quotes question
quote8_re = re.compile(r'^ *([\'"]+)[“‘]*\w', re.MULTILINE)   # quotes word at start of line
snglquote9_re = re.compile(r'‘[^“‘\'’”\n\\]+[^\s“‘\'’”\n\\](\')[^\w]')  # single quote at end of word if there is a matching open quote on the same line
opentrans = str.maketrans('\'"', "‘“")
closetrans = str.maketrans('\'"', '’”')

# Changes straight quotes to curly quotes where context suggests with very high confidence.
# Called by usfm_cleanup, passing in the entire usfm file as a string.
def promoteQuotes(s):
    pos = 0
    snippet = quote0_re.search(s, pos)
    while snippet:
        if snippet.group(1) == snippet.group(2) and len(snippet.group(1)) == 1:
            (i,j) = (snippet.start(1), snippet.end(2))
            s = s[0:i] + snippet.group(1).translate(opentrans) + s[i+1:j-1] + snippet.group(2).translate(closetrans) + s[j:]
        pos = snippet.end()
        snippet = quote0_re.search(s, pos)

    s = _translate(s, quote1_re, opentrans)
    s = _translate(s, quote2_re, opentrans)
    s = _translate(s, quote3_re, closetrans)
    s = _translate(s, quote4_re, closetrans)
    s = _translate(s, quote5_re, closetrans)
    s = _translate(s, quote6_re, closetrans)
    s = _translate(s, quote8_re, opentrans)
    s = _translate(s, snglquote9_re, closetrans)
    s = _translate(s, dblquote9_re, closetrans)
    for pair in subs:
        s = s.replace(pair[0], pair[1])
    return s

dblquote0_re = re.compile(r'[^\w]("+)\w+("+)[^\w]')     # a single word in quotes
dblquote1_re = re.compile(r'[ \(\[]("+)[\w‘\']')     # SPACE|PAREN " word => “
dblquote2_re = re.compile(r': +[\'‘]*("+)[^\.!?)]')     # colon SPACE " ... => “
dblquote3_re = re.compile(r'[,;][’\']*("+)[’\']*[\)\]]')     # comma/semicolon " PAREN => ”
dblquote4_re = re.compile(r'[\.!\?][’\']*("+)')     # period/bang/question " => ”
dblquote5_re = re.compile(r'\w[’\']*("+)\s*$')        # word " EOS => ”
dblquote6_re = re.compile(r'\w[\w ][’”]*("+\?)')       # " question => ” question
dblquote8_re = re.compile(r'^ *("+)[\w\'‘]', re.MULTILINE)   # " word at start of line => “
dblquote9_re = re.compile(r'“[^“‘\'’”\n\\]+[^\s“‘\'’”\n\\](")[^\w]')  # quote at end of word if there is a matching open quote on the same line
dblopentrans = str.maketrans('"', '“')
dblclosetrans = str.maketrans('"', '”')
# dblsubs is a list of tuples to be used for string substitutions.
dblsubs = [
# Convert open quote marks
	('"“', '““'),
	('“"', '““'),
	('‘"', '‘“'),
	('"‘', '“‘'),
    ('“\'"', '“\'“'),
    ('"\'“', '“\'“'),
# Convert closing quote marks
	('"”', "””"),
	('”"', "””"),
	('’"', '’”'),
	('"’', '”’'),
    ('”\'"', '”\'”'),
    ('"\'”', '”\'”'),
]

# Changes straight double quotes to curly quotes where context suggests with very high confidence.
def promoteDoubleQuotes(s):
    pos = 0
    snippet = dblquote0_re.search(s, pos)
    while snippet:
        if snippet.group(1) == snippet.group(2) and len(snippet.group(1)) == 1:
            (i,j) = (snippet.start(1), snippet.end(2))
            s = s[0:i] + snippet.group(1).translate(dblopentrans) + s[i+1:j-1] + snippet.group(2).translate(dblclosetrans) + s[j:]
        pos = snippet.end()
        snippet = dblquote0_re.search(s, pos)

    s = _translate(s, dblquote1_re, dblopentrans)
    s = _translate(s, dblquote2_re, dblopentrans)
    s = _translate(s, dblquote3_re, dblclosetrans)
    s = _translate(s, dblquote4_re, dblclosetrans)
    s = _translate(s, dblquote5_re, dblclosetrans)
    s = _translate(s, dblquote6_re, dblclosetrans)
    s = _translate(s, dblquote8_re, dblopentrans)
    s = _translate(s, dblquote9_re, dblclosetrans)

    for pair in dblsubs:
        s = s.replace(pair[0], pair[1])
    return s

# Internal function.
# Translates quotes in the string wherever the expression matches.
# Uses trans as the translation table.
def _translate(s, rexp, trans):
    snippet = rexp.search(s)
    while snippet:
        (i,j) = (snippet.start(1), snippet.end(1))
        s = s[0:i] + snippet.group(1).translate(trans) + s[j:]
        snippet = rexp.search(s)
    return s

# quotes_re = re.compile(r'[“‘‹«\'"’”›»]')

# # Returns the character position of the first quote in the string, or -1 if none.
# def quotepos(str):
#     quote = quotes_re.search(str)
#     return quote.start() if quote else -1

# openquote_re = re.compile(r'[^\w]*[\'"“‘‹«]+.*\w')
# closequote_re = re.compile(r'\w.*[\'"’”›»]+[^\w]*$')
# internalquote_re = re.compile(r'\w.*["“‘‹«”›»]+.*\w')

# Returns True if the string starts or ends an incomplete quotation.
# This function is used by section_titles.is_heading() to exclude
# most candidates for section titles that include quote marks.
# @TODO A *complete* internal quotation should not cause a True return value.
# def partialQuote(str):
#     starts = bool(openquote_re.match(str))
#     ends = bool(closequote_re.search(str))
#     internal = bool(internalquote_re.search(str))   # too simplistic
#     return starts ^ ends ^ internal

matetrans = str.maketrans("\"'«“‘„»”’", "\"'»”’”«“‘")

# Returns the complementary quote character, or '' if invalid input.
def matechar(quote: str):
    if quote in "\"'«“‘»”’":
        mate = quote.translate(matetrans)
    else:
        mate = ''
    return mate

def is_open(quote: str):
    return quote in "«“‘"

def is_closed(quote: str):
    return quote in "»”’"

# Returns True if the specified character is a straight quote.
# @param singles means single straight quotes qualify
def is_straight(quote: str, singles):
    return quote == '"' or (singles and quote == "'")
