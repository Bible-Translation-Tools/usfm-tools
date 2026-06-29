# Utility functions

import os
import re
from manifestyaml import ManifestYaml

# Returns a count of files in specifed folder matching file name pattern.
# Non-recursive
def count_files(folder, pattern):
    n = 0
    if os.path.isdir(folder):
        for entry in os.listdir(folder):
            if re.match(pattern, entry.lower()):
                n += 1
    return n

# Returns a count of folders in path matching path name pattern.
# If the specified path itself is a folder matching the pattern, return 1.
def count_folders(path, pattern):
    n = 0
    if os.path.isdir(path):
        if re.search(pattern, path):
            n = 1
        for entry in os.listdir(path):
                if re.search(pattern, entry):
                    n += 1
    return n

# Returns the language code from the manifest.yaml file in the specified folder.
# @TODO unit test
def get_language_code(dir):
    code = ""
    if os.path.isdir(dir):
        my = ManifestYaml()
        my.load(dir)
        code = my.getLanguageId()
    return code

# Returns the language name from the manifest.yaml file in the specified folder.
# @TODO unit test
def get_language_name(dir):
    name = ""
    if os.path.isdir(dir):
        my = ManifestYaml()
        my.load(dir)
        name = my.getLanguageName()
    return name
