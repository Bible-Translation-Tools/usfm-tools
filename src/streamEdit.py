# -*- coding: utf-8 -*-
# This program may be modified to do any kind of stream operation on a folder full of files.
# Backs up the .md file being modified.
# Outputs .md files of the same name in the same location.

import re       # regular expression module
import io
import os
import sys

# Globals
source_dir = r'C:\DCS\Greek\SBLGNT\usfm'
target_dir = r'C:\DCS\Greek\SBLGNT\work'    # if same as source_dir, back up original files
nChanged = 0
max_changes = 80
# filename_re = re.compile(r'[\w\-]+\.usfm$')
filename_re = re.compile(r'.*\.usfm')
# yes_backup = True


# Strings to replace with
# whole file matches use newstring[0]
newstring = []
newstring.append('# ')

# Each element of inlinekey is matched against each line of a file.
# The matches occur in sequence, so the result of one match impacts the next.
inlinekey = []
inlinekey.append( re.compile(r'yesu', flags=re.UNICODE) )

# Copies lines from input to output.
# Modifies certain lines before writing them to output.
# Renames the input file to a backup name.
# Renames the output file to the original input file name.
def convertByLine(path):
    with io.open(path, "tr", 1, encoding="utf-8-sig") as input:
        lines = input.readlines()
    if target_dir == source_dir:
        bakpath = path + ".orig"
        if not os.path.isfile(bakpath):
            os.rename(path, bakpath)

    newpath = os.path.join(target_dir, os.path.basename(path))
    output = io.open(newpath, "tw", buffering=1, encoding='utf-8', newline='\n')

    prevline = ""
    for line in lines:
        unaltered = line
        line = convertLine(line, prevline)
        output.write(line)
        prevline = unaltered
    output.close()

w_re = re.compile(r'\\w +(\w+)\|strong="\w+" ?\\w\*')

def convertLine(line, prevline):
    w = w_re.search(line, 0)
    while w:
        word = w.group(1)
        line = line[0:w.start()] + word + line[w.end():]
        w = w_re.search(line, w.start() + len(word))
    return line

# keystring is used only in line-by-line. But it is searched against the entire file one time.
keystring = []
keystring.append( re.compile(r'yesu', flags=re.UNICODE) )

def convertFileByLines(path):
    global nChanged
    convertByLine(path)
    nChanged += 1
    sys.stdout.write("Converted " + shortname(path) + "\n")

def shortname(longpath):
    shortname = longpath
    if source_dir in longpath:
        shortname = longpath[len(source_dir)+1:]
    return shortname

# wholestring = re.compile(r' \\wj \\wj\*[ \n]', flags=re.UNICODE)
#wholestring = re.compile(r'[^v] ([1-9][0-9]?)[^0-9 ,\.\n\-]', flags=re.UNICODE)
wholestring = re.compile(r'\n\\v ')

# Converts the text a whole file at a time.
# Uses wholestring, newstring[0]
def convertWholeFile(path):
    global nChanged

#    found = classic_pattern(mdpath)
    with io.open(path, "tr", encoding="utf-8-sig") as input:
        alltext = input.read()
    found = wholestring.search(alltext)
    if found:
        if target_dir == source_dir:
            bakpath = path + ".orig"
            if not os.path.isfile(bakpath):
                os.rename(path, bakpath)
        newpath = os.path.join(target_dir, os.path.basename(path))
        output = io.open(newpath, "tw", buffering=1, encoding='utf-8', newline='\n')

        # Use a loop for multiple replacements per file
        while found:
            alltext = alltext[0:found.start()] + "\n\\m\n\\v " + alltext[found.end():]
            found = wholestring.search(alltext, found.end() + 6)
        output.write(alltext)
        output.close()
        sys.stdout.write("Converted " + shortname(path) + "\n")
        nChanged += 1

#sub_re = re.compile('figs-questions?', re.UNICODE)
#replacement = 'figs-rquestion'

#sub_re = re.compile(r'<o:p> *</o:p>', re.UNICODE)
sub_re = re.compile(r'\\p\n\\s5\n')
replacement = '\\s5\n\\p\n'
#sub_re = re.compile(r'</?o:p>', re.UNICODE)
#sub_re = re.compile(r'<!--.*-->', re.UNICODE)
#sub_re = re.compile(r'& *nbsp;', re.UNICODE)
#sub_re = re.compile(r'rc://en/', re.UNICODE)
#sub_re = re.compile(r'[Ll]ih?at[\s]*\:+[\s]*\n+[\s]*\[\[', re.UNICODE)
#sub_re = re.compile(r'# +[\*]+(.*)[\*]+', re.UNICODE)

# Stream edit the file by a simple, regular expression substitution
# To do only one substitution per file, change re.sub()'s count argument, below.
def convertFileBySub(path):
    global nChanged
    with io.open(path, "tr", encoding="utf-8-sig") as input:
        alltext = input.read()
    found = sub_re.search(alltext)
    if found:
        if target_dir == source_dir:
            bakpath = path + ".orig"
            if not os.path.isfile(bakpath):
                os.rename(path, bakpath)

        newpath = os.path.join(target_dir, os.path.basename(path))
        output = io.open(newpath, "tw", encoding='utf-8', newline='\n')
        output.write( re.sub(sub_re, replacement, alltext, count=0) )
        output.close()
        sys.stdout.write("Converted " + shortname(path) + "\n")
        nChanged += 1

def convertFile(path):
    convertFileByLines(path)
#    convertWholeFile(path)
    # convertFileBySub(path)


# Recursive routine to convert all files under the specified folder
def convertFolder(folder):
    global nChanged
    global max_changes
    if nChanged >= max_changes:
        return
    sys.stdout.write(shortname(folder) + '\n')
    for entry in os.listdir(folder):
        if entry[0] != '.':
            path = os.path.join(folder, entry)
            if os.path.isdir(path):
                convertFolder(path)
            elif filename_re.match(entry):
                convertFile(path)
            if nChanged >= max_changes:
                break

# Processes all .txt files in specified directory, one at a time
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        source_dir = sys.argv[1]

    if source_dir and os.path.isdir(source_dir):
        convertFolder(source_dir)
        sys.stdout.write("Done. Changed " + str(nChanged) + " files.\n")
    elif os.path.isfile(source_dir):
        path = source_dir
        source_dir = os.path.dirname(path)
        convertFile(path)
        sys.stdout.write("Done. Changed " + str(nChanged) + " files.\n")
    else:
        sys.stderr.write("Usage: python streamEdit.py <folder>\n  Use . for current folder.\n")
