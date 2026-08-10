# pytest unit tests for usfm-tools/src/sentences.py functions

import os
import sys

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
import pytest
import sentences

@pytest.mark.parametrize('str, startsSentence, expected',
    [('sentence 1. next sentence 2.', True, 'Sentence 1. Next sentence 2.'),
     ('sentence\ncontinuation.', True, 'Sentence\ncontinuation.'),
     ('hyphenated-word', True, 'Hyphenated-word'),
     ('sentence 1. next sentence 2.', False, 'sentence 1. Next sentence 2.'),
     ('sentence\ncontinuation.', False, 'sentence\ncontinuation.'),
     ('hyphenated-word', False, 'hyphenated-word'),
     ('b-', True, 'B-'),
     ('মহিমার মত হব’।” সদাপ্রভু বলেন, এস! এস! ', True, ''),
     ('end. ŋina a kenet na merenyejin ti', False, 'end. Ŋina a kenet na merenyejin ti'),
     ('single', False, 'single'),
     ('single', True, 'Single'),
     ('They said, "go...', True, ''),
     ('They said, "go...', False, ''),
     ('"go," they said.', True, '"Go," they said.'),
     ('"go," they said.', False, '"go," they said.'),
    ])
def test_capitalize(str, startsSentence, expected):
    if not expected:
        expected = str
    cap = sentences.capitalize(str, startsSentence)
    assert cap == expected

@pytest.mark.parametrize('s, expected',
    [('Sentence 1. Next sentence 2.', 'Sentence'),
     ('Sentence\nSecond sentence.', 'Sentence'),
     ('Hyphenated-word', 'Hyphenated-word'),
     ('-Another try', 'Another'),
     ('\n  A- Minus', 'A'),
     ('B-', 'B'),
     ('B-C', 'B-C'),
     ('BB-CC', 'BB-CC'),
     ('D--C', 'D'),
     ('E-F-G', 'E-F'),
     ('F-.G', 'F'),
     ('دەزانن؟»', 'دەزانن'),
    ])
def test_firstword(s, expected):
    firstword = sentences.firstword(s)
    assert firstword == expected

@pytest.mark.parametrize('s, expected',
    [('Sentence 1. Next sentence 2.', '2'),
     ('Sentence\nSecond sentence.', 'sentence'),
     ('Hyphenated-word', 'Hyphenated-word'),
     ('-Another try', 'try'),
     ('\n  A- Minus', 'Minus'),
     ('B-', 'B'),
     ('B-C', 'B-C'),
     ('BB-CC', 'BB-CC'),
     ('D--C', 'C'),
     ('E-F-G', 'G'),
     ('F-.G', 'G'),
     ('دەزانن؟»', 'دەزانن'),
    ])
def test_lastword(s, expected):
    firstword = sentences.lastword(s)
    assert firstword == expected

# Note that nextfirstwords() disregards the first sentence or partial sentence in the string.
@pytest.mark.parametrize('s, expected',
    [('Sentence 1. Next sentence 2.', ['Next']),
     ('Sentence 1\nSame sentence.', []),
     ('Sentence 1\n.Second sentence.', ['Second']),
     ('Only one sentence', []),
     ('Only one sentence!', []),
     ('Sentence 1\n.More sentences! Even more! Yet more.', ['More', 'Even', 'Yet']),
     ('First. More-sentences! Even-more more! -Yet- more.', ['More-sentences', 'Even-more', 'Yet']),
     ('F-.G', ['G']),
     ('F-.G-H', ['G-H']),
     ('ڕابوەستێت؟ ڕابوەستێت؟', ['ڕابوەستێت']),
    ])
def test_nextfirstwords(s, expected):
    firstwordlist = [word for word in sentences.nextfirstwords(s)]
    if type(expected) is list:
        assert firstwordlist == expected
    else:
        assert firstwordlist != expected

@pytest.mark.parametrize('str, result',
    [('Sentence 1. Sentence 2.', [0,12]),
     ('Sentence 1." Sentence 2.', [0,13]),
     ('Sentence 1?" Sentence 2.', [0,13]),
     ('Sentence 1! "Sentence 2.', [0,13]),
     ('Sentence 1?“ Sentence 2', [0]),
     ('Only sentence ABC.  ', [0]),
     ('Only sentence XYZ  ', [0]),
     ('.;-%  ', []),
     ('" Only sentence XYZ  ', [2]),
     ('"A sentence XYZ; a phrase!A sentence-dash?    Another sentence  ', [1,26,46]),
     ('One\n sentence.\nTwo', [0,15]),
     ('\\v 3 Verse three.', 'Undefined'),   # Undefined result because usfm markers are not supported
     ('ለእስራኤል አዘዘው፡፡ለያህዌ ከበግችህ፤ ከፍየሎችህ  ይሁን፡፡', [0,13]),
     ('Quoted sentence!" does ___ make a sentence! Why?', [0,18,44]),
     ('Quoted sentence!‘ does not make a sentence! Why?', [0,44]),
     ('মহিমার মত হব’।” সদাপ্রভু বলেন, এস! এস! ', [0,16,35]),
     ('Hyphenated-words in sentence! Should-work! -Why-?', [0,30,44]),
     ('ڕابوەستێت؟ ڕابوەستێت؟', [0,11]),
    ])
