# pytest unit tests for functions in paratext2usfm.py

import os
import sys

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
import pytest
import usfm_cleanup

@pytest.mark.parametrize('s, expected',
    [
        ('.The house.about.', '. The house. about.'),
        ('!The house.about.', '!The house. about.'),
        ('quoted.”The house', 'quoted.”The house'),     # change_quote_medial() handles this
        ('quoted.“The house;', 'quoted.“The house;'),  # change_quote_medial() handles this
        ('quoted:12 disciples,11 men”', 'quoted: 12 disciples, 11 men”'),
        ('sentence.[The house;', 'sentence. [The house;'),
        ('word(?)', 'word (?)'),
        ('?”While,june;kiln^lamb(men)names]oh[,peace“que::road..such.thin:', '?”While, june; kiln^lamb (men) names] oh [, peace“que:: road.. such. thin:'),
        ('eol:\nNew', 'eol:\nNew'),
        ('7:000', '7:000'),
        ('7,000', '7,000'),
        ('eos,s,t', 'eos, s, t'),
    ])
def test_add_spaces(s, expected):
    assert usfm_cleanup.add_spaces(s) == expected

@pytest.mark.parametrize('s, expected',
    [
        ('\\p\n\\s Heading', '\\p\n\\s Heading'),
        ('\\p \\s Heading', '\\p \\s Heading'),
        ('\n\\p\n\\s Heading\n', '\n\\s Heading\n\\p\n'),
        ('\n\\p text \n\\s1 Heading\n', '\n\\p text \n\\s1 Heading\n'), # \p not standalone
        ('\n\\q\n\\s Heading \n', '\n\\s Heading \n\\q\n'),
        ('\n\\m \n\\s2 Heading\n', '\n\\s2 Heading\n\\m \n'),
        ('\\c 5\n\\p \n\\s Heading\n', '\\c 5\n\\s Heading\n\\p \n'),
        ('\\c 6 \n\\pi\n\\s3 Heading\n', '\\c 6 \n\\s3 Heading\n\\pi\n'),
        ('\\v 1 words of a verse.\n\\q2\n\\s Heading\n', '\\v 1 words of a verse.\n\\s Heading\n\\q2\n'),
        ('\n\\q2\n\\s2Heading\n', '\n\\q2\n\\s2Heading\n'),     # not a proper heading
        ('\n\\s Heading\n\\s Heading2', '\n\\s Heading\n\\s Heading2'),
        ('\n\\p\n\\s Heading\n\\s Heading2', '\n\\s Heading\n\\p\n\\s Heading2'),
        ('\n\\p\n\n\\s Heading\n', '\n\\s Heading\n\\p\n'),
        ('\n\\p\n\\s First Heading\n\\v 1 verse\n\\p\n\\s1 Second Heading\n', '\n\\s First Heading\n\\p\n\\v 1 verse\n\\s1 Second Heading\n\\p\n'),
    ])
# usfm_move_pq moves standalone \p \m and \q markers which occur just before an \s# marker
# to the next line after the \s# marker.
def test_usfm_move_pq(s, expected):
    assert usfm_cleanup.usfm_move_pq(s) == expected

@pytest.mark.parametrize('s, expected',
    [
        ('\\p\n\\s Heading', '\\s Heading'),
        ('\\p \\s Heading', '\\s Heading'),     # no line break after \p
        ('\n\\p\n\\s Heading\n', '\n\\s Heading\n'),
        ('asdf \n\\p text \n\\s1 Heading\n', 'asdf \n\\p text \n\\s1 Heading\n'), # \p not standalone
        ('\n\\q\n\\s Heading \n', '\n\\s Heading \n'),
        ('asdf \n\\m \n\\s2 Heading\n', 'asdf \n\\s2 Heading\n'),
        ('\n\\p \n\\s Heading\n', '\n\\s Heading\n'),
        ('\n\\pi\n\\s3 Heading\n', '\n\\s3 Heading\n'),
        ('\n\\q2\n\\s Heading\n', '\n\\s Heading\n'),
        ('asdf.\n\\q1 asdf\n\\q2\n\\s2xyz\n', 'asdf.\n\\q1 asdf\n\\s2xyz\n'),
        ('\n\\s Heading\n\\s Heading2', '\n\\s Heading\n\\s Heading2'),
        ('\n\\p\n\\s Heading\n\\p \n\\s Heading2', '\n\\s Heading\n\\s Heading2'),
        ('\\p\n\\v 1 Verse', ''),
        ('\\p\n\\c 1', '\\c 1'),
        ('\\p\n\\p', '\\p'),
        ('\\p\n\\p words after p', '\\p words after p'),
        ('\\p\n\\p\n', '\\p\n'),
        ('\\p\n\\p words after p\n', '\\p words after p\n'),
        ('\\p words before\n\\s Heading', '\\p words before\n\\s Heading'),
        ('asdf\n\\p\n\\rem asdf', ''),
    ])
