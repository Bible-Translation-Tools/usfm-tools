# Unit tests for parseUsfm and usfmReader.
# Runs parseString on same usfm file(), to assure equivalent output.

import os
import sys
import io
import json
import pytest
from datetime import datetime

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
import parseUsfm
import usfmReader

# usfm_path = r'C:\DCS\usfm-tools\tests\testdata\en_test_39-MAL.usfm'
usfm_path = r'C:\DCS\usfm-tools\tests\testdata\dan_19-PSA.usfm'
# usfm_path = r'C:\DCS\usfm-tools\tests\testdata\fa_43-LUK.usfm'
testdata_path = os.path.dirname(usfm_path)

def test_parseUsfm():
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

def test_usfmReader():
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

# Run this test after successful completion of test_parseUsfm and test_usfmReader.
# It compares the results of the two methods of parsing a usfm file.
def test_compare_files():
    path1 = os.path.join(testdata_path, "usfmParse.txt")
    path2 = os.path.join(testdata_path, "usfmReader.txt")
    with io.open(path1, "tr", encoding="utf-8-sig") as input:
        contents1 = input.readlines()
    with io.open(path2, "tr", encoding="utf-8-sig") as input:
        contents2 = input.readlines()
    assert len(contents1) == len(contents2)
    n = min(len(contents1), len(contents2))
    lineno = 0
    while lineno < n:
        line1 = contents1[n]
        line2 = contents2[n]
        if line1 != line2:
            print(f"Difference at line {n+1}")
        assert line1 == line2

def test_speed():
    with io.open(usfm_path, "tr", encoding="utf-8-sig") as input:
        contents = input.read(-1)

    from line_profiler import LineProfiler
    lp = LineProfiler()
    lp_wrapper = lp(parseUsfm.parseString)
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
     ("\\v 1 Tabe"),
     ("\\p\n"),
     ("\\id phm\n\\ide UTF-8\n\\toc1 Philemon\n\\c 1\n\\v 1 Tabe \n\n"),
     ("\\v 8 Kuki ngandrus.\n(Yohanes Ngandur Yesus)\n"),
     ("\\v 9\\v 10\n"),
     ("\\v 25 Anugerah teke.\\c 2\\v1 verse"),
    ])
def test_parseString(text):
    result1 = parseUsfm.parseString(text)
    result2 = usfmReader.parseString(text)
    print("parseUsfm result:\n")
    for token in result1:
        print(f"{token.type} {token.value}")
    print("\nusfmReader result:\n")
    for token in result2:
        print(f"{token.type} {token.value}")
    assert len(result1) == len(result2)
    for i in range(len(result1)):
        assert result1[i].value == result2[i].value
