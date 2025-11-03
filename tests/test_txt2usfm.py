# pytest unit tests for functions in txt2USFM.py

import io
import os
import sys

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
import pytest
import txt2USFM

@pytest.mark.parametrize('section, newstr',
    [
        ('', ''),
        ('The house.about.', ''),
        ('\\c', ''),
        ('\\c 10', '\\s5\n\\c 10'),
        ('\\c 9 \\v 9', '\\s5\n\\c 9 \\v 9'),
        ('\n\n\\c 8 \\v 8', '\n\n\\s5\n\\c 8 \\v 8'),
        (' \\v 7 \\c 7', ' \\s5\n\\v 7 \\c 7'),
    ])
def test_mark_chunk(section, newstr):
    if not newstr:
        newstr = section
    assert txt2USFM.mark_chunk(section) == newstr

@pytest.mark.parametrize('section, newstr',
    [
        ('', ''),
        ('This Fine House', '\\s This Fine House\n\\p\n'),
        ('   Spaces ', '\\s Spaces\n\\p\n'),
        ('\\c 1 \\v 1 this is a verse', ''),
        ('\\c 2 St      \\v 2 asdfasdf', ''),
        ('\\c 3 Hashed Mark #1 \\v 3', ''),
        ('\\c 3 Two-Thirds Case #1 \\v 3', ''),
        ('\\c 3 Three-Fourths New Case #1 \\v 3', '\\c 3\n\\s Three-Fourths New Case #1\n\\p\n\\v 3'),
        ('\\c 4\nCommon Case\n\\v 4', '\\c 4\n\\s Common Case\n\\p\n\\v 4'),
        ('\\c 5\nCommon Case With Space \n\\v 5', '\\c 5\n\\s Common Case With Space\n\\p\n\\v 5'),
        ('Start section Weak possibility \\v 5', ''),
        ('\\c 6 Strong Possibility    ', '\\c 6\n\\s Strong Possibility\n\\p\n'),
        ('\\c 7 Weak possibility', ''),
        ('   \\v 8 No Possibility', ''),
        ('Before Chapter \\c 9 \\v 9 verse. After Verse', ''),
        ('  Strong Possibility   \\v 9 No Possibility \\c 9', '\\s Strong Possibility\n\\p\n\\v 9 No Possibility \\c 9'),
        ('  Don''t Want This To Be a Heading  \\c 1', ''),
        ('Don''t Want This To Be a Heading  \\c 2 ', ''),
        ('\\c 3 \\s Could Be a Heading  \\v 3 ', ''),
        ('\\c 4 Interference By \\p Heading  \\v 4 ', ''),
        ('Orig Heading\n\\v 5 asdf', '\\s Orig Heading\n\\p\n\\v 5 asdf'),
        ('\\c 6 Sane Possibility', '\\c 6\n\\s Sane Possibility\n\\p\n'),
        ('\\c 7 (Parenthesized Heading) \\v 7', '\\c 7\n\\s Parenthesized Heading\n\\p\n\\v 7'),
        ('\\c 8 (Parens Last lowcase) \\v 8', ''),
        ('\\c 9 Talalu Kalimana Halege (Kawungana)', '\\c 9\n\\s Talalu Kalimana Halege (Kawungana)\n\\p\n'),
        ('\\c 20\nOlukaado Lwabakhosi Mu Ndalo. \n\n\\v 1 “Khulwokhuba ', '\\c 20\n\\s Olukaado Lwabakhosi Mu Ndalo.\n\\p\n\\v 1 “Khulwokhuba '),
        ('\\c 5\nOkhuwuulira Khu lugulu\n\\v 1 Yesu ni kawona ', ''),   # last word uncapitalized
        ('\\c 1 Silsilah Yesus Kristus \\v 1 Kitab silsilah Yesus', '\\c 1\n\\s Silsilah Yesus Kristus\n\\p\n\\v 1 Kitab silsilah Yesus')
    ])
def test_mark_heading_bos(section, newstr):
    if not newstr:
        newstr = section
    assert txt2USFM.mark_section_heading_bos(section) == newstr

@pytest.mark.parametrize('section, wanted',
    [
        ('', ''),
        ('This Fine House', '\\s This Fine House\n\\p\n'),
        ('   Spaces ', '\\s Spaces\n\\p\n'),
        ('\\c 1 \\v 1 this is a verse', ''),
        ('\\c 2 St      \\v 2 asdfasdf', ''),
        ('\\c 3 Strong Possibility \\v 3', ''),
        ('\\c 33 Before Verse \\v 33 After Verse', ''),
        ('\\c 34 Before Verse \\v 34 After Verse. Better Choice', '\\c 34 Before Verse \\v 34 After Verse.\n\\s Better Choice\n\\p\n'),
        ('\\v 35 This is A Verse. \\v 35 Another Verse. Better Choice', '\\v 35 This is A Verse. \\v 35 Another Verse.\n\\s Better Choice\n\\p\n'),
        ('\\v 36 Sentence One. Sentence Two. \\v 36 Another Verse. Better Choice', '\\v 36 Sentence One. Sentence Two. \\v 36 Another Verse.\n\\s Better Choice\n\\p\n'),
        ('\\v 37 Sentence One. Sentence Two. \\v 36 Another Verse Bad Choice', ''),
        ('Strong Possibility \\v 4', ''),   # heading must follow \v marker
        ('Weak possibility \\v 5', ''),
        ('\\c 6 Lame Possibility', ''),   # only one sentence after last usfm marker
        ('\\c 7 Lame Possibility!', ''),
        ('   \\v 8 No Possibility', ''),
        ('Before Chapter\n\\c 9 \\v 9 verse.    After Verse', 'Before Chapter\n\\c 9 \\v 9 verse.\n\\s After Verse\n\\p\n'),
        ('  Strong Possibility   \\v 9 No Possibility \\c 9', ''),
        ('  Don''t Want This To Be a Heading  \\c 1', ''),
        ('Don''t Want This To Be a Heading  \\c 2 ', ''),
        ('\\c 3 \\s Heading Already Marked  \\v 3 ', ''),
        ('\\v 4 Is a verse. Could Be a \\ Heading', '\\v 4 Is a verse.\n\\s Could Be a \\ Heading\n\\p\n'),
        ('\\v 3 Here is a verse. Here Is A Candidate \\f + \\ft Footnote \\f*', ''),
        ('mu syaki syange.’” Olukaado Lw’omuyofu', 'mu syaki syange.’”\n\\s Olukaado Lw’omuyofu\n\\p\n'),
        ('\\f + \\ft Footnote.\\f* Postfootnote', ''),  # only one sentence after last usfm marker
    ])
