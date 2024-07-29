# pytest unit tests for functions in paratext2usfm.py

import os
import sys

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
import pytest

@pytest.mark.parametrize('bookId, result',
    [
        ('GEN', '01-GEN.usfm'),
        ('MAT',  '41-MAT.usfm'),
        ('XXX', ''),
        ('', ''),
    ])
def test_makeUsfmFilename(bookId, result):
    import paratext2usfm
    assert paratext2usfm.makeUsfmFilename(bookId) == result

@pytest.mark.parametrize('fname, result',
    [
        ('01-GEN.usfm', 'GEN'),
        ('41-MAT.usfm', 'MAT'),
        ('41MAT', 'MAT'),
        ('41', ''),
        ('MAT', ''),
        ('41MATlpx_reg.SFM', 'MAT'),
        ('', ''),
        ('41-MAT.usfm', 'MAT'),
    ])
def test_bookidfromPtxfile(fname, result):
    import paratext2usfm
    assert paratext2usfm.bookidfromPtxfile(fname) == result