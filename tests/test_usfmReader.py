# Unit tests for parseUsfm and usfmReader.
# Runs parseString on same usfm file(), to assure equivalent output.

import os
import sys
import io
import pytest
from datetime import datetime

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
import parseUsfm
import usfmReader

# usfm_path = r'C:\DCS\usfm-tools\tests\testdata\en_test_39-MAL.usfm'
# usfm_path = r'C:\DCS\usfm-tools\tests\testdata\dan_19-PSA.usfm'
# usfm_path = r'C:\DCS\usfm-tools\tests\testdata\fa_43-LUK.usfm'
# usfm_path = r'C:\DCS\usfm-tools\tests\testdata\en_test_41-MAT.usfm'
usfm_path = r'C:\DCS\usfm-tools\tests\testdata\_nadroga_42-MRK.usfm'
testdata_path = os.path.dirname(usfm_path)

def parse_using_parseUsfm():
    with io.open(usfm_path, "tr", encoding="utf-8-sig") as input:
        contents = input.read(-1)
    tokens = parseUsfm.parseString(contents)

    dumppath = os.path.join(testdata_path, "usfmParse.txt")
    if os.path.exists(dumppath):
        timestamp = get_timestamp(dumppath)
        bakpath = os.path.join(testdata_path, f"usfmParse-{timestamp}.txt")
        if not os.path.exists(bakpath):
            os.rename(dumppath, bakpath)
    with io.open(dumppath, 'w', encoding="utf-8", newline='\n') as file:
        for token in tokens:
            try:
                file.write(f"{token.type} {token.value}\n")
            except UnicodeDecodeError as e:
                file.write(str(e))

def parse_using_usfmReader():
    with io.open(usfm_path, "tr", encoding="utf-8-sig") as input:
        contents = input.read(-1)
    tokens = usfmReader.parseString(contents)

    dumppath = os.path.join(testdata_path, "usfmReader.txt")
    if os.path.exists(dumppath):
        timestamp = get_timestamp(dumppath)
        bakpath = os.path.join(testdata_path, f"usfmReader-{timestamp}.txt")
        if not os.path.exists(bakpath):
            os.rename(dumppath, bakpath)
    with io.open(dumppath, 'w', encoding="utf-8", newline='\n') as file:
        for token in tokens:
            try:
                file.write(f"{token.type} {token.value}\n")
            except UnicodeDecodeError as e:
                file.write(str(e))

# It compares the results of the two methods of parsing a usfm file.
# I quit using this as a unit test because there are intentional differences.
def omit_test_compare_files():
    parse_using_parseUsfm()
    parse_using_usfmReader()
    path1 = os.path.join(testdata_path, "usfmParse.txt")
    path2 = os.path.join(testdata_path, "usfmReader.txt")
    with io.open(path1, "tr", encoding="utf-8-sig") as input:
        contents1 = input.readlines()
    with io.open(path2, "tr", encoding="utf-8-sig") as input:
        contents2 = input.readlines()
    assert len(contents1) == len(contents2)
    n = min(len(contents1), len(contents2))
    lineno = 0
    ndiffs = 0
    while lineno < n:
        line1 = contents1[lineno]
        line2 = contents2[lineno]
        lineno += 1
        if line1.rstrip() != line2.rstrip():
            print(f"Difference at line {lineno}")
            ndiffs += 1
        assert ndiffs == 0

def test_speed():
    with io.open(usfm_path, "tr", encoding="utf-8-sig") as input:
        contents = input.read(-1)

    from line_profiler import LineProfiler
    lp = LineProfiler()
    lp_wrapper = lp(usfmReader.parseString)
    lp_wrapper(contents)
    lp.print_stats()

if __name__ == "__main__":
    test_speed()

# Returns the modified date/time of the specified file, formatted as a string.
def get_timestamp(path):
    mtime = os.path.getmtime(path)
    dt = datetime.fromtimestamp(mtime)
    s = dt.strftime("%Y%m%d%H%M")
    return s[2:]

