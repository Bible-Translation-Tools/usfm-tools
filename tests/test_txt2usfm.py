# pytest unit tests for functions in txt2USFM.py

import os
import sys

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
import pytest

@pytest.mark.parametrize('str, newstr',
    [
        ('', ''),
        ('The house.about.', ''),
        ('\\c', ''),
        ('\\c 10', '\\s5\n\\c 10'),
        ('\\c 9 \\v 9', '\\s5\n\\c 9 \\v 9'),
        ('\n\n\\c 8 \\v 8', '\n\n\\s5\n\\c 8 \\v 8'),
        (' \\v 7 \\c 7', ' \\s5\n\\v 7 \\c 7'),
    ])
def test_mark_chunk(str, newstr):
    import txt2USFM
    if not newstr:
        newstr = str
    assert txt2USFM.mark_chunk(str) == newstr

@pytest.mark.parametrize('str, newstr',
    [
        ('', ''),
        ('This Fine House', '\\s This Fine House\n\\p'),
        ('   Spaces ', '\\s Spaces\n\\p'),
        ('\\c 1 \\v 1 this is a verse', ''),
        ('\\c 2 St      \\v 2 asdfasdf', ''),
        ('\\c 3 Common Case #1 \\v 3', '\\c 3\n\\s Common Case #1\n\\p\n\\v 3'),
        ('\\c 4\nCommon Case\n\\v 4', '\\c 4\n\\s Common Case\n\\p\n\\v 4'),
        ('\\c 5\nCommon Case With Space \n\\v 5', '\\c 5\n\\s Common Case With Space\n\\p\n\\v 5'),
        ('Start section Weak possibility \\v 5', ''),
        ('\\c 6 Strong Possibility    ', '\\c 6\n\\s Strong Possibility\n\\p'),
        ('\\c 7 Weak possibility', ''),
        ('   \\v 8 No Possibility', ''),
        ('Before Chapter \\c 9 \\v 9 verse. After Verse', ''),
        ('  Strong Possibility   \\v 9 No Possibility \\c 9', '\\s Strong Possibility\n\\p\n\\v 9 No Possibility \\c 9'),
        ('  Don''t Want This To Be a Heading  \\c 1', ''),
        ('Don''t Want This To Be a Heading  \\c 2 ', ''),
        ('\\c 3 \\s Could Be a Heading  \\v 3 ', ''),
        ('\\c 4 Interference By \\p Heading  \\v 4 ', ''),
        ('Orig Heading\n\\v 5 asdf', '\\s Orig Heading\n\\p\n\\v 5 asdf'),
        ('\\c 6 Sane Possibility', '\\c 6\n\\s Sane Possibility\n\\p'),
    ])
def test_mark_section_heading_bos(str, newstr):
    import txt2USFM
    if not newstr:
        newstr = str
    assert txt2USFM.mark_section_heading_bos(str) == newstr

@pytest.mark.parametrize('str, wanted',
    [
        ('', ''),
        ('This Fine House', '\\s This Fine House\n\\p'),
        ('   Spaces ', '\\s Spaces\n\\p'),
        ('\\c 1 \\v 1 this is a verse', ''),
        ('\\c 2 St      \\v 2 asdfasdf', ''),
        ('\\c 3 Strong Possibility \\v 3', ''),
        ('\\c 33 Before Verse \\v 33 After Verse', ''),
        ('\\c 34 Before Verse \\v 34 After Verse. Better Choice', '\\c 34 Before Verse \\v 34 After Verse.\n\\s Better Choice\n\\p'),
        ('\\v 35 This is A Verse. \\v 35 Another Verse. Better Choice', '\\v 35 This is A Verse. \\v 35 Another Verse.\n\\s Better Choice\n\\p'),
        ('\\v 36 Sentence One. Sentence Two. \\v 36 Another Verse. Better Choice', '\\v 36 Sentence One. Sentence Two. \\v 36 Another Verse.\n\\s Better Choice\n\\p'),
        ('\\v 37 Sentence One. Sentence Two. \\v 36 Another Verse Bad Choice', ''),
        ('Strong Possibility \\v 4', ''),   # heading must follow \v marker
        ('Weak possibility \\v 5', ''),
        ('\\c 6 Lame Possibility', ''),   # only one sentence after last usfm marker
        ('\\c 7 Lame Possibility!', ''),
        ('   \\v 8 No Possibility', ''),
        ('Before Chapter\n\\c 9 \\v 9 verse.    After Verse', 'Before Chapter\n\\c 9 \\v 9 verse.\n\\s After Verse\n\\p'),
        ('  Strong Possibility   \\v 9 No Possibility \\c 9', ''),
        ('  Don''t Want This To Be a Heading  \\c 1', ''),
        ('Don''t Want This To Be a Heading  \\c 2 ', ''),
        ('\\c 3 \\s Heading Already Marked  \\v 3 ', ''),
        ('\\v 4 Is a verse. Could Be a \\ Heading', '\\v 4 Is a verse.\n\\s Could Be a \\ Heading\n\\p'),
        ('\\v 3 Here is a verse. Here Is A Candidate \\f + \\ft Footnote \\f*', ''),
    ])
