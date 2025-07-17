# pytest unit tests for functions in plaintext2usfm.py

import os
import sys
import pytest

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
import mark_paragraphs

@pytest.mark.parametrize('s, result',
    [
        ('5', False),
        ('', False),
        ('MATTHEW-', True),
        ('avlede Azor; ', True),
        ("ኧያእቆቢ ኧችን፤", True),
        ("ኧያእቆቢ ኧችን", False),
        ("دەرناکات،", True),   # Arabic comma
        (" دەبن؟", True),      # Arabic question mark
        ("ኖኦራአአር ኢሽሬ፤", True),
        ("spaces  ", False),
    ])
def test_punctuated(s, result):
    assert mark_paragraphs.punctuated(s) == result

@pytest.mark.parametrize('text, expectedblock',
    [
        ('5', 'DIGIT'),
        ('   ', 'Unknown'),
        ('MATTHEW-', 'LATIN'),
        ("ኧያእቆቢ ኧችን፤", 'ETHIOPIC'),
        ("دەرناکات،", 'ARABIC'),   # Arabic comma
        (" دەبن؟", 'ARABIC'),      # Arabic question mark
        ("ኖኦራአአር ኢሽሬ፤", 'ETHIOPIC'),
    ])
def test_unicodeBlock(text, expectedblock):
    block = mark_paragraphs.unicodeBlock(text)
    assert block == expectedblock

@pytest.mark.parametrize('mark, expectedScanning, expectedNotScanning',
    [
        ('5', False, False),
        ('   ', False, False),
        ('p-', False, False),
        ('p', True, True),
        (' pi', False, False),
        ("iot", True, True),
        ("iou", False, False),
        ("m", False, True),
        ("nb", False, True),
        ("b", False, True),
    ])
def test_isParagraph(mark, expectedScanning, expectedNotScanning):
    isp = mark_paragraphs.isParagraph(mark, True)
    assert isp == expectedScanning
    isp = mark_paragraphs.isParagraph(mark, False)
    assert isp == expectedNotScanning

@pytest.mark.parametrize('mark, expected',
    [
        ('f', True),
        ('', False),
        ('p', False),
        ('f*', True),
        (' f', False),
        ("ft", True),
        ("*f", False),
        ("fe", True),
        ("fe*", True),
        ("rq*", True),
        ("fq", True),
    ])
def test_isFootnote(mark, expected):
    isf = mark_paragraphs.isFootnote(mark)
    assert isf == expected

@pytest.mark.parametrize('mark, expected',
    [
        ('em', True),
        ('', False),
        (' em', False),
        ('fig', False),
        ('it*', True),
        ('it', True),
        ("bd", True),
        ("bdit*", True),
        ("no", True),
        ("sc*", True),
    ])
def test_isCharacterStyle(mark, expected):
    iss = mark_paragraphs.isCharacterStyle(mark)
    assert iss == expected