@pytest.mark.parametrize('text',
    [('Sentence 1. next sentence 2.'),
    #  ("\\c 1"),     # parseUsfm fails because it requires space or newline at end of string
    #  ('\\v '),   # parseUsfm returns ('unknown', 'v'); usfmReader returns ('v', '')
    #  ('\\v asdf\n'),   # parseUsfm returns ('unknown', 'v'); usfmReader returns ('v', '')
    #  ('\\c x '),     # parseUsfm returns ('unknown', 'c'); usfmReader returns ('c', '')
    #  ('\\v 15Start right in'),  # parseUsfm return ('unknown', 'v'); usfmReader returns ('v', '')
     ("\\id ROM Romans\n"),
    #  ("\\c 1\\1 asdf"),     # parseUsfm returns ('unknown','c') usfmReader returns ('c', '1')
     ("\\v 1 Tabe"),
     ("\\p\n"),
     ("\\toc1 Philemon\n\\c 1\n"),
     ("\\id phm\n\\ide UTF-8\n\\toc1 Philemon\n\\c 1\n\\v 1 Tabe \n\n"),
     ("\\v 8 Kuki ngandrus.\n(Yohanes Ngandur Yesus)\n"),
    #  ("\\v 9\\v 10\n"),   parseUsfm returns ('unknown', 'v'); usfmReader returns ('v', '')
    #  ("\\v 25 Anugerah teke.\\c 2\\v1 verse"),  # parseUsfm returns "unknown"s for c and v1
     ("\\s Heading\\p\n\\v 4 Four"),
     ("\\toc1 Philemon\n\\c 1\n"),
     ("\\v 20\n"),
    #  ("\\v 20Jammed"),    # parseUfm ('unknown', 'v')
    #  ("\\v notnumeric text"),  # parseUfm ('unknown', 'v')
     ("\\v 21 \\f + \\ft asdf"),
     ("\\v 22-23 asdf"),
     ("\\p asdf"),
     ("\\cl asdf\n\\p  \n\\v 1 asdf"),
     ("\\cl "),
    #  ("\\pasdf"),   # parseUsfm returns ('unknown', 'pasdf'); usfmReader returns ('text', '\pasdf')
     ("\\cl asdf\n\\p  \n\\p asdf"),
     ("\\p \\p\n"),
    #  ("asdf \\f + \\ft asdf \\fqa asdf \\fqa*\\f*\n"),  # parseUmfm accepts \fqa* as a valid usfm marker
    #  ("\\f + \\fqa asdf \\+it qwer\\it*\\fqa*"),    # parseUsfm doesn't recognize \it...\it*
    ])
def test_parseString(text):
    result1 = parseUsfm.parseString(text)
    result2 = usfmReader.parseString(text)
    print("parseUsfm result:")
    for token in result1:
        print(f"{token.type} {token.value}")
    print("\nusfmReader result:")
    for token in result2:
        print(f"{token.type} {token.value}")
    assert len(result1) == len(result2)
    for i in range(len(result1)):
        assert result1[i].value.rstrip() == result2[i].value.rstrip()

@pytest.mark.parametrize('text, expectedtypes',
    [('Sentence 1. next sentence 2.', ['text']),
     ("\\c 1", ['c']),
     ("\\c 1\\v 1 asdf", ['c','v','text']),
     ("\\c 1\\1 asdf", ['c','text']),
     ("\\id ROM Romans", ['id']),
     ('\\v ', ['v']),
     ('\\v asdf\n', ['v','text']),
     ('\\c x ', ['c','text']),
     ('\\v 15Start right in', ['v','text']),
     ("\\v 1 Tabe", ['v','text']),
     ("\\p\n", ['p']),
     ("\\id phm\n\\ide UTF-8\n\\toc1 Philemon\n\\c 1\n\\v 1 Tabe \n\n", ['id','ide','toc1','c','v','text']),
     ("\\v 8 Kuki ngandrus.\n(Yohanes Ngandur Yesus)\n", ['v','text','text']),
     ("\\v 9\\v 10\n", ['v','v']),
     ("\\v 25 Anugerah teke.\\c 2\\v1 verse", ['v','text','c','text']),
     ("\\s Heading\\p\n\\v 4 Four", ['s','p','v','text']),
     ("\\toc1 Philemon\n\\c 1\n", ['toc1','c']),
     ("\\v 20", ['v']),
     ("\\v 20Jammed", ['v', 'text']),
     ("\\v notnumeric text", ['v', 'text']),
     ("\\v 21 \\f + \\ft", ['v','f','ft']),
     ("\\v 22-23 asdf", ['v','text']),
     ("\\p asdf", ['p','text']),
     ("\\cl asdf\n\\p  \n\\v 1 asdf", ['cl', 'p', 'v', 'text']),
     ("\\cl", ['cl']),
     ("\\pasdf", ['text']),
     ("\\cl asdf\n\\p  \n\\p asdf", ['cl','p','p','text']),
     ("\\p \\p\n", ['p','p']),
     ("asdf \\f + \\ft asdf \\fqa asdf \\fqa*\\f*\n", ['text','f', 'ft', 'fqa', 'f*']),
     ("\\f + \\fqa asdf\\+em qwer\\em*\\fqa*", ['f', 'fqa', '+em', 'em*', 'text']),
    ])
def test_usfmReader_parseString(text, expectedtypes):
    tokens = usfmReader.parseString(text)
    for token in tokens:
        assert token.type in usfmReader.all_markers
        print(token)
    assert len(tokens) == len(expectedtypes)
    types = [token.type for token in tokens]
    assert types == expectedtypes

