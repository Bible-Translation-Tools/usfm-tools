# pytest unit tests for usfm-tools/src/sentences.py functions

import os
import sys

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
import pytest

@pytest.mark.parametrize('str, expected',
    [('Sentence 1. Sentence 2.', False),
     ('( Sentence 1 Sentence Two )', True),
     ('Numbers 1 2', False),
     ('Has A Final Period.', True),
     ('Sentence Final Punctuation!', True),
     ('Sentence. Medial Punctuation', False),
     ('Only Sentence ABC  ', True),
     ('Only Sentence Xyz  ', True),
     ('Two words', False),
     ('(Parenthesized Heading)', True),
     ('(noncap Parenthesized Heading)', False),
     ('(\nNewline Starts Parenthesized Heading)', False),
     ('(Newline In\nParenthesized Heading)', False),
     ('(Newline Ends Parenthesized Heading\n)', False),
     ('.;-%  ', False),
     ('" Quoted Sentence"  ', False),
     ('A sentence XYZ; a phrase!A sentence-dash?    Another sentence  ', False),
     ('\\v 3 Verse Three.', False),
     ('', False),
     ('This Fine House', True),
     ('noncap Fine House', False),
     ('Three Words noncap', False),
     ('Four Words But noncap', True),
     ('Newline Wedged\nIn', False),
     ('\nStarts With Newline', True),
     ('Ends With Newline\n', True),
     ('\\c 1 \\v 1 this is a verse', False),
     ('\\c 2 St      \\v 2 asdfasdf', False),
     ('\\c 3 String Possibility \\v 3', False), # Headings cannot include usfm markers
     ('Title MiXed lower', False),              # @todo we may honor capitalized, mixed case words later
     ('before a title. Then A Title', False),
     ("How Paul's word", False),    # last word is not title case
     ("Paul's First Word Possessive", True),
     ('First A Title. Then not a title', False),
     ('This is a Ten Word Candidate with Seven Capitalized Words', True),
     ('This is a Ten Word Candidate with Seven Capitalized Wordsssssss', False),
     ('First and last Words', False),   # I would like for this to be True, but Lamboya's Matthew 1 doesn't. Err on the side of not marking sections.
     ('First and Third words', False),
     ("Tutge Hanuwa Wadeka monno Kama'kna Ammaha", True),
     ('Amenee', False),
     ('Amiina', False),
     ('Selah', False),
        ('“Phrase Quoted" ', False),
        ('End Quote\'', False),
        ('\n‘"', False),
        ('....,;Asdf-no Quotes!', False),
        ('”’’’’’’', False),
        ('  « Begins A Quote.', False),
        ('Embedded "Quote"', False),
        ('"Embedded "Quote', False),
        ('"Look, "At This."', False),
        ('They Said, "At this', False),
        ("Single Quotes Don't Count'as Internal Quotes", True),
        ('Parens At (End)', True),
        ('Olukaado Lw’omuyofu N’amamera', True),
        ("Okhuwoniya Khwomusaacha Muwofwu E'Besusaida", True),
        ('(Single).', False),
        ('(Single)', False),
        ('"Hosana!', False),
        ('Punctuatedword.', False),
        ('Wordone Wordtwo.', True),
    ])
def test_is_heading(str, expected):
    import section_titles
    assert section_titles.is_heading(str) == expected

@pytest.mark.parametrize('str, expected',
    [('Sentence 1. Sentence 2.', False),
     ('Numbers 1 2', False),
     ('Has A Final Period.', True),
     ('Sentence Final Punctuation!', True),
     ('Sentence. Medial Punctuation', False),
     ('Only Sentence ABC  ', True),
     ('Only Sentence Xyz  ', True),
     ('Two words', False),
     ('(Parenthesized Heading)', True),
     ('(noncap Parenthesized Heading)', False),
     ('(\nNewline Starts Parenthesized Heading)', False),
     ('(Newline In\nParenthesized Heading)', False),
     ('(Newline Ends Parenthesized Heading\n)', False),
     ('.;-%  ', False),
     ('" Quoted Sentence"  ', False),
     ('A sentence XYZ; a phrase!A sentence-dash?    Another sentence  ', False),
     ('\\v 3 Verse Three.', False),
     ('', False),
     ('This Fine House', True),
     ('noncap Fine House', False),
     ('Three Words noncap', True),
     ('Four Words But noncap', True),
     ('Newline Wedged\nIn', False),
     ('\nStarts With Newline', True),
     ('Ends With Newline\n', True),
     ('\\c 1 \\v 1 this is a verse', False),
     ('\\c 2 St      \\v 2 asdfasdf', False),
     ('\\c 3 String Possibility \\v 3', False), # Headings cannot include usfm markers
     ('Title MiXed lower', False),              # @todo we may honor capitalized, mixed case words later
     ('before a title. Then A Title', False),
     ("How Paul's word", True),
     ("Paul's First Word Possessive", True),
     ('First A Title. Then not a title', False),
     ('This is a Ten Word Candidate with Seven Capitalized Words', True),
     ('This is a Longer Ten Word Candidate with Seven Capitalizedwordsssssss', True),
     ('First and last Words', True),   # I would like for this to be True, but Lamboya's Matthew 1 doesn't. Err on the side of not marking sections.
     ('First and Third words', False),
     ("Tutge Hanuwa Wadeka monno Kama'kna Ammaha", True),
     ('Amenee', False),
        ('“Phrase Quoted" ', False),
        ('End Quote\'', False),
        ('\n‘"', False),
        ('....,;Asdf-no Quotes!', False),
        ('”’’’’’’', False),
        ('  « Begins A Quote.', False),
        ('Embedded "Quote"', False),
        ('"Embedded "Quote', False),
        ('"Look, "At This."', False),
        ('They Said, "At this', False),
        ("Single Quotes Don't Count'as Internal Quotes", True),
        ('Parens At (End)', True),
        ('Olukaado Lw’omuyofu N’amamera', True),
        ("Okhuwoniya Khwomusaacha Muwofwu E'Besusaida", True),
        ('(Single).', False),
        ('(Single)', False),
        ('"Hosana!', False),
    ])
