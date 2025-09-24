# pytest unit tests for functions in plaintext2usfm.py

import os
import sys
import pytest

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
import usfm_utils

@pytest.mark.parametrize('text, expectedblock',
    [
        ('5', 'LATIN'), # we treat all ASCII characters as LATIN
        ('   ', 'LATIN'), # we treat spaces as LATIN
        ('π', 'GREEK'),
        ('あいう', 'HIRAGANA'),
        ('漢字', 'CJK'),
        ('שלום', 'HEBREW'),
        ('Здравствуйте', 'CYRILLIC'),
        ('MATTHEW-', 'LATIN'),
        ("ኧያእቆቢ ኧችን፤", 'ETHIOPIC'),
        ("دەرناکات،", 'ARABIC'),   # Arabic comma
        (" دەبن؟", 'ARABIC'),      # Arabic question mark
        ("\\v 27 ਕਿਉਂ ਜੋ ਲਿਖਿਆ ਹੋਇਆ ਹੈ*-!", 'GURMUKHI'),
        ("ਯਿਸੂ ਦੀ ਵੰਸ਼ਾਵਲੀ", 'GURMUKHI'),  # Punjabi
    ])
def test_unicodeBlock(text, expectedblock):
    block = usfm_utils.unicodeBlock(text)
    assert block == expectedblock
