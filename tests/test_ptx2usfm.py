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
        ('40-MAT.usfm', 'MAT'),
        ('41-MAT.usfm', 'MAT'),
        ('41MAT', 'MAT'),
        ('41', ''),
        ('MAT', ''),
        ('ACT.usfm', ''),   # this format not supported yet
        ('41MATlpx_reg.SFM', 'MAT'),
        ('', ''),
        ('41-MAT.usfm', 'MAT'),
        ('039MAL.usx', 'MAL'),
        ('0091SA.usx', '1SA'),
        ('0102SA.usfm', '2SA'),
        ('62-2Jn.usfm', '2JN'),
        ('0643Jn.usfm', '3JN'),
        ('66rev.usfm', 'REV'),
        ('067REV-ulb.usfm', 'REV')
    ])
def test_bookidfromFilename(fname, result):
    import paratext2usfm
    assert paratext2usfm.bookidfromFilename(fname) == result
