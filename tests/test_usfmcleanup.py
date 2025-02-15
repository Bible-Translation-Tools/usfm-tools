# pytest unit tests for functions in paratext2usfm.py

import os
import sys

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
import pytest

@pytest.mark.parametrize('str, expected',
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
def test_add_spaces(str, expected):
    import usfm_cleanup
    assert usfm_cleanup.add_spaces(str) == expected

@pytest.mark.parametrize('str, expected',
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
        ('\n\\s Heading\n\s Heading2', '\n\\s Heading\n\s Heading2'),
        ('\n\p\n\\s Heading\n\s Heading2', '\n\\s Heading\n\\p\n\s Heading2'),
        ('\n\\p\n\n\\s Heading\n', '\n\\s Heading\n\\p\n'),
        ('\n\\p\n\\s First Heading\n\\v 1 verse\n\\p\n\\s1 Second Heading\n', '\n\\s First Heading\n\\p\n\\v 1 verse\n\\s1 Second Heading\n\\p\n'),
    ])
# usfm_move_pq moves standalone \p \m and \q markers which occur just before an \s# marker
# to the next line after the \s# marker.
def test_usfm_move_pq(str, expected):
    import usfm_cleanup
    assert usfm_cleanup.usfm_move_pq(str) == expected

@pytest.mark.parametrize('str, expected',
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
        ('\n\\s Heading\n\s Heading2', '\n\\s Heading\n\s Heading2'),
        ('\n\\p\n\\s Heading\n\\p \n\\s Heading2', '\n\\s Heading\n\\s Heading2'),
        ('\\p\n\\v 1 Verse', '\\p\n\\v 1 Verse'),
        ('\\p\n\\c 1', '\\c 1'),
        ('\\p\n\\p', '\\p'),
        ('\\p\n\\p words after p', '\\p words after p'),
        ('\\p\n\\p\n', '\\p\n'),
        ('\\p\n\\p words after p\n', '\\p words after p\n'),
        ('\\p words before\n\\s Heading', '\\p words before\n\\s Heading'),
    ])
# Remove standalone paragraph markers not followed by verse marker.
def test_usfm_remove_pq(str, expected):
    import usfm_cleanup
    assert usfm_cleanup.usfm_remove_pq(str) == expected

