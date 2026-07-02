# -*- coding: utf-8 -*-

# Script for verifying a Scripture Burrito: metadata.json in situ.

nIssues = 0
resourceDir = ""
burrito_contents = dict()

import os
from configmanager import ToolsConfigManager
import re
import sys
from scripture_burrito import Burrito, size_and_checksum

# Writes error message to stderr.
def reportError(msg):
    reportToGui(msg)
    stream(msg, "Error", sys.stderr)
    sys.stderr.flush()
    global nIssues
    nIssues += 1

# Writes warnings message to stderr.
def reportWarning(msg):
    reportError("Possible error. " + msg)

def reportStatus(msg):
    reportToGui(msg)
    stream(msg, "Status", sys.stdout)

def reportToGui(msg):
    if gui:
        with gui.progress_lock:
            gui.progress = msg if not gui.progress else f"{gui.progress}\n{msg}"
        gui.event_generate('<<ScriptMessage>>', when="tail")

# This little function streams the specified message and handles UnicodeEncodeError
# exceptions, which are common in Indian language texts. 2/5/24.
def stream(msg, msgtype, stream):
    try:
        stream.write(msg + "\n")
    except UnicodeEncodeError as e:
        stream.write(f"{msgtype} message not shown, contains Unicode.\n")

def check_url_exists(url):
    import requests
    try:
        response = requests.head(url, allow_redirects=True)
        exists = response.status_code < 400
    except requests.exceptions.RequestException as e:
        exists = False
    return exists

# Verifies the syntactical correctness of the metadata.json file for now.
# Returns the number of issues found.
def verifyBurrito(app = None):
    global gui
    gui = app
    global nIssues
    nIssues = 0
    global resourceDir
    resourceDir = ToolsConfigManager().get('VerifyMetadata', 'work_dir')

    global burrito_contents
    burrito = Burrito(resourceDir)
    is_valid, msg = burrito.load()
    if is_valid:
        global burrito_contents
        burrito_contents = burrito.contents
        verifyCleanDir(resourceDir)
        verifyIngredients()
        verifyLanguage()
        verifyLicense()
        verifyWacsRepo()
    else:
        reportError(f"Invalid burrito data: {msg}")
    return nIssues

issuesfile_re = re.compile(r'issues.*\.txt')
readme_re = re.compile(r'readme(\.md|$)', re.IGNORECASE)

# Checks for extraneous files
def verifyCleanDir(dirpath):
    global burrito_contents
    ingredients = burrito_contents['ingredients'].keys()
    for entry in os.listdir(dirpath):
        # Skip known exceptions
        if entry in {"manifest.yaml", "metadata.json", "wordlist.tsv", ".git"}:
            continue
        if issuesfile_re.match(entry) or readme_re.match(entry):
            continue
        path = os.path.join(dirpath, entry)
        if os.path.isdir(path):
            verifyCleanDir(path)
        else:
            relpath = os.path.relpath(path, resourceDir)
            if relpath not in ingredients and relpath != burrito_contents['copyright']['licenses'][0]['ingredient']:
                reportError(f"This file is not listed as an ingredient in metadata.json: {relpath}")

subdir_re = re.compile(r'^[^\\/]+[\\/][^\\/]+')

def verifyIngredients():
    global resourceDir
    global burrito_contents
    for ingredient in burrito_contents['ingredients'].keys():
        path = os.path.join(resourceDir, ingredient)
        if not os.path.isfile(path):
            reportError(f"Ingredient file not found: {ingredient}")
        else:
            (size, checksum) = size_and_checksum(path)
            expect_size = burrito_contents['ingredients'][ingredient]['size']
            expect_checksum = burrito_contents['ingredients'][ingredient]['checksum']['md5']
            if size != expect_size:
                reportError(f"Ingredient size mismatch for {ingredient}: actual size is {size}")
            if checksum != expect_checksum:
                reportError(f"Ingredient checksum mismatch for {ingredient}: actual checksum is {checksum}")

def verifyLanguage():
    pass

def verifyLicense():
    global burrito_contents
    relpath = burrito_contents['copyright']['licenses'][0]['ingredient']
    path = os.path.join(resourceDir, relpath)
    if not os.path.isfile(path):
        reportError(f"License file not found: {relpath}")

def verifyWacsRepo():
    global burrito_contents
    if 'wacs' in burrito_contents['identification']['primary']:
        reportStatus("Checking existences of WACS repository. Please wait ...")
        repo_info = burrito_contents['identification']['primary']['wacs']
        for repo in repo_info.keys():
            url = os.path.join("https://content.bibletranslationtools.org/", repo)
            if not check_url_exists(url):
                reportError(f"WACS repository does not exist yet: {repo}")
    else:
        reportWarning("No WACS repository specified in metadata.json primary identification.")

def main(app = None):
    verifyBurrito(app)
    if nIssues == 0:
        reportStatus("Done, no issues found.")
    else:
        reportStatus("\nFinished checking burrito, found " + str(nIssues) + " issue(s).")
    sys.stdout.flush()
    if gui:
        gui.event_generate('<<ScriptEnd>>', when="tail")

if __name__ == "__main__":
    main()
