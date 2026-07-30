# coding=utf-8
# Miscellaneous utility functions needed by various usfm tools
#    parseLine()
#    unalign_usfm()
#    unicodeBlock()
#    isCaseless()
#    usfm_errors(path)
#    usfm_text_errors(text)

from __future__ import unicode_literals
import re
import unicodedata
import os
import io

usfm_re = re.compile(r'\\([a-z][a-z1-5]*\*?)(\s+.*)?')
cvnumber_re = re.compile(r'[1-9][-0-9]*')

# Simplistically parses a single line as usfm.
# Assumes markers, if any, occur only at beginning of line.
# Sets value to chapter or verse number or id if applicable, otherwise "".
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
        elif marker == 'id':
            value = remainder[0:3]
            remainder = remainder[3:].strip()
    if not marker:
        remainder = line
    return (marker, value, remainder)

# This function was copied from somewhere else, I can't remember where.
# Converts an aligned USFM string to an unaligned USFM compatible string.
# Remove all tags used for alignments and words.
def unalign_usfm(aligned_usfm):
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
                if block_name != "ZERO":    # ignore \u200c and \u200d, and possibly other zero-width punctuation characters
                    blocks[block_name] = blocks.get(block_name, 0) + 1
        if blocks:
            primary_block = max(blocks, key=lambda key: blocks[key])
    return primary_block

# Returns True if the script is caseless.
def isCaseless(text):
    block = unicodeBlock(text)
    return (block in {'ARABIC','BENGALI','CJK','DEVANAGARI','ETHIOPIC','GUJARATI','GURMUKHI',
                      'HEBREW','HIRAGANA','KANNADA','LAO','MYANMAR','ORIYA','TAMIL','TELUGU'})

backslash_re = re.compile(r'\\\s')
jammed_re = re.compile(r'(\\v +[-0-9]+[^-\s0-9])', re.UNICODE)
usfmcode_re = re.compile(r'(\\[^a-z\+\s])', re.UNICODE)

# Returns a list of serious errors encountered on a quick scan of the specified usfm file.
def usfm_errors(usfmpath):
    errors = []
    if os.path.isfile(usfmpath):
        if os.path.getsize(usfmpath) < 1000:
            errors.append(f"{usfmpath} is incomplete, too small")
        else:
            with io.open(usfmpath, "tr", 1, encoding="utf-8-sig") as input:
                text = input.read(-1)
            errors = usfm_text_errors(text)
            for i in range(0, len(errors)):
                errors[i] = f"{os.path.basename(usfmpath)} {errors[i]}"
    else:
        errors.append( f"Unable to open: {usfmpath}")
    return errors

def usfm_text_errors(text):
    errors = []
    if backslash_re.search(text):
        errors.append("contains stranded backslash(es) followed by space or end of line")
    if bad := jammed_re.search(text):
        errors.append(f"contains verse number(s) not followed by space: {bad.group(1)}")
    for badcode in re.finditer(usfmcode_re, text):
        errors.append(f"contains foreign usfm code: {badcode.group(1)}")
    return errors

# Iterator, returns the next block in the file.
# Usually, a block is a single line.
# If multiple lines of pure text occur together, they are returned as a single block.
def nextblock(path):
    with io.open(path, "tr", encoding="utf-8-sig") as input:
        lines = input.readlines()
    i = 0
    while i < len(lines):
        if not usfm_re.match(lines[i]) and not lines[i].isspace():
            block = lines[i]
            i += 1
            while i < len(lines):
                if not usfm_re.match(lines[i]):
                    block += lines[i]
                    i += 1
                else:
                    break
            yield block
        else:
            yield lines[i]
            i += 1
