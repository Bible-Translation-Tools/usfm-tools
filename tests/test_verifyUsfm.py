# pytest unit tests for functions in verifyUsfm.py

import os
import sys

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
import pytest
import verifyUSFM
from verifyUSFM import State

@pytest.mark.parametrize('str, result',
    [
        ('', 0),
        ('XYZ', 0),
        ('MAT', 28),
        ('mat', 0),
        ('MATT', 0),
        ('REV', 22),
        ('FRT', 0),
        (1, 0),
        (None, 0),
    ])
def test_nChapters(str, result):
    assert verifyUSFM.nChapters(str) == result

@pytest.mark.parametrize('word, expected',
    [
        ('', False),
        ('XYZ', False),
        ('Mat', False),
        ('mat', False),
        ('MaTT', True),
        ('rEv', True),
        ('frT', True),
        ('I', False),
        ('embed"ded', False),
        ("embed'ded", False),
        ("embed’ded", False),
        ("’leading", False),
        ("trailing’", False),
        ('"leading', False),
        ("'QuoTed'", True),
        ("'", False),
        ("`bwo ", False),
        ("a'iy", False),
        ("ab'b'eh", False),
        ("aka-iy", False),
        ("d'Jerusalem", True),
        ("Śâulo", False),
        ("Bârśâbbâś", False),
        ("BârŚâbbâś", True),
        ('Two Words', False),
        # ('two Words', False),     # isMixed() returns True, GIGO
        ('before”after', False),
        ('Before”', False),
        ('”After', False),
        ('Yahweh—that', True),  # isMixed() returns True but em-dash -> two words
        ('laws—I', True),     # isMixed() returns True but em-dash -> two words
        ('Tu`u`tu`u', False),
        ("ኧያእቆቢ ኧችን፤", False),  # this one and the remaining tests are from caseless scripts
        ("دەرناکات،", False),   # Arabic comma
        ("  ؟  ", False),      # Arabic question mark
        ("میرے یسوع دے نال پکے ", False),  # Western Punjabi
        ("\\v 27 ਕਿਉਂ*-!", False),   # Malwai
        ("सब के बारे में हम ", False),  # Urdu-devanagari
        ("देकमिओ छावनछा", False),  # Rai
        ("দ্বিতীয় দিন ", False),     # Assamese
        ("ເປັນເມັດ", False),      # Lao
        ("अमो‍‌‍‌‌‍‌न", False),     # Bhojpuri corrupted word with \i200c and d characters
        ("रहलन", False),    # Bhojpuri
    ])
def test_isMixed(word, expected):
    assert verifyUSFM.isMixed(word) == expected

@pytest.mark.parametrize('s, expected',
    [
        ('', []),
        ('XYZ', ['XYZ']),
        ('embed"ded', []),  # most mid-word punctuation disqualifies the word
        ("embed'ded", ["embed'ded"]),
        ("embed’ded", ["embed’ded"]),
        ("no-break space", ['no-break','space']),  # no-break-space splits words
        ("’leading", ['’leading']),
        ("trailing’", ['trailing’']),
        ('"leading', ['leading']),
        ("'QuoTed'", ['QuoTed']),
        ("'", []),
        ("`bwo ", ['bwo']),
        ("a'iy", ["a'iy"]),
        ("ab'b'eh", ["ab'b'eh"]),
        ("aka-iy", ['aka-iy']),
        ("d'Jerusalem", ["d'Jerusalem"]),
        ("Śâulo", ['Śâulo']),
        ("Bârśâbbâś", ['Bârśâbbâś']),
        ('Two Words', ['Two','Words']),
        ('before”after', []),
        ('Yahweh—that', ['Yahweh','that']),  # em dash separates words
        ('laws’—I', ['laws’','I']),     # em dash
        ('double\'--*hyphen', ['double\'', 'hyphen']),
        ("repeat repeat", ['repeat','repeat']),
        ("''abc’’", ["abc"]),     # arguably, should be ["'abc’"]
        ("'[def]’", ['def']),
        ("'()(def))’", ['def']),
        ("’-def!'", ['def']),
        ("’*def`'", ['def']),
        ("['ghi’]", ["'ghi’"]),
        ("('ghi)’)", ["'ghi"]),
        ("’-’ghi'!", ["’ghi'"]),
        ("**’ghi'`", ["’ghi'"]),
        ("asdf8jkl", []),   # digits disqualify
    ])
def test_listwords(s, expected):
    result = verifyUSFM.listwords(s)
    assert result == expected

