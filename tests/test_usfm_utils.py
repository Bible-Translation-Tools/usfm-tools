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
    ])
def test_unicodeBlock(text, expectedblock):
    block = usfm_utils.unicodeBlock(text)
    assert block == expectedblock
