# pytest unit tests for functions in plaintext2usfm.py

import os
import sys
import pytest

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
import usfm_utils

@pytest.mark.parametrize('line, exp_marker, exp_value, exp_remainder',
    [
        ('', '', '', ''),
        ('15 XYZ', '', '', '15 XYZ'),
        ('\\id mat asdf', 'id', '', 'mat asdf'),
        ('\\p', 'p', '', ''),
        ('\\p asdf', 'p', '', 'asdf'),
        ('\\c 1 asdf', 'c', '1', 'asdf'),
        ('\\v  2', 'v', '2', ''),
        ('\\v  2-3  asdf', 'v', '2-3', 'asdf'),
        ('\\v 4 asdljasdf asdf\\v 5 asdf', 'v', '4', 'asdljasdf asdf\\v 5 asdf'),
        ('asdfasdf. \\v 5', '', '', 'asdfasdf. \\v 5'),
        ('\\h Heading 1', 'h', '', 'Heading 1')
    ])
def test_parseLine(line, exp_marker, exp_value, exp_remainder):
    marker, value, remainder = usfm_utils.parseLine(line)
    assert marker == exp_marker
    assert value == exp_value
    assert remainder == exp_remainder

@pytest.mark.parametrize('text, expectedblock',
    [
        ('5', 'LATIN'), # we treat all ASCII characters as LATIN
        ('   ', 'LATIN'),
        ('π', 'GREEK'),
        ('あいう', 'HIRAGANA'),
        ('漢字', 'CJK'),
        ('שלום', 'HEBREW'),
        ('Здравствуйте', 'CYRILLIC'),
        ('MATTHEW-', 'LATIN'),
        ("ኧያእቆቢ ኧችን፤", 'ETHIOPIC'),
        ("دەرناکات،", 'ARABIC'),   # Arabic comma
        ("  ؟  ", 'ARABIC'),      # Arabic question mark
        ("میرے یسوع دے نال پکے ", 'ARABIC'),  # Western Punjabi
        ("\\v 27 ਕਿਉਂ*-!", 'GURMUKHI'),   # Malwai
        ("ਪਵਿੱਤਰ ਆਤਮਾ ਦਾ ਕਰਾਰ", 'GURMUKHI'), # Malwai
        ("सब के बारे में हम ", 'DEVANAGARI'),  # Urdu-devanagari
        ("देकमिओ छावनछा", 'DEVANAGARI'),  # Rai
        ("দ্বিতীয় দিন ", 'BENGALI'),    # Assamese language
    ])
def test_unicodeBlock(text, expectedblock):
    block = usfm_utils.unicodeBlock(text)
    assert block == expectedblock

@pytest.mark.parametrize('text, expected',
    [
        ('5', False), # we treat all ASCII characters as LATIN
        ('   ', False),
        ('π', False),
        ('あいう', True),
        ('漢字', True),
        ('שלום', True),
        ('Здравствуйте', False),
        ('MATTHEW-', False),
        ("ኧያእቆቢ ኧችን፤", True),
        ("دەرناکات،", True),   # Arabic comma
        ("  ؟  ", True),      # Arabic question mark
        ("میرے یسوع دے نال پکے ", True),  # Western Punjabi
        ("\\v 27 ਕਿਉਂ*-!", True),   # Malwai
        ("ਪਵਿੱਤਰ ਆਤਮਾ ਦਾ ਕਰਾਰ", True), # Malwai
        ("सब के बारे में हम ", True),  # Urdu-devanagari
        ("देकमिओ छावनछा", True),  # Rai
        ("দ্বিতীয় দিন ", True),     # Assamese
        ("ເປັນເມັດ", True),       # Lao
    ])
def test_isCaseless(text, expected):
    result = usfm_utils.isCaseless(text)
    assert result == expected