# Remove standalone paragraph markers not followed by verse marker or \rem
def test_usfm_remove_pq(s, expected):
    if not expected:
        expected = s
    assert usfm_cleanup.usfm_remove_pq(s) == expected

@pytest.mark.parametrize('s, expected',
    [
        ('\\p\n\\s5 Heading?\n\\s Section heading', '\\p\n\\s5 Heading?\n\\s Section heading'),
        ('\\p asdf\\s5\n', '\\p asdf\\s5\n'),
        ('\n\\s5\n', '\n'),
        ('\n\\s5         \n', '\n'),
        ('\n\\s55\n', '\n\\s55\n'),
        ('\n\\s5 chunk\n', '\n\\s5 chunk\n'),
        ('text before\n\\s5\n\\v 5 text after', 'text before\n\\v 5 text after'),
    ])
# Remove standalone paragraph markers not followed by verse marker.
def test_usfm_remove_s5(s, expected):
    assert usfm_cleanup.usfm_remove_s5(s) == expected

@pytest.mark.parametrize('s, expected',
    [
        ('\\id ROM\n\\toc1 romans\n\\toc2 rOMans\n\\h ROMANS\n\\mt Romans\n',
          '\\id ROM\n\\toc1 Romans\n\\toc2 Romans\n\\h Romans\n\\mt Romans\n'),
        ('\\id ROM\n\\mt1 romans\n\\c 1\n\\p\n\\v 1 asdfasjd fasdf\n\\v 2 asdf\n',
          '\\id ROM\n\\mt1 Romans\n\\c 1\n\\p\n\\v 1 asdfasjd fasdf\n\\v 2 asdf\n'),
        ('\\id ROM\n\\toc3 romans\n\\mt2 romans\n\\h 1 peter\n',
          '\\id ROM\n\\toc3 romans\n\\mt2 romans\n\\h 1 Peter\n'),
        ('\\mt ii peter\n', '\\mt II Peter\n'),
        ('\\mt iiI petro\n', '\\mt III Petro\n'),
    ])
def test_fix_booktitles(s, expected):
    assert usfm_cleanup.fix_booktitles(s) == expected

@pytest.mark.parametrize('s, expected',
    [
        ('first,, second', 'first, second'),
        ('first(second', 'first (second'),
        ('first(second[third', 'first (second [third'),
        ("beats..", "beats."),
        ("beats...", ""),
        ('\\v 13 \' first(second', '\\v 13 \'first (second'),
        ('\\v 13-14 « first(second', '\\v 13-14 «first (second'),
        ('right)paren', 'right) paren'),
        ('one)two}three', 'one) two} three'),
        ('four five]. six', ''),
        ('seven)8', 'seven) 8'),
        ('सुगन्धवाला हवन ठहरे ।', 'सुगन्धवाला हवन ठहरे ।'),   # change space to non-break space \u00A0 == 0xC2 0xA0 (UTF-8)
        ('सुगन्धवाला हवन ठहरे ॥', 'सुगन्धवाला हवन ठहरे ॥'),
        ('\\v 1 " Mulolaghe! Namungavombaghe', '\\v 1 "Mulolaghe! Namungavombaghe')
    ])
# 1. Replaces substrings from substitutions module
# 2. Reduces double periods to single.
# 3. Fixes free floating punctuation after verse marker.
# 4. Adds space before left paren/bracket where needed.
def test_fix_punctuation(s, expected):
    if not expected:
        expected = s
    assert usfm_cleanup.fix_punctuation(s) == expected