def test_mark_section_heading_eos(str, wanted):
    import txt2USFM
    if not wanted:
        wanted = str
    assert txt2USFM.mark_section_heading_eos(str) == wanted

@pytest.mark.parametrize('str, expected',
    [
        ('', ''),
        ('This Fine House', '\\s This Fine House\n\\p'),
        ('   Spaces ', '\\s Spaces\n\\p'),
        ('\\c 1 \\v 1 verse one.\nThis Is A Section\n\\v 2 second.', '\\c 1 \\v 1 verse one.\n\\s This Is A Section\n\\p\n\\v 2 second.'),
        ('\\v 3 verse three.\n This Is A Section!  \n\\v 4', '\\v 3 verse three.\n\\s This Is A Section!\n\\p\n\\v 4'),
        (' This Fine House\n\\v 4 asdf', '\\s This Fine House\n\\p\n\\v 4 asdf'),
        ('Heading One\n\\v 5 asdf\nHeading Two\nHeading Three', '\\s Heading One\n\\p\n\\v 5 asdf\nHeading Two\nHeading Three'),
        (' This Fine \\ House\n\\v 6 asdf', ''),
        ('\\v 7 asdf\n  Heading At End ', '\\v 7 asdf\n\\s Heading At End\n\\p'),
    ])
def test_mark_section_heading_lbi_1(str, expected):
    import txt2USFM
    if not expected:
        expected = str
    assert txt2USFM.mark_section_heading_lbi(str, False) == expected

@pytest.mark.parametrize('str, expected',
    [
        ('', ''),
        ('This Fine House', ''),
        ('   Spaces ', ''),
        ('   Spaces \nLast Line', '\\s Spaces\n\\p\nLast Line'),
        ('\\c 1 \\v 1 verse one.\nThis Is A Section\n\\v 2 second.', '\\c 1 \\v 1 verse one.\n\\s This Is A Section\n\\p\n\\v 2 second.'),
        ('\\v 3 verse three.\n This Is A Section!  \n\\v 4', '\\v 3 verse three.\n\\s This Is A Section!\n\\p\n\\v 4'),
        (' This Fine House\n\\v 4 asdf', '\\s This Fine House\n\\p\n\\v 4 asdf'),
        ('Heading One\n\\v 5 asdf\nHeading Two\nHeading Three', '\\s Heading One\n\\p\n\\v 5 asdf\nHeading Two\nHeading Three'),
        (' This Fine \\ House\n\\v 6 asdf', ''),
        ('\\v 7 asdf\n  Heading At End ', ''),
    ])
def test_mark_section_heading_lbi_2(str, expected):
    import txt2USFM
    if not expected:
        expected = str
    assert txt2USFM.mark_section_heading_lbi(str, True) == expected

