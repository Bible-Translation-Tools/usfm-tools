# pytest unit tests for usfm-tools/src/sentences.py functions

import os
import sys

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
import section_titles
import pytest

parens_test_cases = [(' ( Sentence 1 Sentence Two )', '( Sentence 1 Sentence Two )'),
     ('No Parens  ', None),
     ('(Two words)', '(Two words)'),
     ('(Two Sentences. Heading)', None),
     ('before parens(Only Sentence Xyz  )after parens  ', None),
     ('\nline before\n(Only Sentence Xyz)\nLine after\n', '(Only Sentence Xyz)'),
     ('(.;-%)  ', None),
     ('(" Sentence With Quotes)"  ', None),
     ('(  )', None),
     ('(This Fine House\nAbc)', None),
     ('(\nStarts With Newline)', None),
     ('(\\v 1 This Is Interesting)', None),
     ('Parens At End)', None),
     ('(No End Paren', None),
     ('', None),
     ('(not a heading) mid (IS HEADING)', '(IS HEADING)'),
        ('\\v plain verse', None),
        ('', None),
        ('\\v 1 verse then (Heading Title Case)', '(Heading Title Case)'),
        ('\\v 1 verse then (Heading not title)', '(Heading not title)'),
        ('\\v 1 verse then (heading Not Title)', '(heading Not Title)'),
        ('\\v 1 verse then (Heading Title case) continue verse', None),
        ('(Heading half Title case) then some text', None),
        ('(notlower Firstword)', '(notlower Firstword)'),
        ('some text then (Heading Title Case Minus Close Paren', None),
        ('some text then (First heading) (Second Heading)', '(Second Heading)'),
        ('some text then (first heading) (Second heading)', '(Second heading)'),
        ('(first heading) (Second Heading) (Third Heading)', '(Third Heading)'),
        ('\\v 15 Meakore me einya honainyele iteainyembe. (Nim-Kam Mekae Rei maite Yeuboke)', '(Nim-Kam Mekae Rei maite Yeuboke)'),
        ('Do not mark (Parenthesized Words) in the middle of a sentence as a title.', None),
        ('middle of verse (Paul) continue', None),
        ('middle of verse (Peter).', None),
        ('middle of verse (Mary Peter Paul).', None),
        ('(Anything But White Space) after the closing paren disqualifies it', None),
        ('but (White Space Is Okay) \nNext line', '(White Space Is Okay)'),
        ('end of line (Mary Peter Paul)', '(Mary Peter Paul)'),
        ('end of line (One Two Three) with more', None),
        ('(Single).', None),
        ('(Single)', '(Single)'),
        ('\\v 2 some sentence. (Oneword)', '(Oneword)')
    ]

# @pytest.mark.parametrize('line, expected', parens_test_cases)
# def test_find_parenthesized_heading(line, expected):
#     s = section_titles.find_parenthesized_heading(line)
#     assert s == expected

@pytest.mark.parametrize('line, expected', parens_test_cases)
def test_find_parenthesized_heading_new(line, expected):
    if expected is None:
        expected = ""
    s = section_titles.find_parenthesized_heading(line, 0.249)
    assert s == expected

@pytest.mark.parametrize('line, expected',
    [('', ""),
     ('Hukum Taurat wan kitab para nabi. Lalah Baampah Kahidupan', 'Lalah Baampah Kahidupan'),
     ('First Part. Lalah Baampah kahidupan', "Lalah Baampah kahidupan"),
     ('Next Line! Lalah Baampah.', 'Lalah Baampah.'),
     ('Line Four-! Lalah a Baampah.', "Lalah a Baampah."),
     ('Line Four+? Lalah a Baampah', 'Lalah a Baampah'),
     ('Line Five. Lalah a La Baampah.', 'Lalah a La Baampah.'),
     ('Only One Sentence On This Line.', 'Only One Sentence On This Line.'),
     ('Line Six. (Parens Heading)', '(Parens Heading)'),
     ('\\v 7 Line Seven. (Parens Heading).', ''),
     ('  . "', ""),
     ('First A Sentence! Phrase,', ""),
     ('First A Sentence! Phrase:', "Phrase:"),
    ('\\v 17 ਸੋ ਤੱਕ ਚੌਦਾਂ । ਯਿਸੂ ਦਾ ਜਨਮ', 'ਯਿਸੂ ਦਾ ਜਨਮ'),
    ])
