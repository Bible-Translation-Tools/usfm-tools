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

@pytest.mark.parametrize('str, result',
    [
        ('', False),
        ('This Fine House', True),
        ('\\c 1 \\v 1 this is a verse', False),
        ('\\c 2 St      \v 2 asdfasdf', False),
        ('\\c 3 String Possibility \\v 3', True),
    ])
def test_is_heading(str, result):
    import txt2USFM
    assert txt2USFM.is_heading(str) == result

@pytest.mark.parametrize('str, newstr',
    [
        ('', ''),
        ('This Fine House', '\\s This Fine House'),
        ('   Spaces ', '\\s Spaces '),
        ('\\c 1 \\v 1 this is a verse', ''),
        ('\\c 2 St      \\v 2 asdfasdf', ''),
        ('\\c 3 Common Case #1 \\v 3', '\\c 3 \\s Common Case #1 \\v 3'),
        ('\\c 4\nCommon Case\n\\v 4', '\\c 4\n\\s Common Case\n\\v 4'),
        ('\\c 5\nCommon Case With Space \n\\v 5', '\\c 5\n\\s Common Case With Space \n\\v 5'),
        ('Start section Weak possibility \\v 5', ''),
        ('\\c 6 Strong Possibility    ', '\\c 6 \\s Strong Possibility    '),
        ('\\c 7 Weak possibility', ''),
        ('   \\v 8 No Possibility', ''),
        ('Before Chapter \\c 9 \\v 9 verse. After Verse', ''),
        ('  Strong Possibility   \\v 9 No Possibility \\c 9', '\\s Strong Possibility   \\v 9 No Possibility \\c 9'),
        ('  Don''t Want This To Be a Heading  \\c 1', ''),
        ('Don''t Want This To Be a Heading  \\c 2 ', ''),
        ('\\c 3 \\s Could Be a Heading  \\v 3 ', ''),
        ('\\c 4 Interference By \\p Heading  \\v 4 ', ''),
        ('Orig Heading\n\\v 5 asdf', '\\s Orig Heading\n\\v 5 asdf'),
    ])
def test_mark_section_heading_bos(str, newstr):
    import txt2USFM
    if not newstr:
        newstr = str
    assert txt2USFM.mark_section_heading_bos(str) == newstr

@pytest.mark.parametrize('str, newstr',
    [
        ('', ''),
        ('This Fine House', '\\s This Fine House'),
        ('   Spaces ', '   \\s Spaces '),
        ('\\c 1 \\v 1 this is a verse', ''),
        ('\\c 2 St      \\v 2 asdfasdf', ''),
        ('\\c 3 Strong Possibility \\v 3', ''),
        ('\\c 33 Before Verse \\v 33 After Verse', ''),
        ('\\c 34 Before Verse \\v 34 After Verse. Better Choice', '\\c 34 Before Verse \\v 34 After Verse. \\s Better Choice'),
        ('\\v 35 This is A Verse. \\v 35 Another Verse. Better Choice', '\\v 35 This is A Verse. \\v 35 Another Verse. \\s Better Choice'),
        ('\\v 36 Sentence One. Sentence Two. \\v 36 Another Verse. Better Choice', '\\v 36 Sentence One. Sentence Two. \\v 36 Another Verse. \\s Better Choice'),
        ('\\v 37 Sentence One. Sentence Two. \\v 36 Another Verse Bad Choice', ''),
        ('Strong Possibility \\v 4', ''),   # heading must follow \v marker
        ('Weak possibility \\v 5', ''),
        ('\\c 6 Lame Possibility', ''),   # only one sentence after last usfm marker
        ('\\c 7 Lame Possibility!', ''),
        ('   \\v 8 No Possibility', ''),
        ('Before Chapter\n\\c 9 \\v 9 verse. After Verse', 'Before Chapter\n\\c 9 \\v 9 verse. \\s After Verse'),
        ('  Strong Possibility   \\v 9 No Possibility \\c 9', ''),
        ('  Don''t Want This To Be a Heading  \\c 1', ''),
        ('Don''t Want This To Be a Heading  \\c 2 ', ''),
        ('\\c 3 \\s Heading Already Marked  \\v 3 ', ''),
        ('\\v 4 Is a verse. Could Be a \\ Heading', '\\v 4 Is a verse. \\s Could Be a \\ Heading'),
        ('\\v 3 Here is a verse. Here Is A Candidate \\f + \\ft Footnote \\f*', ''),
    ])
def test_mark_section_heading_eos(str, newstr):
    import txt2USFM
    if not newstr:
        newstr = str
    assert txt2USFM.mark_section_heading_eos(str) == newstr