@pytest.mark.parametrize('s, all, expected',
    [
        ('first,second', True, 'first,second'),
        ('first,"second', True, 'first,"second'),
        # ('one,"Two," three,"Four"', False, 'one, "Two," three, "Four"'),  # multiple per line not supported yet
        ("o'jole oddo,'Me", True, "o'jole oddo,' Me"),
        ("o'jole oddo,'Me", False, "o'jole oddo,'Me"),
        ("oddo,'Me ri rossosu i'jâkikâle ~bwo, ", True, "oddo, 'Me ri rossosu i'jâkikâle ~bwo, "),
        ("oddo,'Me ri rossosu i'jâkikâle ~bwo, ", False, "oddo,'Me ri rossosu i'jâkikâle ~bwo, "),
        ('fine."Then', False, ''),    # there is no matching quote to aid us
        ('fine."Then"', False, 'fine. "Then"'),
        ('"fine."Then', False, '"fine." Then'),
        ('"fine."Then"', False, '"fine." Then"'),
        ('he said,"Go', False, 'he said, "Go'),    # said word
        ("he said,'Stay", False, ''),
        ("he said,'Pray", True, "he said, 'Pray"),
        ("he said,'Pray", False, ""),
        ("he said,»You may", True, ''),
        ("«he said,»Then", True, "«he said,» Then"),
        ("he said,‘Do not", False, "he said, ‘Do not"),
   ])
def test_change_quote_medial(s, all, expected):
    if not expected:
        expected = s
    usfm_cleanup._setSaidWords(['said', 'asked'])
    newstr = usfm_cleanup.change_quote_medial(s, all)
    assert newstr == expected

floating_test_cases = [
    ('first\'second', ''),
    ('first,"second', ''),
    ('first, " second', ''),
    ('first, " second"', 'first, "second"'),
    ('"first, " second"', ''),
    ('""XX, " ,YY"', '""XX, ",YY"'),
    ('",YY " ZZ YY""', '",YY" ZZ YY""'),
    ('"  A  "', '"A"'),
    ('"A" BB " C"', '"A" BB "C"'),
    ('" C " " D "', '"C" "D"'),
    ('" D " ,EE "F"', '"D" ,EE "F"'),
    ('" G', ''),
    ('" G " H', '"G" H'),
    ('H " I " J', 'H "I" J'),
    ('I “ 1234 ” ', 'I “1234” '),
    ('J ” 1234 “ ', ''),
    ('" K, " L,“ ', '"K," L,“ '),
    (' " L, " ', ' "L," '),
    ('“,YY ” ZZ YY“ ”', '“,YY” ZZ YY“”'),
    ('“,YY " ZZ XX', '“,YY " ZZ XX'),
    ('“,ZZ " XX YY"', '“,ZZ "XX YY"'),
    ('“,AA " XX YY”', ''),
    ('“,AA " XX YY   ”', '“,AA " XX YY”'),
    ('"BB, ” second”"', ''),
    ('"ABC, ” second” " DEF', ''),
    ('"ABC, “ ABC” " DEF', '"ABC, “ABC” " DEF'),
    ('"CC, " second”', '"CC," second”'),
    ('“DD, “   second”', '“DD, “second”'),
    ('"EE, " FF " GG " HH', '"EE," FF "GG" HH'),
    ('"EE,  " FF " GG " HH "', ''),
    ('he said, " Go', 'he said, "Go'),
    ('he asked, ” Why', ''),
    ("They said, ' Okay", "They said, 'Okay"),
]

@pytest.mark.parametrize('s, expected', floating_test_cases)
def test_change_floating_quotes(s, expected):
    if not expected:
        expected = s
    usfm_cleanup._setSaidWords(['said', 'asked'])
    newstr = usfm_cleanup.change_floating_quotes(s, True)
    assert newstr == expected

