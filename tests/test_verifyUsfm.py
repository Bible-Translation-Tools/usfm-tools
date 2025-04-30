# pytest unit tests for functions in verifyUsfm.py

import os
import sys

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
import pytest
import verifyUSFM

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
    ])
def test_isMixed(word, expected):
    assert verifyUSFM.isMixed(word) == expected

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

@pytest.mark.parametrize('line, exp_marker, exp_payload',
    [
        ('', '', ''),
        ('15 XYZ', '', '15 XYZ'),
        ('\\id mat asdf', 'id', 'mat asdf'),
        ('\\p', 'p', ''),
        ('\\p asdf', 'p', 'asdf'),
        ('\\c 1 asdf', 'c', '1'),
        ('\\v  2', 'v', '2'),
        ('\\v  2-3  asdf', 'v', '2-3'),
        ('\\v 4 asdljasdf asdf\\v 5 asdf', 'v', '4'),
        ('asdfasdf. \\v 5', '', 'asdfasdf. \\v 5'),
    ])
def test_parseLine(line, exp_marker, exp_payload):
    marker, payload = verifyUSFM.parseLine(line)
    assert marker == exp_marker
    assert payload == exp_payload

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

@pytest.mark.parametrize('text, reference, expTrigger',
    [
        ('pslm 103:1', "MAT 6:14", '103:1'),
        # The following test needs more setup: set conpare_dir config value, and call load_source() first.
        # ('nyo konin (kanng Liyar ati nyo).', "MAT 6:13", '('),  # MAT 6:13 is a likely footnote location
        ('nyo konin (kanng Liyar ati nyo).', "MAT 6:14", None),
        ('ahka, (A khё püng nünah thüm ming sheh.)', "MAT 24:15", None),
        ('nyo konin [kanng Liyar ati nyo].', "MAT 6:13", '['),
        ('nyo konin [kanng Liyar ati nyo].', "MAT 6:14", '['),
        ('nyo konin kanng Liyar ati nyo.', "MAT 6:14", None),
        ('a hundred thousand (100,000)', "MAT 6:13", None),
    ])
def test_findFootnote(text, reference, expTrigger):
    assert verifyUSFM.findFootnote(text, reference) == expTrigger

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