def test_find_eol_heading(line, expected):
    assert section_titles.find_eol_heading(line, 0.100) == expected

# Remove this test when the old section_titles is gone.

@pytest.mark.parametrize('s, expected',
    [('Sentence 1. Sentence 2.', 1.0),
     ('numbers 1 2', 0),
     ('Sentence Final Punctuation!', 1),
     ('(Parenthesized Heading)', 1),
     ('(Newline In\nParenthesized Heading)', 1),
     ('.;-%  ', 0),
     ('" Sentence With Quotes"  ', 1.0),
     ('A sentence XYZ; a phrase!A sentence-dash?    Another sentence  ', 3/8),
     ('\\v 3 Verse Three.', 2/4),
     ('', 0),
     ('\\c 2 St      \\v 2 asdfasdf', 1/6),
     ('Title MiXed lower', 1/3),              # @todo we may honor capitalized, mixed case words later
     ("How Paul's word", 2/3),
     ('First A Title. Then not a title', 4/7),
     ('This is a Ten Word Candidate with Seven Capitalized Words', 0.7),
     ("Tutge Hanuwa Wadeka monno Kama'kna Ammaha", 5/6),
     ('Amenee', 1),
    ('“Phrase Quoted" ', 1),
    ("End Quote'", 1.0),
    ('\n‘"', 0),
    ('....,;Asdf-no Quotes!', 0.5),
    ('  « Begins A Quote.', 1.0),
    ('Embedded "Quote"', 1),
    ('"Look, "At This."', 1),
    ('They Said, "At this', 3/4),
    ("Single Quotes' Don't Count as Internal 'Quotes", 6/7)
    ])
def test_percentTitleCase(s, expected):
    assert section_titles.percentTitleOrCaps(s) == expected

# @pytest.mark.parametrize('s, expected',
#     [('మొదటి ప్రార్థన (మార్కు 14:35. లూకా 22:41;42)', 0.555),
# ])
# def test_titlecase_threshold(s, expected):
#     result = section_titles._titlecase_threshold(s)
#     assert result == expected

@pytest.mark.parametrize('preheading, heading, postheading, expected',
    [('N’amamera', 'heading', '\n', 'N’amamera\n\\s heading\n\\p\n'),
     ('', 'heading', '', '\\s heading\n\\p\n'),
     ('Pre  ', '', '', 'Pre'),
     ('', None, '', ''),
     ('Pre    ', 'heading', '', 'Pre\n\\s heading\n\\p\n'),
    ])
def test_insert_heading(preheading, heading, postheading, expected):
    result = section_titles.insert_heading(preheading, heading, postheading)
    assert result == expected

@pytest.mark.parametrize('s, expected',
    [('Sentence 1. Sentence 2.', 4),
     ('numbers 1 2', 3),
     ('Sentence Final Punctuation!', 3),
     ('(Parenthesized Heading)', 2),
     ('(Newline In\nParenthesized Heading)', 4),
     ('.;-%  ', 1),
     ('" Sentence With Quotes"  ', 4),
     ('A sentence XYZ; a phrase!A sentence-dash?    Another sentence  ', 8),
     ('\\v 3 Verse Three.', 4),
     ('', 0),
     (' asdf ', 1),
     ('....,;Asdf-no Quotes!', 2),
     ('  « Begins A Quote.', 4),
    ])
def test_wordcount(s, expected):
    result = section_titles._wordcount(s)
    assert result == expected

@pytest.mark.parametrize('s, expected',
    [('Sentence 1. Sentence 2.', False),
     (' Amen ', True),
     (' sela ', True),
     ('over me. Selah', False),
     ('abide. \\em asdf\\em*', True),
     ('(Looks Good)', False),
     ('(Look)', False),
     ('Look)', False),
     ('', True),
    ])
def test_disqualified(s, expected):
    result = section_titles.disqualified(s)
    assert result == expected