@pytest.mark.parametrize('s, expected',
    [
        ('blah\\s Heading\n\n\n\\v 1', 'blah\\s Heading\n\\p\n\n\n\\v 1'),
        ('\n\\s Heading\n\\v 15 asdflkjadf', '\n\\s Heading\n\\p\n\\v 15 asdflkjadf'),
        ('\\s Heading\n\\p\n\\v 2 asdf', '\\s Heading\n\\p\n\\v 2 asdf'),
        ('\\s Heading\n\n\\p\n\\v 3 asdf', '\\s Heading\n\n\\p\n\\v 3 asdf'),
        ('\\s Heading\n\\p\n\n\\v 4 asdf', '\\s Heading\n\\p\n\n\\v 4 asdf'),
        ('\\s Heading\n\\p\n\n\\v 5 asdf\n\\s Heading 2\n\\v 6 asdf', '\\s Heading\n\\p\n\n\\v 5 asdf\n\\s Heading 2\n\\p\n\\v 6 asdf'),
    ])
# usfm_add_p add \p between section heading and verse marker, where missing.
def test_usfm_add_p(s, expected):
    assert usfm_cleanup.usfm_add_p(s) == expected

@pytest.mark.parametrize('line, expected',
    [
       # the order of these tests is important because mark_sections() is context sensitive
    ('text at start of line\n', ''),
    ('   Space at Start of Line   \n', '\\s Space at Start of Line\n\\p\n'),
    ('\\c 1 \\v 1 asdf\n', ''),
    ('Text at start of line\n', ''),  # after verse 1, the rules change
    ('\\c 2 unexpected text\n', ''),
    ('Looks Like A Title\n', '\\s Looks Like A Title\n\\p\n'),
    ('\\v 1 Part of a verse\n', ''),
    ('Looks Like A Title\n', ''),
    ('the rest of the verse.\n', ''),
    ('Looks Like A Title\n', '\\s Looks Like A Title\n\\p\n'),
    ('\v 2 Part of a verse\n', ''),
    ('  \n', ''),
    ('Looks Like A Title\n', '\\s Looks Like A Title\n\\p\n'),
    ('', ''),
    ('Amini!\n', ''),
    ('blah\\s Heading\n\n\n\\v 1\n', ''),     # \n should never occur
    ('end of verse. (Probable Heading)\n', 'end of verse.\n\\s Probable Heading\n\\p\n'),
    ('end of verse. (Ends with Period.)\n', 'end of verse.\n\\s Ends with Period\n\\p\n'),  # qualifies by virtue of being the last sentence in the line, not because of parens
    ('check this. (Period Outside Parens).\n', 'check this.\n\\s Period Outside Parens\n\\p\n'),  # qualifies by virtue of being the last sentence in the line, not because of parens
    ('end of verse. (not a heading) \n', ''),
    ('Do not mark (Parenthesized Words) in the middle of a sentence as a title.\n', ''),
    ('middle of verse (Paul) continue\n', ''),
    ('middle of verse (Peter).\n', ''),
    ('middle of verse (Mary Peter Paul).\n', ''),
    ('end of line (Mary Peter Paul)\n', 'end of line\n\\s Mary Peter Paul\n\\p\n'),
    ('end of line (One Two Three) with more\n', ''),
    ('\\s Heading\n\\p\n\\v 2 asdf\n', ''),   # should never occur
    ('(Newline \n Mid Sentence)\n', ''),   # should never occur
    ('some words. Then A Heading\n', 'some words.\n\\s Then A Heading\n\\p\n'),
    # (' Matutra Tutge Puasa (Mat. 9:14-17; Luk. 5:33-39)', '\\s Matutra Tutge Puasa (Mat. 9:14-17; Luk. 5:33-39)\n\\p'),
    ])
def test_mark_sections(line, expected):
    if not expected or expected == line:
        expected = line
        expectchange = False
    else:
        expectchange = True
    (c,s) = usfm_cleanup.mark_sections(line)
    assert s == expected
    assert c == expectchange

@pytest.mark.parametrize('line, expected',
    [
    ('11. \\v 11.', '11. \\v 11'),
    ('alone. alert. 12.   13.,', ''),
    ('\\c 14 \\v 14. asdf\n', '\\c 14 \\v 14 asdf\n'),
    ('\\v  15.asdf ', '\\v  15 asdf '),
    ('\\v  16. asdf \\v 17. qwpoeru', '\\v  16 asdf \\v 17 qwpoeru'),
    ('\\v 17.asdf ', '\\v 17 asdf '),
    ('\\v 18)asdf ', '\\v 18 asdf '),
    ('\\v 19) asdf ', '\\v 19 asdf '),
    ('\\v 20-21)asdf ', '\\v 20-21 asdf '),
    ('\\v 21-22)', '\\v 21-22'),
    ('\\v 22-23. ', '\\v 22-23 '),
    ('\\v 24 24.asdf ', ''),
    ('\\v 25 25)asdf ', ''),
    ('\\v 26 26 asdf ', ''),
    ('\\v 27 27. asdf ', ''),
    ])