def test_nextstartpos(str, result):
    startposlist = [pos for pos in sentences.nextstartpos(str)]
    if type(result) is list:
        assert startposlist == result
    else:
        assert startposlist != result

@pytest.mark.parametrize('str, expected',
    [('Sentence 1. Sentence 2.', 2),
     ('Sentence 1?" Sentence 2.', 2),
     ('Sentence 1! "Sentence 2.', 2),
     ('Sentence 1.“ Sentence 2.', 2),
     ('Sentence 1?“ Sentence 2.', 1),
     ('  ', 0),
     (' አ ', 1),
     ('Only sentence ABC.  ', 1),
     ('Only sentence XYZ  ', 1),
     ('.;-%  ', 0),
     ('" Only sentence XYZ  ', 1),
     ('"A sentence XYZ; a phrase!A sentence-dash?    Another sentence  ', 3),
     ('One\n sentence.\nTwo', 2),
     ('\\v 3 Verse three.', 1),   # Fortuitous result because usfm markers are not supported
     ('ለእስራኤል አዘዘው፡፡ለያህዌ ከበግችህ፤ ከፍየሎችህ  ይሁን፡፡', 2),
     ('Quoted sentence!" does make a sentence! Why?', 3),
     ('Quoted sentence!‘ does not make a sentence! Why?', 2),
     ('মহিমার মত হব’।” সদাপ্রভু বলেন, এস! এস! ', 3),
     (' ڕابوەستێت؟  ڕابوەستێت؟  ڕابوەستێت', 3),
    ])
def test_sentenceCount(str, expected):
    returned = sentences.sentenceCount(str)
    assert returned == expected

@pytest.mark.parametrize('str, checkquotes, expected',
    [('Sentence 1. Sentence 2.', False, '.'),
     ('Sentence 1. Sentence 2.', True, '.'),
     ('Sentence 1?" ', False, '?'),
     ('Sentence 1?" ', True, '?'),
     ('Sentence.——', False, '.'),
     ('Sentence.——', True, '.'),
     ('Sentence?——', False, '?'),
     ('Sentence?——', True, ''),
     ('Sentence."', False, '.'),
     ('Sentence."', True, '.'),
     ('  ', False, ''),
     ('.', False, '.'),
     ('.', True, '.'),
     ('Only sentence ABC!  ', False, '!'),
     ('Only sentence XYZ  ', False, ''),
     ('.;-%  ', False, '.'),
     ('" Only sentence XYZ "  ', False, ''),
     ('" Only sentence XYZ "  ', True, ''),
     ('"A sentence XYZ;', False, ''),
     ('One\n sentence.»', False, '.'),
     ('One\n sentence.»', True, '.'),
     ('\\v 3 Verse three.', False, '.'),
     ('ለእስራኤል አዘዘው፡፡ለያህዌ ከበግችህ፤ ከፍየሎችህ  ይሁን፡፡', False, '፡'),
     ('ለእስራኤል አዘዘው፡፡ለያህዌ ከበግችህ፤ ከፍየሎችህ  ይሁን፡፡“', True, ''),
     ('Incorrectly quoted sentence!‘', False, '!'),
     ('Incorrectly quoted sentence!‘', True, ''),
     ('মহিমার মত হব’।”', False, '।'),
     ('মহিমার মত হব’।”', True, '।'),
     ('لەبەردەمیدا ڕابوەستێت؟', True, '؟'),
     ('మొదటి ప్రార్థన (మార్కు 14:35. లూకా 22:41;42)', False, ''),
    ])
def test_endsSentence(str, checkquotes, expected):
    returned = sentences.endsSentence(str, checkquotes)
    assert returned == expected

@pytest.mark.parametrize('s, expected',
    [('N’amamera', True),
     ('text', False),
     ('5', False),
     ('', False),
     ('(Parenthesized)', True),
     ('.;-%  ', False),
     ('.;-%Word', False),
     ('"Quotes"', True),
     ("'Quoted", True),
     ("Endquoted'", True),
     (' Spaced', True),
     ("Paul's", True),
     ("E'Besusaida", True),
     ("Syo’mufwire", True),
     ("syo’Mufwire", False),
     ("Syo’Mufwire", True),
     ("Syo’muFwire", False),
     ("Syo’MUFWIRE", False),
     (" E'siwanwa Syo’Mufwire'lower", False),   # isCapitalized(word) does not support phrases
     ("Orang-orang", True),
     ("Orang-Orang", True),
     ("Orang-ORang", False),
     ("orang-Orang", False),
     ('"Hosana!', True),
     ('After-all', True),
     ('Иона', True),
    ])
def test_isCapitalized(s, expected):
    assert sentences.isCapitalized(s) == expected