def test_mark_heading_eos(section, wanted):
    if not wanted:
        wanted = section
    assert txt2USFM.mark_section_heading_eos(section) == wanted

@pytest.mark.parametrize('section, expected',
    [
        ('', ''),
        ('This Fine House', '\\s This Fine House\n\\p\n'),
        ('   Spaces ', '\\s Spaces\n\\p\n'),
        ('\\c 1 \\v 1 verse one.\nThis Is A Section\n\\v 2 second.',
         '\\c 1 \\v 1 verse one.\n\\s This Is A Section\n\\p\n\\v 2 second.'),
        ('\\v 3 verse three.\n This Is Exclamation!  \n\\v 4', '\\v 3 verse three.\n\\s This Is Exclamation!\n\\p\n\\v 4'),
        (' This Fine House\n\\v 4 asdf', '\\s This Fine House\n\\p\n\\v 4 asdf'),
        ('Heading One\n\\v 5 asdf\nHeading Two\nHeading Three', '\\s Heading One\n\\p\n\\v 5 asdf\nHeading Two\nHeading Three'),
        (' This Fine \\ House\n\\v 6 asdf', ''),
        ('\\v 7 asdf\n  Heading At End ', '\\v 7 asdf\n\\s Heading At End\n\\p\n'),
        ('wakiiye awo.\nOkhulangiwa Khwa Matayo\n\\v 9 Nga Yesu lukali', 'wakiiye awo.\n\\s Okhulangiwa Khwa Matayo\n\\p\n\\v 9 Nga Yesu lukali')
    ])
def test_mark_heading_lbi_1(section, expected):
    # Tests for heading recognition in a line-by-itself, NOT at the end of a chapter
    if not expected:
        expected = section
    result = txt2USFM.mark_section_heading_lbi(section, 'REV 22:8', False)
    assert result == expected

@pytest.mark.parametrize('section, expected',
    [
        ('', ''),
        ('This Fine House', ''),
        ('   Spaces ', ''),
        ('   Spaces \nLast Line', '\\s Spaces\n\\p\nLast Line'),
        ('\\c 1 \\v 1 verse one.\nThis Is A Section\n\\v 2 second.', '\\c 1 \\v 1 verse one.\n\\s This Is A Section\n\\p\n\\v 2 second.'),
        ('\\v 3 verse three.\n This Is A Section.  \n\\v 4', '\\v 3 verse three.\n\\s This Is A Section.\n\\p\n\\v 4'),
        (' This Fine House\n\\v 4 asdf', '\\s This Fine House\n\\p\n\\v 4 asdf'),
        ('Heading One\n\\v 5 asdf\nHeading Two\nHeading Three', '\\s Heading One\n\\p\n\\v 5 asdf\nHeading Two\nHeading Three'),
        (' This Fine \\ House\n\\v 6 asdf', ''),
        ('\\v 7 asdf\n  Heading At End ', ''),
    ])
def test_mark_heading_lbi_2(section, expected):
    # Tests for heading recognition in a line-by-itself at the end of a chapter
    if not expected:
        expected = section
    result = txt2USFM.mark_section_heading_lbi(section, 'REV 22:8', True)
    assert result == expected
    result = txt2USFM.mark_section_heading_lbi(section, 'REV 22:9', False)
    assert result == expected