def test_is_possibleheading(str, expected):
    import section_titles
    assert section_titles.is_possible_heading(str) == expected

@pytest.mark.parametrize('str, expected',
    [(' ( Sentence 1 Sentence Two )', '( Sentence 1 Sentence Two )'),
     ('No Parens  ', None),
     ('(Two words)', None),
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
        ('\\v 1 verse then (Heading not title)', None),
        ('\\v 1 verse then (heading Not Title)', None),
        ('\\v 1 verse then (Heading Title case) continue verse', None),
        ('(Heading half Title case) then some text', None),
        ('(notlower Firstword)', None),
        ('some text then (Heading Title Case Minus Close Paren', None),
        ('some text then (First heading) (Second Heading)', '(Second Heading)'),
        ('some text then (first heading) (Second heading)', None),
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
        ('(Single)', None),
        ('\\v 2 some sentence. (Oneword)', None)
    ])
def test_find_parenthesized_heading(str, expected):
    import section_titles
    assert section_titles.find_parenthesized_heading(str) == expected

@pytest.mark.parametrize('line, expected',
    [('', None),
     ('Hukum Taurat wan kitab para nabi. Lalah Baampah Kahidupan', 'Lalah Baampah Kahidupan'),
     ('First Part. Lalah Baampah kahidupan', None),
     ('Next Line! Lalah Baampah.', 'Lalah Baampah.'),
     ('Line Four-! Lalah a Baampah.', None),
     ('Line Four+? Lalah a Baampah', 'Lalah a Baampah'),
     ('Line Five. Lalah a La Baampah.', 'Lalah a La Baampah.'),
     ('Only One Sentence On This Line.', 'Only One Sentence On This Line.'),
     ('Line Six. (Parens Heading)', '(Parens Heading)'),
     ('Line Seven. (Parens Heading).', '(Parens Heading).'),
     ('  . "', None),
    ])
def test_find_eol_heading(line, expected):
    import section_titles
    assert section_titles.find_eol_heading(line) == expected

@pytest.mark.parametrize('str, expected',
    [('Sentence 1. Sentence 2.', 0.5),
     ('numbers 1 2', 0),
     ('Sentence Final Punctuation!', 1),
     ('(Parenthesized Heading)', 1),
     ('(Newline In\nParenthesized Heading)', 1),
     ('.;-%  ', 0),
     ('" Sentence With Quotes"  ', 0.75),
     ('A sentence XYZ; a phrase!A sentence-dash?    Another sentence  ', 0.25),
     ('\\v 3 Verse Three.', 0.5),
     ('', 0),
     ('\\c 2 St      \\v 2 asdfasdf', 1/6),
     ('Title MiXed lower', 1/3),              # @todo we may honor capitalized, mixed case words later
     ("How Paul's word", 2/3),
     ('First A Title. Then not a title', 4/7),
     ('This is a Ten Word Candidate with Seven Capitalized Words', 0.7),
     ("Tutge Hanuwa Wadeka monno Kama'kna Ammaha", 5/6),
     ('Amenee', 1),
        ('“Phrase Quoted" ', 1),
        ("End Quote'", 0.5),
        ('\n‘"', 0),
        ('....,;Asdf-no Quotes!', 0.5),
        ('  « Begins A Quote.', 3/4),
        ('Embedded "Quote"', 1),
        ('"Look, "At This."', 1),
        ('They Said, "At this', 3/4),
        ('Single Quotes\' Don\'t Count as Internal \'Quotes', 4/7)
    ])
def test_percentTitleCase(str, expected):
    import section_titles
    assert section_titles.percentTitlecase(str) == expected

@pytest.mark.parametrize('str, expected',
    [('N’amamera', True),
     ('text', False),
     ('5', False),
     (None, False),
     ('(Parenthesized)', True),
     ('', False),
     ('.;-%  ', False),
     ('.;-%Word', False),
     ('"Quotes"', True),
     ("Paul's", True),
     ("E'Besusaida", True),
     ("Syo’mufwire", True),
     ("syo’Mufwire", False),
     ("Syo’Mufwire", True),
     ("Syo’muFwire", False),
     ("Syo’MUFWIRE", False),
     (" E'siwanwa Syo’Mufwire'lower", False),   # isCapitalized does not support phrases
     ("'Quoted", False),
     ("Endquoted'", False),
     ("Orang-orang", True),
     ("Orang-Orang", True),
     ("Orang-ORang", False),
     ("orang-Orang", False),
     ('"Hosana!', True),
    ])
def test_isCapitalized(str, expected):
    import section_titles
    assert section_titles.isCapitalized(str) == expected

@pytest.mark.parametrize('preheading, heading, postheading, expected',
    [('N’amamera', 'heading', '\n', 'N’amamera\n\\s heading\n\\p\n'),
     ('', 'heading', '', '\\s heading\n\\p\n'),
     ('Pre  ', '', '', 'Pre'),
     ('', None, '', ''),
     ('Pre    ', 'heading', '', 'Pre\n\\s heading\n\\p\n'),
    ])
def test_insert_heading(preheading, heading, postheading, expected):
    import section_titles
    result = section_titles.insert_heading(preheading, heading, postheading)
    assert result == expected
