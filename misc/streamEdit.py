# -*- coding: utf-8 -*-
# This program may be modified to do any kind of stream operation on a folder full of files.
# Backs up the file being modified, unless they are being created in a separate folder.
# Outputs files of the same name in the same location.

import re       # regular expression module
import io
import os
import sys

# Globals
source_dir = r'C:\DCS\Burmese\Judson (ebible usfm)'
target_dir = r'C:\DCS\Burmese\work'    # if same as source_dir, back up original files
nChanged = 0
max_changes = 80
# filename_re = re.compile(r'.*\.usfm$')
filename_re = re.compile(r'14-2CH\.usfm$')
prevline = ""

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

    for line in lines:
        line = convertLine(line)
        output.write(line)
    output.close()

# Returns True if the line is to be kept as is, False if not.
# Redefine this function to obtain desired behavior.
def keeper(line):
    # keep = line.startswith("\\s1")
    keep = False
    return keep

w_re = re.compile(r'\\w ([^|]+)\|strong="[\w,]+" ?\\w\* ?')  # Keep this pattern!
# character_styling = [r'\\\+nd( |\*)', r'\\\+tl( |\*)', r'\\\+fq( |\*)', r'\\\+xt( |\*)']
# round2 = [r'\\xt( |\*)']
# round3 = [r'\\\+em( |\*)', r'\\\+sc( |\*)']
# pm_re = re.compile(r'\\[mp]\s*$')

def convertLine(line):
    w = w_re.search(line)
    while w:
        remainder = line[w.end():]
        # if re.match(r'\w', remainder):
        #     remainder = ' ' + remainder
        line = line[0:w.start()] + w.group(1) + remainder
        w = w_re.search(line, w.start())
    line = line.replace('  ', ' ')
    line = line.replace(' \n', '\n')
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

# patterns = [re.compile(r'\\xt.*?\\xt\*'), re.compile(r'\\\+xt.*?\\\+xt\*')]
patterns = [ re.compile(r' +\\fqa\* +([,\.;?!])')]

def convertWholeString(alltext, pattern):
    found = pattern.search(alltext)
    while found:
        alltext = alltext[0:found.start()] + "\\fqa*" + found.group(1)+ alltext[found.end():]
        found = pattern.search(alltext, found.start())
    return alltext

# Converts the text a whole file at a time.
def convertWholeFile(path):
    global nChanged

    with io.open(path, "tr", encoding="utf-8-sig") as input:
        alltext = input.read()
    needchange = False
    for pattern in patterns:
        if pattern.search(alltext):
            needchange = True
            break

    if needchange:
        if target_dir == source_dir:
            bakpath = path + ".orig"
            if not os.path.isfile(bakpath):
                os.rename(path, bakpath)

        for pattern in patterns:
            alltext = convertWholeString(alltext, pattern)
        newpath = os.path.join(target_dir, os.path.basename(path))
        with io.open(newpath, "tw", buffering=1, encoding='utf-8', newline='\n') as output:
            output.write(alltext)
        sys.stdout.write("Converted " + shortname(path) + "\n")
        nChanged += 1

#sub_re = re.compile('figs-questions?', re.UNICODE)
#replacement = 'figs-rquestion'

#sub_re = re.compile(r'<o:p> *</o:p>', re.UNICODE)
sub_re = re.compile(r'\( *injili *\)')
replacement = 'injili'
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

def replaceCharacters(path):
    global nChanged
    badchar = '|'
    goodchar = '।'
    with io.open(path, "tr", encoding="utf-8-sig") as input:
        origtext = input.read()
    if badchar in origtext:
        if target_dir == source_dir:
            bakpath = path + ".orig"
            if not os.path.isfile(bakpath):
                os.rename(path, bakpath)

        newtext = origtext.replace(badchar, goodchar)
        assert newtext != origtext
        newpath = os.path.join(target_dir, os.path.basename(path))
        with io.open(newpath, "tw", encoding='utf-8', newline='\n') as output:
            output.write( newtext )
        sys.stdout.write("Replaced characters in " + shortname(path) + "\n")
        nChanged += 1

def convertFile(path):
    convertFileByLines(path)
    # convertWholeFile(path)
    # convertFileBySub(path)
    # replaceCharacters(path)

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
    nChanged = 0
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        source_dir = sys.argv[1]

    if not os.path.isdir(target_dir):
        os.mkdir(target_dir)
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
