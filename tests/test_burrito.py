# pytest unit tests for functions in LanguageInfo.py
# Before running these tests:
#    make version 7.6 the most common source in sources_translations in mgv.json.
#    remove "said_words" from test.json, or, set it to an empty dict -- {}

import os
import sys
import shutil
import filecmp
# import pytest

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
from scripture_burrito import Burrito

testdir = r'C:\DCS\Test'

def test_init_newfile():
    # This test function backs up the existing .json file before deleting it.
    pass

def test_read_write():
    # backup existing file
    path = os.path.join(testdir, "metadata.json")
    bakpath = os.path.join(testdir, "metadata_backup.json")
    if os.path.isfile(bakpath):
        if os.path.isfile(path):
            os.remove(bakpath)
        else:
            os.rename(bakpath, path)
    shutil.copyfile(path, bakpath)
    burrito = Burrito(testdir)
    errors = burrito.load()
    assert not errors
    content1 = burrito.contents
    burrito.save()
    errors = burrito.load()
    assert not errors
    content2 = burrito.contents
    assert content1 == content2