@pytest.mark.parametrize('str, newstr',
    [
        ('', ''),
        ('This Fine House', '\\s This Fine House\n\\p'),
        ('   Spaces ', '\\s Spaces\n\\p'),
        ('\\c 1 \\v 1 verse one.\nThis Is A Section\n\\v 2 second.', '\\c 1 \\v 1 verse one.\n\\s This Is A Section\n\\p\n\\v 2 second.'),
        ('\\v 3 verse three.\n This Is A Section!  \n\\v 4', '\\v 3 verse three.\n\\s This Is A Section!\n\\p\n\\v 4'),
        (' This Fine House\n\\v 4 asdf', '\\s This Fine House\n\\p\n\\v 4 asdf'),
        ('Heading One\n\\v 5 asdf\nHeading Two\nHeading Three', '\\s Heading One\n\\p\n\\v 5 asdf\nHeading Two\nHeading Three'),
        (' This Fine \\ House\n\\v 6 asdf', '\\s This Fine \\ House\n\\p\n\\v 6 asdf'),
        ('\\v 7 asdf\n  Heading At End ', '\\v 7 asdf\n\\s Heading At End\n\\p'),
        ('This Fine House', '\\s This Fine House\n\\p'),
        ('\\c 1 \\v 1 This is Apostle Paul', ''),
        ('\\c 2 St      \\v 2 asdfasdf', ''),
        ('\\c 3 Common Case #1 \\v 3', '\\c 3\n\\s Common Case #1\n\\p\n\\v 3'),
        ('\\c 4\nCommon Case\n\\v 4', '\\c 4\n\\s Common Case\n\\p\n\\v 4'),
        ('\\c 5\nCommon Case With Space \n\\v 5', '\\c 5\n\\s Common Case With Space\n\\p\n\\v 5'),
        ('Start section Weak possibility \\v 5', ''),
        ('\\c 6 Strong Possibility    ', '\\c 6\n\\s Strong Possibility\n\\p'),
        ('\\c 7 Weak possibility', ''),
        ('   \\v 8 No Possibility', ''),
        ('\\c 9\nWord One\nWord Two\n\\v 9 asdf', '\\c 9\n\\s Word One\n\\p\nWord Two\n\\v 9 asdf'),
        ('Before Chapter\n\\c 9 \\v 9 verse. After Verse', 'Before Chapter\n\\c 9 \\v 9 verse.\n\\s After Verse\n\\p'),
        ('  Strong Possibility   \\v 9 No Possibility \\c 9', '\\s Strong Possibility\n\\p\n\\v 9 No Possibility \\c 9'),
        ('  Don''t Want This To Be a Heading  \\c 1', ''),
        ('Don''t Want This To Be a Heading  \\c 2 ', ''),
        ('\\c 3 \\s Could Be a Heading\n\\p\n\\v 3 ', ''),
        ('\\c 4 Interference By \\p Heading  \\v 4 ', ''),
        ('Orig Heading\n\\v 5 asdf', '\\s Orig Heading\n\\p\n\\v 5 asdf'),
        ('\\c 33 Before Verse \\v 33 After Verse', '\\c 33\n\\s Before Verse\n\\p\n\\v 33 After Verse'),
        ('\\c 34 Before Verse \\v 34 After Verse. Better Choice', '\\c 34\n\\s Before Verse\n\\p\n\\v 34 After Verse.\n\\s Better Choice\n\\p'),
        ('\\v 35 This is A Verse. \\v 35 Another Verse. Better Choice', '\\v 35 This is A Verse. \\v 35 Another Verse.\n\\s Better Choice\n\\p'),
        ('\\v 36 Sentence One. Sentence Two. \\v 36 Another Verse. Better Choice', '\\v 36 Sentence One. Sentence Two. \\v 36 Another Verse.\n\\s Better Choice\n\\p'),
        ('\\v 37 Sentence One. Sentence Two. \\v 36 Another Verse Bad Choice', ''),
        ('Weak possibility \\v 5', ''),
        ('\\c 6 Sane Possibility', '\\c 6\n\\s Sane Possibility\n\\p'),   # only one sentence after last usfm marker
        ('\\c 7 Sane Possibility!', '\\c 7\n\\s Sane Possibility!\n\\p'),
        ('\\c 3\n\\s Heading Already Marked\n\\p\n\\v 3 ', ''),
        ('\\v 4 Is a verse. Could Be a \\ Heading', '\\v 4 Is a verse.\n\\s Could Be a \\ Heading\n\\p'),
        ('at the end of a verse. Amen.', '')
    ])
# Call mark_section_headings() with the lastchunk parameter False
def test_mark_section_headings_1(str, newstr):
    import txt2USFM
    if not newstr:
        newstr = str
    assert txt2USFM.mark_section_headings(str, False) == newstr

@pytest.mark.parametrize('str, newstr',
    [
        ('', ''),
        ('This Fine House', '\\s This Fine House\n\\p'),
        ('   Spaces ', '\\s Spaces\n\\p'),
        ('\\v 3 verse three.\n This Is A Section!  \n\\v 4', '\\v 3 verse three.\n\\s This Is A Section!\n\\p\n\\v 4'),
        (' This Fine House\n\\v 4 asdf', '\\s This Fine House\n\\p\n\\v 4 asdf'),
        ('Heading One\n\\v 5 asdf\nHeading Two\nHeading Three', '\\s Heading One\n\\p\n\\v 5 asdf\nHeading Two\nHeading Three'),
        (' This Fine \\ House\n\\v 6 asdf', '\\s This Fine \\ House\n\\p\n\\v 6 asdf'),
        ('\\v 7 asdf\n  Heading At End ', ''),
        ('This Fine House', '\\s This Fine House\n\\p'),
        ('Start section Weak possibility \\v 5', ''),
        ('   \\v 8 No Possibility', ''),
        ('Orig Heading\n\\v 5 asdf', '\\s Orig Heading\n\\p\n\\v 5 asdf'),
        ('\\v 35 This is A Verse. \\v 35 Another Verse. Better Choice', ''),
        ('\\v 36 Sentence One. Sentence Two. \\v 36 Another Verse. Better Choice', ''),
        ('\\v 37 Sentence One. Sentence Two. \\v 36 Another Verse Bad Choice', ''),
        ('Weak possibility \\v 5', ''),
        ('\\v 4 Is a verse. Could Be a \\ Heading', ''),
        ('at the end of a verse.\nAmen Amen.', '')
    ])
# Call mark_section_headings() with the lastchunk parameter True
def test_mark_section_headings_2(str, newstr):
    import txt2USFM
    if not newstr:
        newstr = str
    assert txt2USFM.mark_section_headings(str, True) == newstr