@pytest.mark.parametrize('s, nchapter, expname',
    [
        ('', 1, ''),
        ('XYZ', 22, 'XYZ'),
        (' Mat ', 33, 'Mat'),
        ('1 Korin', 1, 'Korin'),
        ('1   Korin', 2, '1   Korin'),
        ('1 Korin   1', 1, '1 Korin'),
        ('1   Korin  1', 2, '1   Korin  1'),
        ('2   Korin  1', 2, 'Korin  1'),
        ('1Korin 1', 1, '1Korin'),
        ('1Korin 1', 2, '1Korin 1'),
        ('1Korin 2', 1, '1Korin 2'),
        ('1Korin 2', 2, '1Korin'),
    ])
def test_parseChapterLabel(s, nchapter, expname):
    assert verifyUSFM.parseChapterLabel(s, nchapter) == expname

@pytest.mark.parametrize('s, expected',
    [
        ('', 0),
        ('X3YZ', 0),
        (' 1 ', 1),
        ('1 Korin', 0),
        ('22', 22,),
        ('باب ۱', 0),
        ('۱', 1),
        ('۱۳', 13),
        ('  ۲۴  ', 24),
    ])
def test_decimalvalue(s, expected):
    assert verifyUSFM.decimal_value(s) == expected

@pytest.mark.parametrize('text, expTrigger',
    [
        ('pslm 103:1', ':'),
        # The following test needs more setup: set conpare_dir config value, and call load_source() first.
        # ('nyo konin (kanng Liyar ati nyo).', "MAT 6:13", '('),  # MAT 6:13 is a likely footnote location
        ('nyo konin (kanng Liyar ati nyo).', '('),
        ('ahka, (A khё püng nünah thüm ming sheh.)', '('),
        ('nyo konin [kanng Liyar ati nyo].', '['),
        ('nyo konin [kanng Liyar ati nyo].', '['),
        ('nyo konin kanng Liyar ati nyo.', None),
        ('a hundred thousand (100,000)', None),
        ('first  (second ) third', None),
        ('first [ second ] third', None),
        ('first (second third)', '('),
        ('[11:12]', ':'),
        ('(Jer.13:14) asdf', ':')
    ])
def test_findFootnote(text, expTrigger):
    assert verifyUSFM.findFootnote(text) == expTrigger

@pytest.mark.parametrize('text, expected',
    [
        ('pslm 103:1', False),
        ('Parens (Psalm 103:1).', False),
        ('Brackets [but not reference v.13]', False),
        ('[unmatched bracket COL 4:3', False),
        ('spaces [ MR K 1:44  ]', True),
        ('a hundred thousand [100,000]', False),
    ])
def test_validBracketedFootnote(text, expected):
    assert verifyUSFM.validBracketedFootnote(text) == expected

@pytest.mark.parametrize('fname, expected',
    [
        ('unusual.usfm', False),
        ('41-mat.usfm', False),
        ('A9-GLO.usfm', True),
        ('A1-BAK.usfm', True),
    ])
def test_peripheral(fname, expected):
    assert verifyUSFM.peripheral(fname) == expected

@pytest.mark.parametrize('line, expected',
    [
        (None, None),
        ('', None),
        ('A line, with nothing quoted.', None),
        ('\\v 1 A real, "test"', 'real'),
        ('\\v 2 A colon: «test', 'colon'),
        ('\\v 3 A single quote, \'quotation.\'', None),
        ('\\v 4 A backward, ”quotation.“', None),
    ])
def test_said_word(line, expected):
    word = verifyUSFM.said_word(line)
    assert word == expected

def test_State_versebridges():
    state = State()
    state.addID('MAT')
    state.addChapter('1')
    state.addVerseBridge(1, 3)
    state.addVerse('1')
    assert state.reference == 'MAT 1:1'
    assert state.getReference() == 'MAT 1:1-3'
    state.addChapter('2')
    state.addVerse('20')
    state.addVerseBridge(20, 25)
    assert state.verse == 20
    assert state.reference == 'MAT 2:20'
    assert state.getReference() == 'MAT 2:20-25'

def test_similarity():
    strA = "In the beginning God created the heaven and the earth."
    strB = "In the start God made the heavens and the earth."
    sim, n = verifyUSFM.similarity(strA, strB)
    assert n == 3  # 'the', 'and', 'earth.'
    assert abs(sim - (3 / 11)) < 0.0001  # 5 common words, 13 unique words total