@pytest.mark.parametrize('section, newstr',
    [
        ('', ''),
        ('This Fine House', '\\s This Fine House\n\\p\n'),
        ('   Spaces ', '\\s Spaces\n\\p\n'),
        ('\\c 1 \\v 1 verse one.\nThis Is A Section\n\\v 2 second.', '\\c 1 \\v 1 verse one.\n\\s This Is A Section\n\\p\n\\v 2 second.'),
        ('\\v 3 verse three.\n This Is A Section.  \n\\v 4', '\\v 3 verse three.\n\\s This Is A Section.\n\\p\n\\v 4'),
        (' This Fine House\n\\v 4 asdf', '\\s This Fine House\n\\p\n\\v 4 asdf'),
        ('Heading One\n\\v 5 asdf\nHeading Two\nHeading Three', '\\s Heading One\n\\p\n\\v 5 asdf\nHeading Two\nHeading Three'),
        (' This Fine \\ House\n\\v 6 asdf', '\\s This Fine \\ House\n\\p\n\\v 6 asdf'),
        ('\\v 7 asdf\n  Heading At End ', '\\v 7 asdf\n\\s Heading At End\n\\p\n'),
        ('This Fine House', '\\s This Fine House\n\\p\n'),
        ('\\c 1 \\v 1 This is Apostle Paul', ''),
        ('\\c 2 St      \\v 2 asdfasdf', ''),
        ('\\c 3 Common Case One \\v 3', '\\c 3\n\\s Common Case One\n\\p\n\\v 3'),
        ('\\c 3 Lower Case #3 \\v 3', ''),
        ('\\c 4\nCommon Case\n\\v 4', '\\c 4\n\\s Common Case\n\\p\n\\v 4'),
        ('\\c 5\nCommon Case With Space \n\\v 5', '\\c 5\n\\s Common Case With Space\n\\p\n\\v 5'),
        ('Start section Weak possibility \\v 5', ''),
        ('\\c 6 Strong Possibility    ', '\\c 6\n\\s Strong Possibility\n\\p\n'),
        ('\\c 7 Weak possibility', ''),
        ('   \\v 8 No Possibility', ''),
        ('\\c 9\nWord One\nWord Two\n\\v 9 asdf', '\\c 9\n\\s Word One\n\\p\nWord Two\n\\v 9 asdf'),
        ('Before Chapter\n\\c 9 \\v 9 verse. After Verse', 'Before Chapter\n\\c 9 \\v 9 verse.\n\\s After Verse\n\\p\n'),
        ('  Strong Possibility   \\v 9 No Possibility \\c 9', '\\s Strong Possibility\n\\p\n\\v 9 No Possibility \\c 9'),
        ('  Don''t Want This To Be a Heading  \\c 1', ''),
        ('Don''t Want This To Be a Heading  \\c 2 ', ''),
        ('\\c 3 \\s Could Be a Heading\n\\p\n\\v 3 ', ''),
        ('\\c 4 Interference By \\p Heading  \\v 4 ', ''),
        ('Orig Heading\n\\v 5 asdf', '\\s Orig Heading\n\\p\n\\v 5 asdf'),
        ('\\c 33 Before Verse \\v 33 After Verse', '\\c 33\n\\s Before Verse\n\\p\n\\v 33 After Verse'),
        ('\\c 34 Before Verse \\v 34 After Verse. Better Choice', '\\c 34\n\\s Before Verse\n\\p\n\\v 34 After Verse.\n\\s Better Choice\n\\p\n'),
        ('\\v 35 This is A Verse. \\v 35 Another Verse. Better Choice', '\\v 35 This is A Verse. \\v 35 Another Verse.\n\\s Better Choice\n\\p\n'),
        ('\\v 36 Sentence One. Sentence Two. \\v 36 Another Verse. Better Choice', '\\v 36 Sentence One. Sentence Two. \\v 36 Another Verse.\n\\s Better Choice\n\\p\n'),
        ('\\v 37 Sentence One. Sentence Two. \\v 36 Another Verse Bad Choice', ''),
        ('Weak possibility \\v 5', ''),
        ('\\c 6 Sane Possibility', '\\c 6\n\\s Sane Possibility\n\\p\n'),   # only one sentence after last usfm marker
        ('\\c 7 Sane Possibility.', '\\c 7\n\\s Sane Possibility.\n\\p\n'),
        ('\\c 3\n\\s Heading Already Marked\n\\p\n\\v 3 ', ''),
        ('\\v 4 Is a verse. Could Be a \\ Heading', '\\v 4 Is a verse.\n\\s Could Be a \\ Heading\n\\p\n'),
        ('at the end of a verse. Amen.', ''),
        ('\\v 5 Kiru YâkoboEsepo. (Christ).', ''),
        ('\\v 6 Kiru YâkoboEsepo! (Jesus Christ).', ''),
        ('\\v 7 Kiru YâkoboEsepo? (Jesus Christ)', '\\v 7 Kiru YâkoboEsepo?\n\\s Jesus Christ\n\\p\n'),
    ])
# Call mark_section_headings() with the lastchunk parameter False
def test_mark_section_headings_1(section, newstr):
    if not newstr:
        newstr = section
    assert txt2USFM.mark_section_headings(section, 'REV 22:8', False) == newstr

