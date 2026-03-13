# pytest unit tests for Burrito class

import os
import sys
import shutil
# import pytest

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
from scripture_burrito import Burrito

testdir = r'C:\DCS\Test\no_manifest'

def backup():
    # backup existing file
    path = os.path.join(testdir, "metadata.json")
    bakpath = os.path.join(testdir, "metadata_backup.json")
    if os.path.isfile(path) and not os.path.isfile(bakpath):
        shutil.copyfile(path, bakpath)
    elif os.path.isfile(bakpath) and not os.path.isfile(path):
        shutil.copyfile(bakpath, path)

def test_validate():
    # Validates existing file.
    burrito = Burrito(testdir)
    assert burrito.load()

def test_init_newfile():
    backup()
    burrito = Burrito(testdir)
    burrito.create()
    assert burrito.contents != {}
    assert burrito.save()   # proves that the contents are valid

def test_rewrite():
    backup()
    burrito = Burrito(testdir)
    assert burrito.load()
    content1 = burrito.contents
    burrito.save()
    assert burrito.load()
    content2 = burrito.contents
    assert content1 == content2