def test_remove_periods(line, expected):
    if not expected or expected == line:
        expected = line
        expectchange = False
    else:
        expectchange = True
    (c,s) = usfm_cleanup.remove_periods(line)
    assert s == expected
    assert c == expectchange

@pytest.mark.parametrize('line, pos, exp_matepos',
    [
        ('"Quoted."', 0, 8),
        ('"Quoted."', 1, -1),
        ('x"Quoted."', 1, 9),
        ('x"Quoted."', 9, -1),
        ('x“Curly.”', 1, 8),
        ('x”Curly.“', 1, -1),
        ('x“Curly. “More”', 1, -1),
        ('“1234"6789“1234””789"1234"‘789’’234‘‘789’1234"', 35, -1),
        ('““234"6789“1234””789"1234"‘789’’234‘‘789’1234"”', 0, 46),
        ('“1234"6789“1234””789"1234"‘789’’234‘‘789’1234"', 0, 16),
        ('“1234"6789“1234””789"1234"‘789’’234‘‘789’1234"', 5, -1),
        ('“1234"6789“1234””789"1234"‘789’’234‘‘789’1234"', 7, -1),
        ('“1234"6789“1234””789"1234"‘789’’234‘‘789’1234"', 10, 15),
        ('“1234"6789“1234””789"1234"‘789’’234‘‘789’1234"', 15, -1),
        ('“1234"6789“1234””789"1234"‘789’’234‘‘789’1234"', 20, 25),
        ('“1234"6789“1234””789"1234"‘789’’234‘‘789’1234"', 25, -1),
        ('“1234"6789“1234””789"1234"‘789’’234‘‘789’1234"', 26, 30),
        ('“1234"6789“1234””789"1234"‘789’’234‘‘789’1234"', 31, -1),
        ('“1234"6789“1234””789"1234"‘789’’234‘‘789’1234"', 35, -1),
        ('“1234"6789“1234””789"1234"‘789’’234‘‘789’1234"', 36, 40),
        ('“1234"6789“1234””789"1234"‘789’’234‘‘789’1234"', 40, -1),
        ('“1234"6789“1234””789"1234"‘789’’234‘‘789’1234"', 45, -1),
        ('“1234"6789“1234””789"1234"‘789’’234‘‘789’1234"', -1, -1),
    ])
def test_find_matching_closequote(line, pos, exp_matepos):
    matepos = usfm_cleanup.find_matching_closequote(line, pos, True, True)
    assert matepos == exp_matepos

@pytest.mark.parametrize('line, pos, exp_matepos',
    [
        ('"Quoted."', 0, -1),
        ('"Quoted."', 1, -1),
        ('x"Quoted."', 1, -1),
        ('x"Quoted."', 9, 1),
        ('x“Curly.”', 1, -1),
        ('x”Curly.“', 1, -1),
        ('x“Curly. “More”', 14, 9),
        ('““234"6789“1234””789"1234"‘789’’234‘‘789’1234"”', 47, -1),
        ('““234"6789“1234””789"1234"‘789’’234‘‘789’1234"”', 46, 0),
        ('““234"6789“1234””789"1234"‘789’’234‘‘789’1234"”', 45, -1),
        ('““234"6789“1234””789"1234"‘789’’234‘‘789’1234"”', 42, -1),
        ('““234"6789“1234””789"1234"‘789’’234‘‘789’1234"”', 40, 36),
        ('““234"6789“1234””789"1234"‘789’’234‘‘789’1234"”', 36, -1),
        ('““234"6789“1234””789"1234"‘789’’234‘‘789’1234"”', 31, -1),
        ('““234"6789“1234””789"1234"‘789’’234‘‘789’1234"”', 30, 26),
        ('““234"6789“1234””789"1234"‘789’’234‘‘789’1234"”', 25, 20),
        ('““234"6789“1234””789"1234"‘789’’234‘‘789’1234"”', 20, -1),
        ('““234"6789“1234””789"1234"‘789’’234‘‘789’1234"”', 16, 1),
        ('““234"6789“1234””789"1234"‘789’’234‘‘789’1234"”', 15, 10),
        ('““234"6789“1234””789"1234"‘789’’234‘‘789’1234"”', 10, -1),
        ('““234"6789“1234””789"1234"‘789’’234‘‘789’1234"”', 5, -1),
        ('““234"6789“1234””789"1234"‘789’’234‘‘789’1234"”', 1, -1),
    ])