@pytest.mark.parametrize('section, newstr',
    [
        ('', ''),
        ('This Fine House', '\\s This Fine House\n\\p\n'),
        ('   Spaces ', '\\s Spaces\n\\p\n'),
        ('\\v 3 verse three.\n This Is A Section.  \n\\v 4', '\\v 3 verse three.\n\\s This Is A Section.\n\\p\n\\v 4'),
        (' This Fine House\n\\v 4 asdf', '\\s This Fine House\n\\p\n\\v 4 asdf'),
        ('Heading One\n\\v 5 asdf\nHeading Two\nHeading Three', '\\s Heading One\n\\p\n\\v 5 asdf\nHeading Two\nHeading Three'),
        (' This Fine \\ House\n\\v 6 asdf', '\\s This Fine \\ House\n\\p\n\\v 6 asdf'),
        ('\\v 7 asdf\n  Heading At End ', ''),
        ('This Fine House', '\\s This Fine House\n\\p\n'),
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
# Call mark_section_headings() with the lastchunk parameter True,
# in which case, mark_section_headings() doesn't look for section heading at end of section.
def test_mark_section_headings_2(section, newstr):
    if not newstr:
        newstr = section
    result = txt2USFM.mark_section_headings(section, 'REV 22:8', True)
    assert result == newstr
    result = txt2USFM.mark_section_headings(section, 'REV 22:9', False)
    assert result == newstr

@pytest.mark.parametrize('s, expected',
    [
        (None, None),
        ('', ''),
        ('This Fine House', ''),
        ('   Spaces ', ''),
        ('Parens at (end)', ''),
        ('(Total parens)', 'Total parens'),
        ('(Start) with parens', ''),
        ('   \n(StartParens', ''),
        ('   \n(Parens)', 'Parens'),
        ('   ends with Parens)', ''),
        ('(  spaces involved )  ', 'spaces involved'),
    ])
def test_remove_parens(s, expected):
    if not expected:
        expected = s
    assert txt2USFM.remove_parens(s) == expected

@pytest.mark.parametrize('schap, section, ctitle, expected',
    [
        ('1', '', 'Pasal 1', '\n\\cl Pasal 1\n'),
        ('1', 'This Fine House', 'Pasal', '\n\\cl Pasal\nThis Fine House'),
        ('1', '\n\\c 1\n\\s DER ARKEMA SIN\n\\p\n\\v 1 Der nom.\n\\v 2 Taurat\n', 'Pasal 1', '\n\\c 1\n\\cl Pasal 1\n\\s DER ARKEMA SIN\n\\p\n\\v 1 Der nom.\n\\v 2 Taurat\n'),
        ('1', '\\c 1\n\\s DER ARKEMA SIN\n\\p\n\\v 1 Der nom.', 'Pasal 1', '\\c 1\n\\cl Pasal 1\n\\s DER ARKEMA SIN\n\\p\n\\v 1 Der nom.'),
        ('2', '\\c 2\n\\v 1 asdf', 'Pasal 2', '\\c 2\n\\cl Pasal 2\n\\p\n\\v 1 asdf'),
        ('3', '\\c 3\n\\v 1 asdf', '3', '\\c 3\n\\p\n\\v 1 asdf'),
        ('4', '\\c 4\n\\v 1 asdf', 'Pasal', '\\c 4\n\\cl Pasal\n\\p\n\\v 1 asdf'),
        ('5', '\\c 5', 'Pasal 5', '\\c 5\n\\cl Pasal 5\n'),
        ('5', '5', 'Pasal 5', '\n\\cl Pasal 5\n5'),
        ('5', '\\v 1 asdf', '5', '\\p\n\\v 1 asdf'),
        ('6', '\\c 6', '', '\\c 6'),
    ])
def test_augmentChapter(schap, section, ctitle, expected):
    if not expected:
        expected = section
    result = txt2USFM.augmentChapter(schap, section, ctitle)
    assert result == expected

@pytest.mark.parametrize('path, expected',
    [
        (r'C:\DCS\Test\REG\amo_1pe_text_reg\00', []),
        (r'C:\DCS\Test\REG\amo_1pe_text_reg\01', ['01','03','06','08','11','13','15','18','20','22','24']),
    ])
def test_listChunks(path, expected):
    chunks = txt2USFM.listChunks(path)
    assert chunks == expected

@pytest.mark.parametrize('chunkno, chapter, expected',
    [
        (0, 1, ['1','2']),
        (1, 1, ['3','4','5']),
        (10, 1, ['24','25']),
        (11, 1, []),
        (0, 5, ['1','2','3','4']),
        (0, 6, []),
    ])
def test_makeVerseRange(chunkno, chapter, expected):
    path = r'C:\DCS\Test\REG\amo_1pe_text_reg\01'
    if chapter > 1:
        path = r'C:\DCS\Test\REG\amo_1pe_text_reg\05'
    chunks = txt2USFM.listChunks(path)
    verserange = txt2USFM.makeVerseRange(chunks, chunkno, '1PE', chapter)
    assert verserange == expected

@pytest.mark.parametrize('text, expected',
    [
        (r'\v8', ''),
        (r'\V8Afo', ''),
        (r'\v 8Afo eni. \v 9 Newarafi', r'\v 8 Afo eni. \v 9 Newarafi'),
        ('\\v 10\tEna teno. \\v 11\t40 ti deno.', '\\v 10 Ena teno. \\v 11 40 ti deno.'),
        ('\\v 1\tIV) Mana Yomi bami. \\v 2\t2 usukeka', '\\v 1 IV) Mana Yomi bami. \\v 2 2 usukeka'),
    ])
def test_addSpaceAfterVerseNo(text, expected):
    if not expected:
        expected = text
    result = txt2USFM.addSpaceAfterVerseNo(text)
    assert result == expected

@pytest.mark.parametrize('text, expected',
    [
        (r' Yitan\v 8 nin li.  \v9 Yisinan uremere.',  r' Yitan \v 8 nin li.  \v 9 Yisinan uremere.'),
        (r' Yitan \v 8 nin li.  \v9 Yisinan uremere.', r' Yitan \v 8 nin li.  \v 9 Yisinan uremere.'),
        (r' Yitan \V 8 nin li.  \V9 Yisinan uremere.', r' Yitan \v 8 nin li.  \v 9 Yisinan uremere.'),
        (r' Yitan /v 8 nin li.  /V9 Yisinan uremere.', r' Yitan \v 8 nin li.  \v 9 Yisinan uremere.'),
        # (' Yitan /8 nin li.  \\9 Yisinan uremere.', r' Yitan \v 8 nin li.  \v 9 Yisinan uremere.'), # not supported yet
        (r' Yitan /\v 8 nin li.  \\V9 Yisinan uremere.', r' Yitan \v 8 nin li.  \v 9 Yisinan uremere.'),
        (r' Yitan\\v 8 nin li.\\V9 Yisinan uremere.', r' Yitan \v 8 nin li. \v 9 Yisinan uremere.'),
        (r' Yitan \V 8nin li.  \v9Yisinan uremere.\v10',  r' Yitan \v 8 nin li.  \v 9 Yisinan uremere. \v 10'),
        (r'\V10 Kimal akara. /v11 Kiti nani. \v12',  r'\v 10 Kimal akara. \v 11 Kiti nani. \v 12'),
        (r'\v12',  r'\v 12'),
        (r'\V10Kimal akara. /v11Kiti nani. \v12 ',  r'\v 10 Kimal akara. \v 11 Kiti nani. \v 12 '),
        (r'\V10Kimal akara. \v Kiti nani.',  r'\v 10 Kimal akara. \v Kiti nani.'),
        (r'\V10 \v Kimal akara. \v11 Kiti nani.',  r'\v 10 Kimal akara. \v 11 Kiti nani.'),
        (r'\V10 \v Kimal akara. \v \v11 Kiti nani.',  r'\v 10 Kimal akara. \v 11 Kiti nani.'),
        (r'\ V 10 \v Kimal akara. \v \ v11 Kiti nani.',  r'\v 10 Kimal akara. \v 11 Kiti nani.'),
        (r'\ v 10 \v Kimal akara. \ v11 Kiti nani.',  r'\v 10 Kimal akara. \v 11 Kiti nani.'),
        (r'v 12 Meng yning. v 13 Kishono minu.  v 14', r'\v 12 Meng yning. \v 13 Kishono minu. \v 14'),
        (r'Yitan\v 8. nin li.  \v9) Yisinan uremere.',  r'Yitan. \v 8 nin li. \v 9 Yisinan uremere.'),
        (r'\v 8) nin li \v9! Yisinan uremere.',  r'\v 8 nin li! \v 9 Yisinan uremere.'),
        ('\\V10 Kimal akara. \nHeading\n\\v11 Kiti nani.',  '\\v 10 Kimal akara. \nHeading\n\\v 11 Kiti nani.'),
        (r'\v5 Bara nene acine. \v7 Andi aleli ba.', r'\v 5 Bara nene acine. \v 7 Andi aleli ba.'),
        (r'\v 8Afo eni. \v 9 Newarafi', r'\v 8 Afo eni. \v 9 Newarafi'),
        (r'\v 8 \v 10 ۔ادٕہ کران۔_ \v 9 ۔یتھ  ساتؠٕ۔_ ۔بلکہ سجایِن', r'')
    ])
def test_fixVerseMarkers(text, expected):
    if not expected:
        expected = text
    result = txt2USFM.fixVerseMarkers(text)
    assert result == expected

@pytest.mark.parametrize('section, expected',
    [
        (r'\v 1 Ndin ', r'\c 1 \v 1 Ndin '),
        (r'\v 5 asdf asdf', r'\c 1 \v 5 asdf asdf'),    # sic
        (r'\C \v 1 Ndin ', r'\c 1 \v 1 Ndin '),
        (r'\c 1 \v 1 Ndin ', ''),
        (r'\ c11 \v 1 Ndin ', r'\c 11 \v 1 Ndin '),
        (r'\ c 11 \v 1 Ndin ', r'\c 11 \v 1 Ndin '),
        (r'\ C11 \v 1 Ndin ', r'\c 11 \v 1 Ndin '),
        (r'\C11\v 1 Ndin', r'\c 11 \v 1 Ndin'),
        (r'\C12 1 Ndin ', r'\c 12 1 Ndin '),
        (r'\c33', r'\c 33'),
        (' \n \\c11 \\v 1 Ndin ', ' \n \\c 11 \\v 1 Ndin '),
        (' c 4 \\v 1 asdf', r' \c 4 \v 1 asdf'),
    ])
def test_fixChapterMarkers(section, expected):
    if not expected:
        expected = section
    section = txt2USFM.fixChapterMarkers(section, '01')
    assert section == expected

@pytest.mark.parametrize('section, expected',
    [
        ('  ! zxcv  ;  xcvb 2  ) poiu', '! zxcv;  xcvb 2) poiu'),
        ('the end .', 'the end.'),
        ('1 ,000 .000', '1,000.000'),
        ('said ,', 'said,'),
        ('said ,"Now', 'said,"Now'),
        ('said ," Now', 'said," Now'),
        ('asdf ... evev .', 'asdf ... evev.'),
        ('qwer ; evev .[poi ;]', 'qwer; evev. [poi;]'),
        ('2 , 000 . 000', '2, 000. 000'),
        ('!zxcv .xcvb 2)poiu', '! zxcv. xcvb 2) poiu'),
        ('( one )two', '(one) two'),
        ('¡  Spanish !¿ Espanol ?', '¡Spanish! ¿Espanol?'),
        ('(  wert )[! link ](reference )', '(wert) [! link](reference)'),
        ('(kiti asa da kitimine ba.)', ''),
    ])
def test_fixPunctuationSpacing(section, expected):
    if not expected:
        expected = section
    section = txt2USFM.fixPunctuationSpacing(section)
    assert section == expected

@pytest.mark.parametrize('section, expected',
    [
        ('', True),
        ('This Fine House', True),
        ('\n\\c 1\n\\s DER ARKEMA SIN\n\\p\n\\v 1 Der nom.', False),
        ('\\c 1\n\\s DER ARKEMA SIN\n', False),
        ('\\v 1 \\c 2\n\\v 1 asdf', True),
        ('\\v \\c 2\n\\v 1 asdf', False),
        ('\\c 6', False),
        ('\\c \\v 2', True),
   ])
def test_lacksChapter(section, expected):
    lacks = txt2USFM.lacksChapter(section)
    assert lacks == expected

@pytest.mark.parametrize('text, expected',
    [
        (r'\v 1', ['1']),
        (r'\v 1-2', ['1','2']),
        (r'\v 3 Usetano akhambula, "Ingave uveve \v 4', ['3','4']),
    ])
def test_find_vnumbers(text, expected):
    vnumbers_found = txt2USFM.find_vnumbers(text)
    assert vnumbers_found == expected

@pytest.mark.parametrize('text, vstr, expected',
    [
        (r'Nan Kutelle. \v 7 Bara mine.', '5', ''),
        (r'\v Kuwu ati. \v 6 Umong nsono." \v 7 Bara nono', '5', r'\v 5 Kuwu ati. \v 6 Umong nsono." \v 7 Bara nono'),
        (r'\v 5 Kuwu ati. \v Umong nsono." \v Bara nono', '6', r'\v 5 Kuwu ati. \v 6 Umong nsono." \v Bara nono'),
        (r'\v 10 Iwa, kube. \n 11 Bara na ', '11', r'\v 10 Iwa, kube. \n \v 11 Bara na '),
        (r'\v 10 Iwa, kube. \n Bara na ', '11', r'\v 10 Iwa, kube. \n Bara na '),
        (r'1 \v Yesu nlira. \v 2 A aworo \v 3 nan', '1', r'\v 1 Yesu nlira. \v 2 A aworo \v 3 nan'),
        (r'1 \v Yesu nlira. \v 2 A aworo \v 3 nan', '4', r'1 \v 4 Yesu nlira. \v 2 A aworo \v 3 nan'),
        (r'end. 1 \v Yesu nlira. \v 2 A aworo ', '1', r'end. \v 1 Yesu nlira. \v 2 A aworo '),
        (r'\c 1 1 \v Yesu nlira. \v 2 A aworo ', '1', r'\c 1 \v 1 Yesu nlira. \v 2 A aworo '),
        (r'elevator 9 10 escalator', '10', r'elevator 9 \v 10 escalator'),
        (r'3 Usetano akhambula, "Ingave uveve', '3', r'\v 3 Usetano akhambula, "Ingave uveve'),
        (r'4 Usetano akhambula, "Ingave uveve', '4', r'\v 4 Usetano akhambula, "Ingave uveve'),
    ])
def test_fixStrandedTag(text, vstr, expected):
    if not expected:
        expected = text
    result = txt2USFM.fixStrandedTag(text, vstr)
    assert result == expected

range1 = ['1', '2', '3', '4']
range3 = ['3', '4']
range4 = ['4', '5']
range5 = ['5', '6', '7']
range8 = ['8', '9']
range8b = ['8', '9', '10']
range10 = ['10','11']
range16 = ['16','17','18']
range17 = ['17','18','19','20']
range20 = ['20','21','22']
range33 = ['33','34','35']
range38 = ['38','39','40']
range41 = ['41']

@pytest.mark.parametrize('text, verserange, expected',
    [
        (r'random text', range41, r'\v 41 random text'),
        (r'\v 3 Usetano akhambula, "Ingave uveve', range3, r'\v 3 Usetano akhambula, "Ingave uveve \v 4'),
        (r'\v 4 Usetano akhambula, "Ingave uveve', range3, r'\v 3-4 Usetano akhambula, "Ingave uveve'),
        (r'\v Usetano akhambula, "Ingave uveve', range3, r'\v 3-4 Usetano akhambula, "Ingave uveve'),
        (r'Usetano akhambula, "Ingave uveve', range3, r'\v 3-4 Usetano akhambula, "Ingave uveve'),
        (r'Usetano akhambula, \v 5 "Ingave uveve', range3, r'\v 3-4 Usetano akhambula, \v 5 "Ingave uveve'),
        (r'Usetano akhambula, \v 4 "Ingave uveve', range3, r'\v 3 Usetano akhambula, \v 4 "Ingave uveve'),
        (r'5 Usetano akhambula, "Ingave uveve', range3, r'\v 3-4 5 Usetano akhambula, "Ingave uveve'),
        (r'\v 9-10 Bara ba. Bara nani.', range8b, r''),  # leave alone if verse bridge is present
        (r'\c 2 Nan Kutelle. \v 4 Bara mine.', range1, r'\c 2 \v 1-3 Nan Kutelle. \v 4 Bara mine.'),
    ])
def test_insertMissingVerseMarkers(text, verserange, expected):
    if not expected:
        expected = text
    result = txt2USFM.insertMissingVerseMarkers(text, verserange)
    assert result == expected

@pytest.mark.parametrize('text, verserange, expected',
    [
        (r'\v 4 Bara nene acine. \v 5 Andi aleli ba.', range4, ''),
        (r'8 \v 9 Newarafi', range8, ''),
        (r'\v 8   9 Newarafi', range8, r'\v 8-9 Newarafi'),
        (r'\c 1 \v 1 \v 2 Teni Jut weci', range1, r'\c 1 \v 1-2 Teni Jut weci' ),
        (r'\c 1 \v 1 \v 2 Teni \v 3 Jut \v 4 weci', range1, r'\c 1 \v 1-2 Teni \v 3 Jut \v 4 weci' ),
        (r'\v 5 یەشوای \v 6 \v 7 لەسەر زەوی.', range5, r'\v 5 یەشوای \v 6-7 لەسەر زەوی.'),
        (r'\v 18 \v 16 Afo  bacpaci. \v 17 Yeni', range16, r'\v 16 Afo  bacpaci. \v 17 Yeni \v 18'),
        (r'\v 16 Afo  bacpaci. \v 18 \v 17 Yeni', range16, r'\v 16 Afo  bacpaci. \v 17 Yeni \v 18'),
        (r'\v 5 \v 4 Tenti kandauko,', range4, r'\v 4-5 Tenti kandauko,'),
    ])
def test_moveEmpty(text, verserange, expected):
    if not expected:
        expected = text
    result = txt2USFM.moveEmpty(text, verserange)
    assert result == expected

@pytest.mark.parametrize('text, expected',
    [
        (r'\v 5 Ufihelelelage  \v 4 Nuwohakika.  \v 6 Ulyahova.', r'\v 4 Ufihelelelage  \v 5 Nuwohakika.  \v 6 Ulyahova.'),
        (r'\v 17 Pwu ula. \v 16 Akhata. \v 18 Pwu."', r'\v 16 Pwu ula. \v 17 Akhata. \v 18 Pwu."'),
        (r'\v 22 Omunu  \v 20 U Yiisu  \v 21 Pwu fingi.', r'\v 20 Omunu  \v 21 U Yiisu  \v 22 Pwu fingi.'),
        (r'\v 33 \v 35 Udada mwene.   \v 34 Pwu becha', r''),
        (r'\v 38 U Yesu ncheyo?  \v 40 Mlolage  \v 39 Avileamale', r'\v 38 U Yesu ncheyo?  \v 39 Mlolage  \v 40 Avileamale'),
        (r'\v 10 Kimal akara. \v 11 Kiti nani. 12', r''),
        (r'\v 10 Kimal akara. \v 9 Kiti nani. 12', r'\v 9 Kimal akara. \v 10 Kiti nani. 12'),
        (r'\c 2 \v 2 Nan Kutelle. \v 4 Bara mine.', r''),
        (r'\v 10-11 Kimal akara. \v 9 Kiti nani. \v 8 asdf', r'\v 8 Kimal akara. \v 9 Kiti nani. \v 10-11 asdf'),
        (r'\v 10-11 Kimal akara. \v 9 Kiti nani. \v 8 asdf', r'\v 8 Kimal akara. \v 9 Kiti nani. \v 10-11 asdf'),
        (r'\v 28 Iwa e masu . \v 12 Gwana b. \v 13 Anit vat.', r''),
        # (r'\v 6 \v 7 \v 5 Kubi ko na iwa zuro kiti kirum', r'\v 5-7 Kubi ko na iwa zuro kiti kirum'),  # future
        (r'\v 19 \v 18 Aua na.', r''),  # reorder rejects strings with empty verses
    ])
def test_reorderVerseMarkers(text, expected):
    if not expected:
        expected = text
    result = txt2USFM.reorderVerseMarkers(text)
    assert result == expected

@pytest.mark.parametrize('text, verserange, expected',
    [
        (r'\v 3 Usetano akhambula, "Ingave uveve', range3,
         r'\v 3 Usetano akhambula, "Ingave uveve \v 4'),
        (r'\v 6 Ufihelelelage  \v 5 Nuwohakika.  \v 7 Ulyahova.', range5,
         r'\v 5 Ufihelelelage  \v 6 Nuwohakika.  \v 7 Ulyahova.'),
        (r'\v 5 \v 6 Naho Daada.  \v 6 Ululino nalwo. \v 7 Ulu nalwo.', range5,
         r'\v 5-6 Naho Daada.  \v 6 Ululino nalwo. \v 7 Ulu nalwo.'),    # Not ideal, but an improvement
        (r'\v 17 Pwu ula. \v 16 Akhata. \v 18 Pwu."', range16,
         r'\v 16 Pwu ula. \v 17 Akhata. \v 18 Pwu."'),
        (r'\v 22 Omunu  \v 20 U Yiisu  \v 21 Pwu fingi.', range20,
         r'\v 20 Omunu  \v 21 U Yiisu  \v 22 Pwu fingi.'),
        (r'\v 33 \v 35 Udada mwene.   \v 34 Pwu becha', range33, r''),  # Unable to improve
        (r'\v 38 U Yesu ncheyo?    \v 40 Mlolage amavokho  \v 39 Avileamale', range38,
         r'\v 38 U Yesu ncheyo?    \v 39 Mlolage amavokho  \v 40 Avileamale'),
        (r'\v 8 \v 9 nin li. 9  Yisinan uremere.', range8,
         r'\v 8-9 nin li. 9  Yisinan uremere.'),
        (r'\v 10 Kimal akara. \v 11 Kiti nani. 12', range10, r''),
        (r'Nan Kutelle. \v 7 Bara mine.', range5, r'\v 5-6 Nan Kutelle. \v 7 Bara mine.'),
        (r'\v 6 Nan Kutelle. \v 7 Bara mine.', range5, r'\v 5-6 Nan Kutelle. \v 7 Bara mine.'),
        (r'\c 2 Nan Kutelle. \v 4 Bara mine.', range1, r'\c 2 \v 1-3 Nan Kutelle. \v 4 Bara mine.'),
        (r'\v Kuwu ati. \v 6 Umong nsono." \v 7 Bara nono', range5, r'\v 5 Kuwu ati. \v 6 Umong nsono." \v 7 Bara nono'),
        (r'\v 5 Kuwu ati. \v Umong nsono." \v Bara nono', range5, r'\v 5 Kuwu ati. \v 6 Umong nsono." \v 7 Bara nono'),
        (r'\v 10 Iwa, kube. \n 11 Bara na ', range10,
         r'\v 10 Iwa, kube. \n \v 11 Bara na '),
        (r'\v 10 Iwa, kube. \n Bara na ', range10,
         r'\v 10 Iwa, kube. \n Bara na \v 11'),
        (r'1 \v Yesu nlira. \v 2 A aworo \v 3 nan \v 4 asdf', range1, r'\v 1 Yesu nlira. \v 2 A aworo \v 3 nan \v 4 asdf'),
        (r'end. 1 \v Yesu nlira. \v 2 A aworo \v 3 nan \v 4 asdf', range1, r'end. \v 1 Yesu nlira. \v 2 A aworo \v 3 nan \v 4 asdf'),
        (r'\c 1 1 \v Yesu nlira. \v 2 A aworo \v 3 nan \v 4 asdf', range1, r'\c 1 \v 1 Yesu nlira. \v 2 A aworo \v 3 nan \v 4 asdf'),
        (r'Usetano akhambula, "Ingave uveve', range5, r'\v 5-7 Usetano akhambula, "Ingave uveve'),
        (r'Usetano akhambula, "Ingave uveve', range41, r'\v 41 Usetano akhambula, "Ingave uveve'),
        (r'\v 8 Bara ba. \v 9 Bara nani.', range8b,
         r'\v 8 Bara ba. \v 9 Bara nani. \v 10'),
        (r'\v 3 Bara nene acine. \v 5 Andi aleli ba.', range4, r''),
        (r'\v 3 Bara nene acine. \v 5 Andi aleli ba.', range3, r''),
        # (r'\v 6 \v 7 \v 5 Kubi ko na iwa zuro kiti kirum', range5, r'\v 5 Kubi ko na iwa zuro kiti kirum')  # future
    ])
def test_fixVerseOrder(text, verserange, expected):
    if not expected:
        expected = text
    result = txt2USFM.fixVerseOrder(text, '01', verserange)
    assert result == expected

@pytest.mark.parametrize('text, verserange, expected',
    [
        (r'\v3 Bara nene acine. \v5 Andi aleli ba.', range4, r'\v 3 Bara nene acine. \v 5 Andi aleli ba.'),
        (r'8Afo eni. 9 Newarafi', range8, r'\v 8 Afo eni. \v 9 Newarafi'),
        (r'9Afo eni. 8 Newarafi', range8, r'\v 8 Afo eni. \v 9 Newarafi'),
        (r'\c 1 \v 1 \v 2 Teni Jut weci', ['1','2'], r'\c 1 \v 1-2 Teni Jut weci' ),
        (r'\c 1 \v 1 \v 2 Teni \v 3 Jut \v 4 weci', range3, ''),
        (r'\v 1 \v 2 Teni \v 3 Jut \v 4 weci', range1, r'\c 8 \v 1-2 Teni \v 3 Jut \v 4 weci' ),
        (r'\v 5 یەشوای \v 6 \v 7 لەسەر زەوی.', range5, r'\v 5 یەشوای \v 6-7 لەسەر زەوی۔'),
        (r'\v 5 یەشوای \v 7 \v 6 لەسەر زەوی.', range5, r'\v 5 یەشوای \v 6 لەسەر زەوی۔ \v 7'),
        (r'\v 7 \v 5 یەشوای \v 6 لەسەر زەوی۔', range5, r'\v 5 یەشوای \v 6 لەسەر زەوی۔ \v 7'),
        (r'\v 5 \v 4 Tenti kandauko,', range4, r'\v 4-5 Tenti kandauko,'),
        ('\\v 10\tEna teno. \\v 11\t40 ti deno.', range10, '\\v 10 Ena teno. \\v 11 40 ti deno.'),
        ('\\v 1\tIV) Mana Yomi bami. \\v 2\t2 usukeka', ['1','2'], '\\c 8 \\v 1 IV) Mana Yomi bami. \\v 2 2 usukeka'),
        (r'\v 19 \v 17 Na. \v 18 Aua na.\n\19 	Aua o isi? \v 20 .	Aua o', range17, r'\v 19 \v 17 Na. \v 18 Aua na.\n\19 	Aua o isi? \v 20 Aua o'),
        (r'\v 11 \v 10 Aua na.', range10, r'\v 10-11 Aua na.'),
    ])
def test_cleanupText(text, verserange, expected):
    if not expected:
        expected = text
    firstchunk = ("\\v 1 " in text or '\\v 1\t' in text)
    result = txt2USFM.cleanupText(text, '08', verserange, firstchunk)
    assert result == expected
