# -*- coding: utf-8 -*-
# This script converts Word documents to UTF-8 text files.

import configmanager
import usfm_verses
import re
import io
import os
import sys
from pathlib import Path
import docx

config = None
gui = None
ids = {}    # id: list of fnames for that id
issues_file = None

# Writes error message to stderr and to issues.txt.
def reportError(msg):
    reportToGui('<<ScriptMessage>>', msg)
    write(msg, sys.stderr)
    openIssuesFile().write(msg + "\n")

# Sends a progress message to the GUI, and to stdout.
def reportProgress(msg):
    reportToGui('<<ScriptProgress>>', msg)
    write(msg, sys.stdout)

# Sends a status message to the GUI, and to stdout.
def reportStatus(msg):
    reportToGui('<<ScriptMessage>>', msg)
    write(msg, sys.stdout)

def reportToGui(event, msg):
    if gui:
        with gui.progress_lock:
            gui.progress = msg if not gui.progress else f"{gui.progress}\n{msg}"
        gui.event_generate(event, when="tail")

# This little function streams the specified message and handles UnicodeEncodeError
# exceptions, which are common in Indian language texts. 2/5/24.
def write(msg, stream):
    try:
        stream.write(msg + "\n")
    except UnicodeEncodeError as e:
        stream.write("(Unicode...)\n")

# If issues.txt file is not already open, opens it for writing.
# First renames existing issues.txt file to issues-oldest.txt unless
# issues-oldest.txt already exists.
# Returns file pointer.
def openIssuesFile():
    global issues_file
    if not issues_file:
        path = os.path.join(config['source_dir'], "issues.txt")
        if os.path.exists(path):
            bakpath = os.path.join(config['source_dir'], "issues-oldest.txt")
            if not os.path.exists(bakpath):
                os.rename(path, bakpath)
        issues_file = io.open(path, "tw", buffering=2048, encoding='utf-8', newline='\n')
    return issues_file

def closeIssuesFile():
    global issues_file
    if issues_file:
        issues_file.close()
        issues_file = None

# Reports error if this bookId has already been seen.
def check_dups(bookId, fname):
    global ids
    if bookId in ids:
        ids[bookId].append(fname)
        num =  usfm_verses.verseCounts[bookId]['usfm_number']
        msg = f"Multiple file names resolved to {num}-{bookId}:"
        for name in ids[bookId]:
            msg += f"\n  {name}"
        reportError(msg)
    else:
        ids[bookId] = [fname]

# Returns the degree of similarity between the two strings by a simple algorithm,
# similar to Jaccard similarity metric, based on number of characters in common.
def similarity(s1, s2):
    set1 = set(list(s1.upper()))
    set2 = set(list(s2.upper()))
    sim = len(set1&set2) / len(set1|set2)
    return sim

# Returns the most likely bookId for the specified number and fname.
def bookByNumber(num, name, bookIds):
    books = usfm_verses.verseCounts

    for id in bookIds:
        if num == books[id]["usfm_number"]:
            bookId = id
            break
    if int(num) > 39:   # NT
        b2 = None
        for book in books:
            if books[book]['sort'] == int(num):
                b2 = book
                break
        sim1 = similarity(name, books[bookId]['en_name'])
        if similarity(name, books[b2]['en_name']) > sim1:
            bookId = b2
    return bookId

def roman2arabic(str):
    str = str.replace("III ", "3 ")
    str = str.replace("II ", "2 ")
    str = str.replace("I ", "1 ")
    return str

num_name_re = re.compile(r'([0-6][0-9]?)[ \-\.]*([A-Za-z1-3]I*[ A-Za-z][A-Za-z]+)')

# Attempts to determine the Bible book from the file name.
# Returns upper case bookId, or empty string on failure.
def getBookId(filename):
    bookId = None
    (fname, ext) = os.path.splitext(filename)
    books = usfm_verses.verseCounts
    bookIds = list(books)
    bookIds.sort(key=lambda book: len(books[book]['en_name']), reverse=True)
    if len(fname) == 3 and fname.upper() in bookIds:
        bookId = fname.upper()
    else:
        fnameA = roman2arabic(fname)
        for id in bookIds:
            if books[id]['en_name'] in fnameA.title():
                bookId = id
                break
    if not bookId:
        if num_name := num_name_re.match(fname):
            num2 = int(num_name.group(1))
            name = num_name.group(2)
            name3 = name[0:3].upper()
            if name3 in books:
                bookId = name3
            elif 3 < num2 < 68:
                bookId = bookByNumber(f"{num2:02d}", fname[fname.find(num_name.group(2)):], bookIds)
    return bookId

def shortname(longpath):
    source_dir = Path(config['source_dir'])
    shortname = Path(longpath)
    if shortname.is_relative_to(source_dir):
        shortname = shortname.relative_to(source_dir)
    return str(shortname)

# Generates a path name for output text file.
def makeTxtPath(inputpath, bookId):
    if bookId:
        num = usfm_verses.verseCounts[bookId]['usfm_number']
        path = os.path.join(config['target_dir'], f"{num}-{bookId}.txt")
    else:
        fname = os.path.basename(inputpath) + ".txt"
        path = os.path.join(config['target_dir'], fname)
    return path

# This method is called to convert the specified file to usfm.
def convertFile(path, bookId):
    reportProgress(f"Converting: {shortname(path)}...")
    sys.stdout.flush()
    if not bookId:
        reportError("Unable to identify this book from the file name.")
    
    # Begin the actual conversion
    document = docx.Document(path)

    # Write the output file
    txtpath = makeTxtPath(path, bookId)
    with io.open(txtpath, 'tw', encoding='utf-8', newline='\n') as output:
        path = path.replace('\\', '/')  # avoid false usfm tags
        output.write(f"\\rem The text in this file was extracted from {path}.\n\n")
        str = '\n'.join([p.text.strip() for p in document.paragraphs]) 
        str = re.sub(r' +', r' ', str)
        output.write(str)
        output.write('\n')

def convertFolder(folder):
    for entry in os.listdir(folder):
        path = os.path.join(folder, entry)
        if os.path.isdir(path) and entry[0] != '.':
            convertFolder(path)
        elif os.path.isfile(path) and entry.endswith(".docx") and entry[0] != '~':
            bookId = getBookId(entry)
            if bookId:
                check_dups(bookId, entry)
            convertFile(path, bookId)

def main(app = None):
    global gui
    gui = app
    global ids
    ids = {}
    global config
    config = configmanager.ToolsConfigManager().get_section('Word2text')
    if config:
        source_dir = config['source_dir']
        file = config['filename']
        target_dir = config['target_dir']
        Path(target_dir).mkdir(exist_ok=True)

        if file:
            path = os.path.join(source_dir, file)
            if os.path.isfile(path):
                bookId = getBookId(file)
                if bookId:
                    check_dups(bookId, file)
                title = convertFile(path, bookId)
            else:
                reportError(f"No such file: {path}")
        else:
            convertFolder(source_dir)

    closeIssuesFile()
    reportStatus("\nDone.")
    sys.stdout.flush()
    if gui:
        gui.event_generate('<<ScriptEnd>>', when="tail")

# Processes each directory and its files one at a time
if __name__ == "__main__":
    main()