@pytest.mark.parametrize('str, newstr',
    [
        ('', ''),
        ('This Fine House', '\\s This Fine House'),
        ('   Spaces ', '\\s Spaces'),
        ('\\c 1 \\v 1 verse one.\nThis Is A Section\n\\v 2 second.', '\\c 1 \\v 1 verse one.\n\\s This Is A Section\n\\v 2 second.'),
        ('\\v 3 verse three.\n This Is A Section!  \n\\v 4', '\\v 3 verse three.\n\\s This Is A Section!\n\\v 4'),
        (' This Fine House\n\\v 4 asdf', '\\s This Fine House\n\\v 4 asdf'),
        ('Heading One\n\\v 5 asdf\nHeading Two\nHeading Three', '\\s Heading One\n\\v 5 asdf\nHeading Two\nHeading Three'),
        (' This Fine \\ House\n\\v 6 asdf', ''),
        ('\\v 7 asdf\n  Heading At End ', '\\v 7 asdf\n\\s Heading At End'),
    ])
def test_mark_section_heading_lbi(str, newstr):
    import txt2USFM
    if not newstr:
        newstr = str
    assert txt2USFM.mark_section_heading_lbi(str) == newstr

@pytest.mark.parametrize('str, newstr',
    [
        ('', ''),
        ('This Fine House', '\\s This Fine House'),
        ('   Spaces ', '\\s Spaces '),
        ('\\c 1 \\v 1 verse one.\nThis Is A Section\n\\v 2 second.', '\\c 1 \\v 1 verse one.\n\\s This Is A Section\n\\v 2 second.'),
        ('\\v 3 verse three.\n This Is A Section!  \n\\v 4', '\\v 3 verse three.\n\\s This Is A Section!\n\\v 4'),
        (' This Fine House\n\\v 4 asdf', '\\s This Fine House\n\\v 4 asdf'),
        ('Heading One\n\\v 5 asdf\nHeading Two\nHeading Three', '\\s Heading One\n\\v 5 asdf\nHeading Two\nHeading Three'),
        (' This Fine \\ House\n\\v 6 asdf', '\\s This Fine \\ House\n\\v 6 asdf'),
        ('\\v 7 asdf\n  Heading At End ', '\\v 7 asdf\n\\s Heading At End'),
        ('This Fine House', '\\s This Fine House'),
        ('\\c 1 \\v 1 This is Apostle Paul', ''),
        ('\\c 2 St      \\v 2 asdfasdf', ''),
        ('\\c 3 Common Case #1 \\v 3', '\\c 3 \\s Common Case #1 \\v 3'),
        ('\\c 4\nCommon Case\n\\v 4', '\\c 4\n\\s Common Case\n\\v 4'),
        ('\\c 5\nCommon Case With Space \n\\v 5', '\\c 5\n\\s Common Case With Space \n\\v 5'),
        ('Start section Weak possibility \\v 5', ''),
        ('\\c 6 Strong Possibility    ', '\\c 6 \\s Strong Possibility    '),
        ('\\c 7 Weak possibility', ''),
        ('   \\v 8 No Possibility', ''),
        ('Before Chapter\n\\c 9 \\v 9 verse. After Verse', 'Before Chapter\n\\c 9 \\v 9 verse. \\s After Verse'),
        ('  Strong Possibility   \\v 9 No Possibility \\c 9', '\\s Strong Possibility   \\v 9 No Possibility \\c 9'),
        ('  Don''t Want This To Be a Heading  \\c 1', ''),
        ('Don''t Want This To Be a Heading  \\c 2 ', ''),
        ('\\c 3 \\s Could Be a Heading  \\v 3 ', ''),
        ('\\c 4 Interference By \\p Heading  \\v 4 ', ''),
        ('Orig Heading\n\\v 5 asdf', '\\s Orig Heading\n\\v 5 asdf'),

        ('\\c 33 Before Verse \\v 33 After Verse', '\\c 33 \\s Before Verse \\v 33 After Verse'),
        ('\\c 34 Before Verse \\v 34 After Verse. Better Choice', '\\c 34 \\s Before Verse \\v 34 After Verse. Better Choice'),
        ('\\v 35 This is A Verse. \\v 35 Another Verse. Better Choice', '\\v 35 This is A Verse. \\v 35 Another Verse. \\s Better Choice'),
        ('\\v 36 Sentence One. Sentence Two. \\v 36 Another Verse. Better Choice', '\\v 36 Sentence One. Sentence Two. \\v 36 Another Verse. \\s Better Choice'),
        ('\\v 37 Sentence One. Sentence Two. \\v 36 Another Verse Bad Choice', ''),
        ('Weak possibility \\v 5', ''),
        ('\\c 6 Sane Possibility', '\\c 6 \\s Sane Possibility'),   # only one sentence after last usfm marker
        ('\\c 7 Sane Possibility!', '\\c 7 \\s Sane Possibility!'),
        ('\\c 3 \\s Heading Already Marked  \\v 3 ', ''),
        ('\\v 4 Is a verse. Could Be a \\ Heading', '\\v 4 Is a verse. \\s Could Be a \\ Heading'),
    ])
def test_mark_section_headings(str, newstr):
    import txt2USFM
    if not newstr:
        newstr = str
    assert txt2USFM.mark_section_headings(str) == newstr