@pytest.mark.parametrize('text, expectedtypes, expectedvalues',
    [('Sentence 1. next sentence 2.', ['text'], ['Sentence 1. next sentence 2.']),
     ("\\c 1", ['c'], [' 1']),
     ("\\c 2\\v 1 asdf", ['c','v'], []),
     ("\\c 3\\1 asdf", ['c'], []),
     ("\\c 4\n\\5 \\v 1 asdf", ['c','text','v'], [' 4', '\\5 ', ' 1 asdf']),
     ("\\c 5\\1\n asdf", ['c','text'], [' 5\\1', ' asdf']),
     ("\\id ROM Romans", ['id'], [' ROM Romans']),
     ("\\5 6", ['text'], []),
     ("", [], []),
     ('\\v ', ['v'], [' ']),
     ('\\v asdf\n\n\n\\p\n\\v 6 asdf', ['v','p','v'], [' asdf', '', ' 6 asdf']),
     ('\\c x ', ['c'], [' x ']),
     ('\\v 15Start right in ', ['v'], [' 15Start right in ']),
     ("\\v 1 Tabe", ['v'], []),
     ("\\p   \n", ['p'], ['   ']),
     ("\\id phm\n\\ide UTF-8\n\\toc1 Philemon\n\\c 1\n\\v 1 Tabe \n\n", ['id','ide','toc1','c','v'], []),
     ("\\v 8 Kuki ngandrus.\n(Yohanes Ngandur Yesus)\n", ['v','text'], []),
     ("\\v 9\\v 10\n", ['v','v'], [' 9',' 10']),
     ("\\v 25 Anugerah teke.\\c 2\\v1 verse", ['v','c'], [' 25 Anugerah teke.', ' 2\\v1 verse']),
     ("\\s Heading\\p\n\\v 4 Four", ['s','p','v'], []),
     ("\\toc1 Philemon\n\\c 1\n", ['toc1','c'], []),
     ("\\c\n", ['c'], []),
     ("\\c2 2\n", ['text'], ['\\c2 2']),
     ("\\f + \\ft Instead of \\fqa rebuke \\fqa*", ['f','ft','fqa'], []),
     ("\\fqa*", ['text'], ['\\fqa*']),
     ("\\v 21 \\f + \\ft", ['v','f','ft'], [' 21 ', ' + ', '']),
     ("\\v 27\n\\Ni mata lawa ", ['v','text'], [' 27', '\\Ni mata lawa ']),
     ("asdf \\f + \\ft asdf \\fqa asdf\\fqa*\\f*\n", ['text','f', 'ft','fqa','f*'], ['asdf ', ' + ', ' asdf ', ' asdf\\fqa*', '']),
     ("\\f + \\fqa asdf\\+em qwer\\em*\\fqa*", ['f','fqa','+em','em*'], []),
     ("\\fqa* asdf", ['text'], ['\\fqa* asdf']),
     (" \\fqa* asdf", ['text'], [' \\fqa* asdf']),
     ("\\rem filename.docx", ["rem"], [' filename.docx']),
     ("\\s Heading.10", ["s"], [' Heading.10']),
    ])
def test_nextpair(text, expectedtypes, expectedvalues):
    types = []
    values = []
    for token in usfmReader.nextpair(text):
        assert token.type in usfmReader.all_markers
        types.append(token.type)
        values.append(token.value)
        print(token)
    assert len(types) == len(expectedtypes)
    assert types == expectedtypes
    if expectedvalues:
        assert values == expectedvalues

@pytest.mark.parametrize('text, expected',
    [('Sentence 1. next sentence 2.', []),
     ("\\c 1", [('c',0)]),
     ("\\em asdf", [('em', 0)]),
     ("\\+em asdf", [('+em', 0)]),
     (" asdf\\+em*", [('+em*', 5)]),
     ("x\\fqa", [('fqa',1)]),
     ("\\xyz* asdf", []),
     (" \\xyz asdf", []),
     ("\\c 1 \\v 1 \\p\n", [('c',0), ('v',5), ('p',10)]),
     ("\\f + \\fqa asdf\\+em qwer\\+em*\\fqa*", [('f',0), ('fqa',5), ('+em',14), ('+em*',23)]),
     ("\\fqa* asdf", []),
     (" \\q3 asdf", [('q3',1)]),
    ])
def test_list_usfm(text, expected):
    usfms = usfmReader.list_usfm(text)
    for usfm in usfms:
        print(usfm)
    assert len(usfms) == len(expected)
    m = min(len(usfms), len(expected))
    for n in range(m):
        assert usfms[n] == expected[n]
