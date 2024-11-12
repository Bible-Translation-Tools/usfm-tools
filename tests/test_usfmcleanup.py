# pytest unit tests for functions in paratext2usfm.py

import os
import sys

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
import pytest

@pytest.mark.parametrize('str, newstr',
    [
        ('.The house.about.', '. The house. about.'),
        ('!The house.about.', '!The house. about.'),
        ('quoted.”The house', 'quoted.” The house'),
        ('quoted.“The house;', 'quoted. “The house;'),
        ('quoted:12 disciples,11 men”', 'quoted: 12 disciples, 11 men”'),
        ('sentence.[The house;', 'sentence. [The house;'),
        ('word(?)', 'word (?)'),
        ('?”While,june;kiln^lamb(men)names]oh[,peace“que::road..such.thin:', '?” While, june; kiln^lamb (men) names] oh [, peace “que:: road.. such. thin:'),
        ('eol:\nNew', 'eol:\nNew'),
    ])
def test_add_spaces(str, newstr):
    import usfm_cleanup
    assert usfm_cleanup.add_spaces(str) == newstr

@pytest.mark.parametrize('str, newstr',
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
def test_usfm_move_pq(str, newstr):
    import usfm_cleanup
    assert usfm_cleanup.usfm_move_pq(str) == newstr

@pytest.mark.parametrize('str, newstr',
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
def test_usfm_remove_pq(str, newstr):
    import usfm_cleanup
    assert usfm_cleanup.usfm_remove_pq(str) == newstr

@pytest.mark.parametrize('str, newstr',
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
def test_usfm_remove_s5(str, newstr):
    import usfm_cleanup
    assert usfm_cleanup.usfm_remove_s5(str) == newstr

@pytest.mark.parametrize('str, newstr',
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
def test_fix_booktitles(str, newstr):
    import usfm_cleanup
    assert usfm_cleanup.fix_booktitles(str) == newstr

@pytest.mark.parametrize('str, newstr',
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
def test_fix_punctuation(str, newstr):
    import usfm_cleanup
    assert usfm_cleanup.fix_punctuation(str) == newstr

@pytest.mark.parametrize('str, posn',
    [
        ('\\v plain verse', 0),
        ('', 0),
        ('\\v 1 verse then (Heading Title Case)', 1),
        ('\\v 1 verse then (Heading not title)', 0),
        ('\\v 1 verse then (heading Not Title)', 0),
        ('\\v 1 verse then (Heading Title Case) continue verse', 1),
        ('(Heading half Title case) then some text', 1),
        ('some text then (Heading Title Case Minus Close Paren', 0),
        ('some text then (First heading) (Second Heading)', 1),
        ('some text then (first heading) (Second heading)', 2),
        ('(first heading) (Second heading) (Third Heading)', 2),
        ('\\v 15 Meakore me einya honainyele iteainyembe. (Nim-Kam Mekae Rei maite Yeuboke)', 1),
    ])
def test_has_parenthesized_heading(str, posn):
    import usfm_cleanup
    assert usfm_cleanup.has_parenthesized_heading(str) == posn