# coding=utf-8
# Miscellaneous utility functions needed by various usfm tools
#    parseLine()
#    unalign_usfm()
#    unicodeBlock()

from __future__ import unicode_literals
import re
import unicodedata

usfm_re = re.compile(r'\\([a-z][a-z1-5]*\*?)(\s+.*)?')
cvnumber_re = re.compile(r'[1-9][-0-9]*')

# Simplistically parses a single line as usfm.
# Assumes markers, if any, occur only at beginning of line.
# Sets value to chapter or verse number if applicable, otherwise "".
# Returns a tuple of (marker, value, remainder)
def parseLine(line):
    marker = value = remainder = ""
    if usfm := usfm_re.match(line):
        marker = usfm.group(1)
        remainder = usfm.group(2).strip() if usfm.group(2) else ""
        if marker in {'c', 'v'}:
            if cvnumber := cvnumber_re.match(remainder):
                value = cvnumber.group(0)
                remainder = remainder[len(value):].strip()
            else:
                marker = ""
    if not marker:
        remainder = line
    return (marker, value, remainder)

def unalign_usfm(aligned_usfm):
    """
    Converts an aligned USFM string to an unaligned USFM compatible string
    :param aligned_usfm:
    :return: the unaligned USFM of the string
    """
    # Remove all tags used for alignments and words
    usfm = re.sub(r'\\ts(-s)*\s*\\\*\s*', r'', aligned_usfm, flags=re.UNICODE | re.MULTILINE)
    usfm = re.sub(r'\\zaln-s[^*]*?\*', r'', usfm, flags=re.UNICODE | re.MULTILINE)
    usfm = re.sub(r'\\zaln-e\\\*', r'', usfm, flags=re.UNICODE | re.MULTILINE)
    usfm = re.sub(r'\\k-s.*?\\\*', r'', usfm, flags=re.UNICODE | re.MULTILINE)
    usfm = re.sub(r'\\k-e\\\*', r'', usfm, flags=re.UNICODE | re.MULTILINE)
    usfm = re.sub(r'\\w ([^|]+)\|.*?\\w\*', r'\1', usfm, flags=re.UNICODE | re.MULTILINE)
    usfm = re.sub(r'^\n', '', usfm, flags=re.UNICODE | re.MULTILINE)
    usfm = re.sub(r'^([^\\].*)\n(?=[^\\])', r'\1 ', usfm, flags=re.UNICODE | re.MULTILINE)
    usfm = re.sub(r'^\\(.*)\n(?=[^\\])', r'\\\1 ', usfm, flags=re.UNICODE | re.MULTILINE)
    usfm = re.sub(r'  +', ' ', usfm, flags=re.UNICODE | re.MULTILINE)

    # Clean up bad USFM data and fixing punctuation
    usfm = re.sub(r"\s*' s(?!\w)", "'s", usfm, flags=re.UNICODE | re.MULTILINE)
    usfm = re.sub(r'\\s5', '', usfm, flags=re.UNICODE | re.MULTILINE)
    usfm = re.sub(r'\\fqa([^*]+)\\fqa(?![*])', r'\\fqa\1\\fqa*', usfm, flags=re.UNICODE | re.MULTILINE)

    # Pair up quotes by chapter
    chapters = re.compile(r'\\c ').split(usfm)
    usfm = chapters[0]
    for chapter in chapters[1:]:
        chapter = re.sub(r'[ \t]*"([^"]+)"[ \t]*', r' "\1" ', chapter, flags=re.UNICODE | re.MULTILINE | re.DOTALL)
        usfm += '\\c {0}'.format(chapter)
    usfm = re.sub(r'\\(\w+\**)([^\w* \n])', r'\\\1 \2', usfm, flags=re.UNICODE | re.MULTILINE)  # \\q1" => \q1 "
    usfm = re.sub(r" ' ", r" '", usfm, flags=re.UNICODE | re.MULTILINE)
    usfm = re.sub(r' +([:;.?,!\]})-])', r'\1', usfm, flags=re.UNICODE | re.MULTILINE)
    usfm = re.sub(r'([{(\[-]) +', r'\1', usfm, flags=re.UNICODE | re.MULTILINE)

    return usfm.strip()

# Returns the first word of the Unicode name of most of the characters in the string.
# This is not exactly the same as the Unicode Block, but better.
def unicodeBlock(text):
    blocks = {}
    if text.isascii():
        primary_block = 'LATIN' # our simplification
    else:
        primary_block = 'Unknown'
        for char in text:
            if char not in " \n\\vcpq*-0123456789":
                block_name = unicodedata.name(char, "Unknown").split()[0]
                blocks[block_name] = blocks.get(block_name, 0) + 1
        if blocks:
            primary_block = max(blocks, key=lambda key: blocks[key])
    return primary_block

# Returns True if the script is caseless.
def isCaseless(text):
    block = unicodeBlock(text)
    return (block in {'ARABIC','BENGALI','CJK','DEVANAGARI','ETHIOPIC','GURMUKHI','HEBREW','HIRAGANA'})
