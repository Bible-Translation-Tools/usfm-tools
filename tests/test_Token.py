# pytest unit tests for Token class in usfmReader.py

import os
import sys
import pytest

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
from usfmReader import Token


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
    token = Token(mark, "")
    iss = token.isCharacterStyle()
    assert iss == expected

@pytest.mark.parametrize('mark, expected, interior',
    [
        ('f', True, False),
        ('', False, False),
        ('p', False, False),
        ('f*', True, False),
        (' f', False, False),
        ("ft", True, True),
        ("*f", False, False),
        ("fe", True, False),
        ("fe*", True, False),
        ("rq*", True, True),
        ("fq", True, True),
    ])
def test_isFootnote(mark, expected, interior):
    token = Token(mark, "")
    isf = token.isFootnote()
    assert isf == expected
    isinterior = token.isFootnoteInterior()
    assert isinterior == interior

@pytest.mark.parametrize('mark, expected',
    [
        ('5', False),
        ('   ', False),
        ('p-', False),
        ('p', True),
        (' pi', False),
        ("iot", True),
        ("iou",  False),
        ("m",  True),
        ("nb", True),
        ("b", True),
    ])
def test_isParagraph(mark, expected):
    token = Token(mark, "")
    isp = token.isParagraph()
    assert isp == expected

@pytest.mark.parametrize('mark, expected',
    [
        ('5', False),
        ('   ', False),
        ('p', False),
        ('qss', False),
        ('q', True),
        (' q', False),
        ("qm2", True),
        ("m", False),
        ("sp", False),
        ("q3", True),
    ])
def test_isPoetry(mark, expected):
    token = Token(mark, "")
    isp = token.isPoetry()
    assert isp == expected
