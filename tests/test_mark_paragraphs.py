# pytest unit tests for functions in mark_paragraphs.py

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

@pytest.mark.parametrize('mark, expected',
    [
        ('5', False),
        ('   ', False),
        ('p', False),
        ('qss', False),
        ('q', True),
        (' q', False),
        ("qm2", True),
        ("q3", True),
        ("m", False),
        ('d', True),
        ("sp", True),
    ])
def test_isPoetryMark(mark, expected):
    isp = mark_paragraphs.isPoetryMark(mark)
    assert isp == expected

@pytest.mark.parametrize('s, expected',
    [('5', ''),
     ('   ', ''),
     ('p', ''),
     ('"qss', 'qss'),
     ('"q"', '"""q"""'),
     (' "q', ''),
     ('"qm2"', '"""qm2"""'),
     ("q,3", 'q;3'),
     ('"m"nnnn', '"""m"""nnnn'),
     ('"d" ee "', '"""d""" ee "'),
     ('sp " sp', ''),
     ('rst" uvw"', ''),
     ('xyz"', '')
    ])
def test_csv(s, expected):
    if not expected:
        expected = s
    result = mark_paragraphs.csv(s)
    assert result == expected
