# pytest unit tests for functions in plaintext2usfm.py

import os
import sys
import pytest

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
import plaintext2usfm

@pytest.mark.parametrize('str, n, pos',
    [
        ('5', 5, 0),
        ('MATTHEW-5', 5, 8),
        ('chap 5', 5, 5),
        ("no number", 5, -1),
        ("1. Have", 1, 0),
    ])
def test_hasnumber(str, n, pos):
    assert plaintext2usfm.hasnumber(str, n) == pos

@pytest.mark.parametrize('str, n, pretext, vv, remainder',
    [
        ('5', 5, "", "5", ""),
        ('MATTHEW-5', 5, "MATTHEW-", "5", ""),
        ('chap 5', 5, "chap ", "5", ""),
        ("no number", 5, "","",""),
        ("1. Have", 1, "", "1", ". Have"),
        ("2.Have", 1, "", "", ""),
        ("2.Have", 2, "", "2", ".Have"),
        ("2Have", 2, "", "2", "Have"),
        ("Have2", 2, "Have", "2", ""),
        ("H2ave", 2, "H", "2", "ave"),
        ("3.Today is 3 tomorrow is 4", 3, "", "3", ".Today is 3 tomorrow is 4"),
    ])
def test_getvv(str, n, pretext, vv, remainder):
    (p,v,r) = plaintext2usfm.getvv(str, n)
    assert p == pretext
    assert v == vv
    assert r == remainder

@pytest.mark.parametrize('s, expected',
    [
        ('', [("","")]),
        ('MATTHEW-5', [("", "MATTHEW-5")]),
        ('\\c 1 ', [("c", "1 ")]),
        ('\\c1', [("c", "1")]),
        ('\\v 1 verse text', [("v", "1 verse text")]),
        ('\\v1 verse text', [("v", "1 verse text")]),
        ('\\v2 verse2 \\v 3 next', [("v", "2 verse2 "), ("v", "3 next")]),
        ('pretext \\v3 verse3 \\v 4 next', [("", "pretext "), ("v", "3 verse3 "), ("v", "4 next")]),
        ('\\v ', [("v", "")]),
        ('\\v4 ', [("v", "4 ")]),
    ])
def test_parseLine(s, expected):
    trlist = plaintext2usfm.parseLine(s)
    assert len(trlist) == len(expected)
    for i in range(len(trlist)):
        assert trlist[i][0] == expected[i][0]
        assert trlist[i][1] == expected[i][1]
