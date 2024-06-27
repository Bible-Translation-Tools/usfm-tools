# -*- coding: utf-8 -*-
# Used by usfm_cleanup.py.
# Substitutions in this file convert straight double quotes to curly double quotes.
# To be used in languages where the single quote (apostrophe) is a word-forming character.
# These substitutions are applied after some regular expressions replacements have been made.

# dblsubs is a list of tuples to be used for string substitutions.
dblsubs = [
# Convert open quote marks
	('"“', '““'),
	('“"', '““'),
# Convert closing quote marks
	('"”', "””"),
	('”"', "””"),
]

import re
dblquote0_re = re.compile(r'[^\w]("+)[\w\']+("+)[^\w]')     # a single word in quotes
dblquote1_re = re.compile(r'[ \(\[]("+)[\w‘\']')     # SPACE|PAREN " word => “
dblquote2_re = re.compile(r': +[\'‘]*("+)[^\.!?)]')     # colon SPACE " ... => “
dblquote3_re = re.compile(r'[,;][’\']*("+)[’\']*[ \)]')     # comma/semicolon " SPACE|PAREN => ”
dblquote4_re = re.compile(r'[\.!\?][’\']*("+)')     # period/bang/question " => ”
dblquote5_re = re.compile(r'\w[’\']*("+) *\n')        # word " EOL => ”
dblquote6_re = re.compile(r'\w[\w ][’”]*("+\?)')       # " question => ” question
dblquote8_re = re.compile(r'\n *("+)[\w\'‘]')   # " word at start of line => “
dblopentrans = str.maketrans('"', '“')
dblclosetrans = str.maketrans('"', '”')

# Changes straight double quotes to curly quotes where context suggests with very high confidence.
def promoteDoubleQuotes(str):
    pos = 0
    snippet = dblquote0_re.search(str, pos)
    while snippet:
        if snippet.group(1) == snippet.group(2) and len(snippet.group(1)) == 1:
            (i,j) = (snippet.start(1), snippet.end(2))
            str = str[0:i] + snippet.group(1).translate(dblopentrans) + str[i+1:j-1] + snippet.group(2).translate(dblclosetrans) + str[j:]
        pos = snippet.end()
        snippet = dblquote0_re.search(str, pos)

    str = translate(str, dblquote1_re, dblopentrans)
    str = translate(str, dblquote2_re, dblopentrans)
    str = translate(str, dblquote3_re, dblclosetrans)
    str = translate(str, dblquote4_re, dblclosetrans)
    str = translate(str, dblquote5_re, dblclosetrans)
    str = translate(str, dblquote6_re, dblclosetrans)
    str = translate(str, dblquote8_re, dblopentrans)

    for pair in dblsubs:
        str = str.replace(pair[0], pair[1])
    return str

# Translates quotes in the string where the expression matches.
# Uses trans as the translation table.
def translate(str, rexp, trans):
    snippet = rexp.search(str)
    while snippet:
        (i,j) = (snippet.start(1), snippet.end(1))
        str = str[0:i] + snippet.group(1).translate(trans) + str[j:]
        snippet = rexp.search(str)
    return str

if __name__ == "__main__":
    teststr = 'They said: "boat '
    print(f"promoteDoubleQuotes({teststr}) => ({promoteDoubleQuotes(teststr)})")
