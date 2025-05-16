# Utility functions

import os
import re

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