def test_find_matching_openquote(line, pos, exp_matepos):
    matepos = usfm_cleanup.find_matching_openquote(line, pos, True)
    assert matepos == exp_matepos

@pytest.mark.parametrize('line, all, exp_pairs',
    [
    ('first\'second', True, []),
    ('first, " second"', True, [(7,15)]),
    ('first, " second"', False, [(7,15)]),
    ('"first, " second"', True, []),
    ('""234 " 890"', False, [(6,11), (0,1)]),
    ('"It is written: \'Do not test\'"', True, [(0,29), (16,28)]),
    # ('"Tell him: "I am here.""', True, [(0,23), (11,22)]),  # This case is not supported yet
    ('““234"6789“1\'34””78\'"1234"‘789’’234‘‘789’1234"”\' \' ', True, [(47, 49), (0, 46), (36, 40), (26, 30), (20, 25), (1, 16), (10, 15)]),
    ('““234"6789“1\'34””78\'"1234"‘789’’234‘‘789’1234"”\' \' ', False, [ (0, 46), (36, 40), (26, 30), (20, 25), (1, 16), (10, 15)]),
    ])
def test_pair_up_quotes(line, all, exp_pairs):
    pairs = usfm_cleanup.pair_up_quotes(line, all)
    assert pairs == exp_pairs
    quotes = [p[0] for p in pairs] + [p[1] for p in pairs]
    assert len(set(quotes)) == len(pairs) * 2    # ensures no duplicate indexes

@pytest.mark.parametrize('label, testtitle, schapter, expected',
    [
    ('chapter 1', "بەشی", '1', 'بەشی 1'),
    ('بەشی ٣', "بەشی", '1', 'بەشی ٣'),
    ('بەشی ١٠', "بەشی", '11', 'بەشی ١٠'),
    ('بەشی ١٠', "بەشی", '10', 'بەشی ١٠'),
    ('chap 12', 'chapter', '23', 'chapter 23'),
    ])
def test_fix_chapter_label(label, testtitle, schapter, expected):
    # Set standard_chapter_title in the config file before running this test
    if not expected:
        expected = label
    usfm_cleanup.set_std_title(testtitle)
    result = usfm_cleanup.fix_chapter_label(label, schapter)
    assert result == expected

# The order of these tests is important, because the unit under tests remembers
# whether the previous string ended a sentence.
@pytest.mark.parametrize('text, expected',
    [('Sentence 1. next sentence 2.', 'Sentence 1. Next sentence 2.'),
     ('sentence\ncontinuation.', 'Sentence\ncontinuation.'),
     ('hyphenated-word', 'Hyphenated-word'),
     ('sentence 1. next sentence 2.', 'sentence 1. Next sentence 2.'),
     ('sentence\ncontinuation.', 'Sentence\ncontinuation.'),
     ('hyphenated-word', 'Hyphenated-word'),
     ('b-', 'b-'),
     ('মহিমার মত হব’।” সদাপ্রভু বলেন, এস! এস! ', ''),
     ('end. ŋina a kenet na merenyejin ti', 'End. Ŋina a kenet na merenyejin ti'),
     ('single.', ''),
     ('single', 'Single'),
     ('they said, "go...', ''),
     ('they said, "go...', 'They said, "go...'),
     ('"go," they said.', '"Go," they said.'),
     ('dashing?-', 'Dashing?-'),
     ('quoting. ‘', ''),
     ('closed then open!"“', 'Closed then open!"“'),
     ('starts a new sentence', 'Starts a new sentence'),
    ])
def test_capitalizeAsNeeded(text, expected):
    if not expected:
        expected = text
    result = usfm_cleanup.capitalizeAsNeeded(text)
    assert result == expected
