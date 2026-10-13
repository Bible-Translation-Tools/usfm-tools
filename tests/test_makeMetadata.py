# pytest unit tests

import os
import sys
import shutil
import pytest

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
import makeMetadata

testdir = r'C:\DCS\Test\no_manifest'

@pytest.mark.parametrize('fname, expected_id, expected_name',
    [
        ('15-2CHmyajvb.usfm', '2CH', 'ရာဇဝင်ချုပ်ဒုတိယစောင်'),
        ('ABC.usfm', 'EPH', 'Uafisawa'),
        ('51-PHP.usfm', 'PHP', 'Filibiya'),
    ])
def test_idfromfle(fname, expected_id, expected_name):
    path = os.path.join(testdir, fname)
    id, name = makeMetadata.getIdAndTitle(path)
    assert id == expected_id, f"Expected id {expected_id} but got {id} for file {path}"
    assert name == expected_name, f"Expected name {expected_name} but got {name} for file {path}"
