# pytest unit tests for functions in paratext2usfm.py

import os
import sys
import pytest

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
import paratext2usfm

@pytest.mark.parametrize('fname, expected',
    [
        ('02-GENshpNTpo.usfm', 'GEN'),
        ('02-GENshpNTpo.fmm', 'GEN'),
        ('70-3JNshpNTpo.usfm', '3JN'),
    ])
def test_bookidfromFilename(fname, expected):
    assert paratext2usfm.bookidfromFilename(fname) == expected
