# pytest unit tests for functions in plaintext2usfm.py

import os
import sys

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
import pytest

@pytest.mark.parametrize('str, n, pos',
    [
        ('5', 5, 0),
        ('MATTHEW-5', 5, 8),
        ('chap 5', 5, 5),
        ("no number", 5, -1),
        ("1. Have", 1, 0),
    ])
def test_hasnumber(str, n, pos):
    import plaintext2usfm
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
    import plaintext2usfm
    (p,v,r) = plaintext2usfm.getvv(str, n)
    assert p == pretext
    assert v == vv
    assert r == remainder
