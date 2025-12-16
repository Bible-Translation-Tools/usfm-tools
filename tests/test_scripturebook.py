# pytest unit tests for ToolsConfigManager

import os
import sys
import pytest
# import shutil

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
from scripturebook import ScriptureBook

def test_getErrors():
    ruth = ScriptureBook(r'C:\DCS\Test\test_scripturebook\08-RUT.usfm')
    assert ruth.getErrors() == []
    ruth = ScriptureBook(r'C:\DCS\Test\test_scripturebook\08-RUTABEGA.usfm')
    assert len( ruth.getErrors() ) == 1
    assert "Unable to open" in ruth.getErrors()[0]

def test_getBookInfo():
    ruth = ScriptureBook(r'C:\DCS\Test\test_scripturebook\08-RUT.usfm')
    assert ruth.getBookId() == 'RUT'
    assert ruth.getBookLength() == 13887
    assert ruth.getChunkCount() == 38
    assert ruth.getVerseCount(1) == 22
    assert ruth.getVerseCount(3) == 18
    assert ruth.getVerseCount(5) == 0

@pytest.mark.parametrize('chapter, verse, expected',
    [
        (1, 3, "ଏଉତ୍ତାରୁ ନୟମୀର ସ୍ୱାମୀ ଏଲିମେଲକର ମୃତ୍ୟୁୁ ହୁଅନ୍ତେ, ସେ ଓ ତାହାର ଦୁଇ ପୁତ୍ର ଅବଶିଷ୍ଟ ରହିଲେ।"),
        (1, 5, "ତହୁଁ ମହଲୋନ ଓ କିଲୀୟୋନ ଦୁଇ ଜଣଙ୍କର ମୃତ୍ୟୁୁ ହୁଅନ୍ତେ, ସେ ସ୍ତ୍ରୀ, ଦୁଇ ପୁତ୍ରବଧୂ ଓ ସ୍ୱାମୀବିହୀନା ହୋଇ ରହିଲା।"),
        (2, 17, "ତହିଁରେ ସେ ସନ୍ଧ୍ୟା ପର୍ଯ୍ୟନ୍ତ ସେହି କ୍ଷେତ୍ରରେ ବଳକା ଶସ୍ୟ ସଂଗ୍ରହ କଲା; ପୁଣି ନିଜ ସାଉଣ୍ଟିଲା ଶସ୍ୟ ମଳନ୍ତେ, ପ୍ରାୟ ଏକ ଐଫା ଯବ ହେଲା।"),
        (3, 9, "ସେ ଉତ୍ତର କଲା, “ମୁଁ ଆପଣଙ୍କର ଦାସୀ ରୂତ; ଏଣୁ ନିଜ ଚାଦର ଆପଣଙ୍କ ଦାସୀ ଉପରେ ବିସ୍ତାର କରନ୍ତୁ, କାରଣ ଆପଣ ମୁକ୍ତିକର୍ତ୍ତା ଜ୍ଞାତି ଅଟନ୍ତି।”"),
        (4, 0, ""),
    ])
def test_getText(chapter, verse, expected):
    ruth = ScriptureBook(r'C:\DCS\Test\test_scripturebook\08-RUT.usfm')
    text = ruth.getText(chapter, verse)
    assert text == expected

@pytest.mark.parametrize('chapter, verse, expected',
    [
        (1, 3, ""),
        (2, 17, "2:17 ଏକ ଐଫା ପ୍ରାୟ ୧୨ କିଲୋ "),
        (3, 9, "3:9 ଏଣୁ ନିଜ ପକ୍ଷ ଆପଣଙ୍କ ଦାସୀ ଉପରେ ବିସ୍ତାର କରନ୍ତୁ, ଅର୍ଥାତ୍ ମୋତେ ବିବାହ କର ")
    ])
def test_getFootnote(chapter, verse, expected):
    ruth = ScriptureBook(r'C:\DCS\Test\test_scripturebook\08-RUT.usfm')
    text = ruth.getFootnote(chapter, verse)
    assert text == expected

@pytest.mark.parametrize('chapter, verse, expected_mark, expected_punct',
    [
        (0, 0, "", ""),
        (1, 1, "p", ""),
        (1, 2, "p", "।"),
        (1, 3, "", ""),
        (1, 12, "p", "।"),
        (1, 13, "", ""),
        (1, 18, "", ""),
        (2, 2, "q1", "।"),
        (4, 16, "p", "।"),
        (5, 1, "p", "।"),
        (5, 2, "p", "।"),
    ])
def test_getPmark(chapter, verse, expected_mark, expected_punct):
    ruth = ScriptureBook(r'C:\DCS\Test\test_scripturebook\22-SNG.usfm')
    pmark, punct = ruth.getPmark(chapter, verse)
    assert pmark == expected_mark
    assert punct == expected_punct

@pytest.mark.parametrize('chapter, verse, expected_mark, expected_punct',
    [
        (0, 0, "s5", ""),
        (1, 0, "s", ""),
        (1, 2, "s", "।"),   # "s" because only the first section mark after a verse is saved
        (1, 27, "", ""),
        (2, 0, "s1", "।"),
    ])
def test_getSmark(chapter, verse, expected_mark, expected_punct):
    ruth = ScriptureBook(r'C:\DCS\Test\test_scripturebook\51-PHP.usfm')
    smark, punct = ruth.getSmark(chapter, verse)
    assert smark == expected_mark
    assert punct == expected_punct
