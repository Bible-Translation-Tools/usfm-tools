# pytest unit tests for functions in footnotes.py

import os
import sys
import pytest

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
import footnotes

language_code = 'en'
language_name = 'English'

@pytest.mark.parametrize('dir, expected',
    [(r'C:\DCS\EnglishTest\en_ulb.WA.v21-05', True),
     ('', False),
     (r'C:\DCS\EnglishTest', False),
     (r'C:\DCS\EnglishTest\Prescanned', True),
    ])
def test_validSourceDir(dir, expected):
    assert footnotes.validSourceDir(dir) == expected

@pytest.mark.parametrize('dir, expected',
    [(r'C:\DCS\EnglishTest', False),
     ('', False),
     (r'C:\DCS\EnglishTest\Prescanned', True),
    ])
def test_preScanned(dir, expected):
    assert footnotes.preScanned(dir) == expected

def test_scanUnscanned():
    dir = r'C:\DCS\EnglishTest\Unscanned'
    assert footnotes.preScanned(dir) == False
    footnotedVerses = footnotes.getFootnotedVerses(dir)
    assert 'JHN 8.11' not in footnotedVerses
    fvpath = os.path.join(dir, "footnotedVerses.json")
    if os.path.isfile(fvpath):
        os.remove(fvpath)

def test_getPrescanned():
    dir = r'C:\DCS\EnglishTest\Prescanned'
    footnotes.reset()
    assert footnotes.preScanned(dir) == True
    footnotedVerses = footnotes.getFootnotedVerses()    # Returns current set if any, or default set
    assert 'JHN 8:11' in footnotedVerses
    footnotedVerses = footnotes.getFootnotedVerses(dir)
    assert 'JHN 8:11' not in footnotedVerses

@pytest.mark.parametrize('verse, expected',
    [('GEN 1:26', True),
     ('GEN 1:27', False),
     ('ROM 8:28', True),
    ])
def test_footnotedVerses(verse, expected):
    # Tests the initial, default set
    footnotes.reset()
    fv = footnotes.getFootnotedVerses()     # Returns default set after reset()
    result = (verse in fv)
    assert result == expected
    assert len(fv) == 384

def test_scanFootnotes():
    dir = r'C:\DCS\EnglishTest\work'
    fvpath = os.path.join(dir, "footnotedVerses.json")
    if os.path.isfile(fvpath):
        os.remove(fvpath)
    fv = footnotes.getFootnotedVerses(dir)
    assert os.path.isfile(fvpath)
    assert footnotes.preScanned(dir) == True
    assert len(fv) == 4
    assert ('DAN 9:1' in fv)
    assert ('DAN 9:3' not in fv)

def test_scanFootnotes2():
    dir = r'C:\DCS\EnglishTest\en_ulb.WA.v21-05'
    fvpath = os.path.join(dir, "footnotedVerses.json")
    assert footnotes.preScanned(dir) == True
    assert os.path.isfile(fvpath)
    fv = footnotes.getFootnotedVerses(dir)
    assert len(fv) == 114
    assert "LEV 20:7" not in fv
    assert "MRK 16:20" in fv
