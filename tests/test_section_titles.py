# pytest unit tests for usfm-tools/src/sentences.py functions

import os
import sys

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
import pytest

@pytest.mark.parametrize('str, expected',
    [('Sentence 1. Sentence 2.', False),
     ('Numbers 1 2', True),
     ('Sentence Final Punctuation!', True),
     ('Sentence. Medial Punctuation', False),
     ('Only Sentence ABC  ', True),     # > 50% title case
     ('Only Sentence Xyz  ', True),
     ('Two words', False),
     ('(Parenthesized Heading)', True),
     ('(noncap Parenthesized Heading)', False),
     ('.;-%  ', False),
     ('" Sentence With Quotes"  ', False),
     ('A sentence XYZ; a phrase!A sentence-dash?    Another sentence  ', False),
     ('\\v 3 Verse Three.', False),
     ('', False),
     ('This Fine House', True),
     ('noncap Fine House', False),
     ('Newline Wedged\nIn', False),
     ('\nStarts With Newline', True),
     ('Ends With Newline\n', True),
     ('\\c 1 \\v 1 this is a verse', False),
     ('\\c 2 St      \v 2 asdfasdf', False),
     ('\\c 3 String Possibility \\v 3', False), # Headings cannot include usfm markers
     ('Title MiXed lower', False),              # @todo we may honor capitalized, mixed case words later
     ('before a title. Then A Title', False),
     ("How Paul's word", True),
     ("Paul's First Word Possessive", True),
     ('First A Title. Then not a title', False),
     ('This is a Ten Word Candidate with Seven Capitalized Words', True),
     ('This is a Ten Word Candidate with Seven Capitalized Wordsssssss', False),
     ('First and last Words', False),   # I would like for this to be True, but Lamboya's Matthew 1 doesn't.
     ('First and Third words', False),
     ("Tutge Hanuwa Wadeka monno Kama'kna Ammaha", True),
    ])
def test_is_heading(str, expected):
    import section_titles
    assert section_titles.is_heading(str) == expected

@pytest.mark.parametrize('str, expected',
    [(' ( Sentence 1 Sentence 2 )', '( Sentence 1 Sentence 2 )'),
     ('Only Sentence Abc  ', None),
     ('(Two words)', '(Two words)'),
     ('(Two Sentences. Heading)', None),
     ('before parens(Only Sentence Xyz  )after parens  ', '(Only Sentence Xyz  )'),
     ('\nline before\n(Only Sentence Xyz)\vline after\n', '(Only Sentence Xyz)'),
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
        ('\\v 1 verse then (Heading not title)', None),
        ('\\v 1 verse then (heading Not Title)', None),
        ('\\v 1 verse then (Heading Title case) continue verse', '(Heading Title case)'),
        ('(Heading half Title case) then some text', '(Heading half Title case)'),
        ('(notlower Firstword)', None),
        ('some text then (Heading Title Case Minus Close Paren', None),
        ('some text then (First heading) (Second Heading)', '(First heading)'),
        ('some text then (first heading) (Second heading)', '(Second heading)'),
        ('(first heading) (Second heading) (Third Heading)', '(Second heading)'),
        ('\\v 15 Meakore me einya honainyele iteainyembe. (Nim-Kam Mekae Rei maite Yeuboke)', '(Nim-Kam Mekae Rei maite Yeuboke)'),
    ])
def test_find_parenthesized_heading(str, expected):
    import section_titles
    assert section_titles.find_parenthesized_heading(str) == expected
