# pytest unit tests for the original and the WA versions of scripture_burrito_validator.

import os
import sys
import shutil
# import pytest

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
import scripture_burrito_validator
import scripture_burrito_validator_orig

testdir_wa = r'C:\DCS\Test\burritos\WA'
testdir_orig = r'C:\DCS\Test\burritos\orig'

def test_empty():
    is_valid, msg = scripture_burrito_validator.validate("")
    if not is_valid:
        print(msg)
    assert not is_valid

def test_WA_file():
    path = os.path.join(testdir_wa, "metadata.json")
    is_valid, msg = scripture_burrito_validator.validate(path)
    if not is_valid:
        print(msg)
    assert is_valid

    is_valid, msg = scripture_burrito_validator_orig.validate(path)
    if not is_valid:
        print(msg)
    assert is_valid

def test_orig_file():
    path = os.path.join(testdir_orig, "metadata.json")
    is_valid, msg = scripture_burrito_validator.validate(path)
    if not is_valid:
        print(msg)
    assert not is_valid

    is_valid, msg = scripture_burrito_validator_orig.validate(path)
    if not is_valid:
        print(msg)
    assert is_valid

def test_rai():
    path = r'C:\DCS\Rai\work\metadata.json'
    is_valid, msg = scripture_burrito_validator.validate(path)
    if not is_valid:
        print(msg)
    assert is_valid

    is_valid, msg = scripture_burrito_validator_orig.validate(path)
    if not is_valid:
        print(msg)
    assert is_valid