@pytest.mark.parametrize('str, expected',
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
def test_usfm_remove_s5(str, expected):
    import usfm_cleanup
    assert usfm_cleanup.usfm_remove_s5(str) == expected

@pytest.mark.parametrize('str, expected',
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
def test_fix_booktitles(str, expected):
    import usfm_cleanup
    assert usfm_cleanup.fix_booktitles(str) == expected

@pytest.mark.parametrize('str, expected',
    [
        ('first,, second', 'first, second'),
        ('first(second', 'first (second'),
        ('first(second[third', 'first (second [third'),
        ("beats..", "beats."),
        ('\\v 13 \' first(second', '\\v 13 \'first (second'),
        ('\\v 13 « first(second', '\\v 13 «first (second'),
        ('first,, second', 'first, second'),
    ])
# 1. Replaces substrings from substitutions module
# 2. Reduces double periods to single.
# 3. Fixes free floating punctuation after verse marker.
# 4. Adds space before left paren/bracket where needed.
def test_fix_punctuation(str, expected):
    import usfm_cleanup
    assert usfm_cleanup.fix_punctuation(str) == expected

@pytest.mark.parametrize('str, all, double, expected',
    [
        ('first,second', True, True, 'first,second'),
        ('first,"second', True, True, 'first,"second'),
        ("o'jole oddo,'Me", True, True, "o'jole oddo,' Me"),
        ("o'jole oddo,'Me", False, True, "o'jole oddo,'Me"),
        ("o'jole oddo,'Me", False, False, "o'jole oddo,'Me"),
        ("oddo,'Me ri rossosu i'jâkikâle ~bwo, ", True, True, "oddo, 'Me ri rossosu i'jâkikâle ~bwo, "),
        ("oddo,'Me ri rossosu i'jâkikâle ~bwo, ", False, True, "oddo,'Me ri rossosu i'jâkikâle ~bwo, "),
        ("oddo,'Me ri rossosu i'jâkikâle ~bwo, ", False, False, "oddo,'Me ri rossosu i'jâkikâle ~bwo, "),
   ])
def test_change_quote_medial(str, all, double, expected):
    import usfm_cleanup
    assert usfm_cleanup.change_quote_medial(str, all, double)[1] == expected

@pytest.mark.parametrize('str, expected',
    [
        ('blah\\s Heading\n\n\n\\v 1', 'blah\\s Heading\n\\p\n\n\n\\v 1'),
        ('\n\\s Heading\n\\v 15 asdflkjadf', '\n\\s Heading\n\\p\n\\v 15 asdflkjadf'),
        ('\\s Heading\n\\p\n\\v 2 asdf', '\\s Heading\n\\p\n\\v 2 asdf'),
        ('\\s Heading\n\n\\p\n\\v 3 asdf', '\\s Heading\n\n\\p\n\\v 3 asdf'),
        ('\\s Heading\n\\p\n\n\\v 4 asdf', '\\s Heading\n\\p\n\n\\v 4 asdf'),
        ('\\s Heading\n\\p\n\n\\v 5 asdf\n\\s Heading 2\n\\v 6 asdf', '\\s Heading\n\\p\n\n\\v 5 asdf\n\\s Heading 2\n\\p\n\\v 6 asdf'),
    ])
# usfm_add_p add \p between section heading and verse marker, where missing.
def test_usfm_add_p(str, expected):
    import usfm_cleanup
    assert usfm_cleanup.usfm_add_p(str) == expected

@pytest.mark.parametrize('line, expected',
    [
       # the order of these tests is important because mark_sections() is context sensitive
    ('text at start of line', ''),
    ('   Space at Start of Line   ', '\\s Space at Start of Line   '),
    ('\\c 1 \\v 1 asdf', ''),
    ('Text at start of line', ''),  # after verse 1, the rules change
    ('\\c 2 unexpected text', ''),
    ('Looks Like A Title', '\\s Looks Like A Title'),
    ('\\v 1 Part of a verse', ''),
    ('Looks Like A Title', ''),
    ('the rest of the verse.', ''),
    ('Looks Like A Title', '\\s Looks Like A Title'),
    ('\v 2 Part of a verse', ''),
    ('  ', '  '),
    ('Looks Like A Title', '\\s Looks Like A Title'),
    ('', ''),
    ('Amini!', ''),
    ('blah\\s Heading\n\n\n\\v 1', ''),     # \n should never occur
    ('end of verse. (Probable Heading)', 'end of verse.\n\\s Probable Heading\n\\p'),
    ('end of verse. (Ends with Period.)', ''),
    ('end of verse. (not a heading) ', ''),
    ('Do not mark (Parenthesized Words) in the middle of a sentence as a title.', ''),
    ('middle of verse (Paul) continue', ''),
    ('middle of verse (Peter).', ''),
    ('middle of verse (Mary Peter Paul).', ''),
    ('end of line (Mary Peter Paul)', 'end of line\n\\s Mary Peter Paul\n\\p'),
    ('end of line (One Two Three) with more', ''),
    ('\\s Heading\n\\p\n\\v 2 asdf', ''),   # should never occur
    ('(Newline \n Mid Sentence)', ''),   # should never occur
    # (' Matutra Tutge Puasa (Mat. 9:14-17; Luk. 5:33-39)', '\\s Matutra Tutge Puasa (Mat. 9:14-17; Luk. 5:33-39)\n\\p'),
    ])
def test_mark_sections(line, expected):
    import usfm_cleanup
    if not expected or expected == line:
        expected = line
        expectchange = False
    else:
        expectchange = True
    (c,s) = usfm_cleanup.mark_sections(line)
    assert s == expected
    assert c == expectchange
