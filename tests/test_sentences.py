# pytest unit tests for usfm-tools/src/sentences.py functions

import os
import sys

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
import pytest

@pytest.mark.parametrize('str, expected',
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
     ('F-.G', 'F')
    ])
def test_firstword(str, expected):
    import sentences
    firstword = sentences.firstword(str)
    assert firstword == expected

# Note that nextfirstwords() disregards the first sentence or partial sentence in the string.
@pytest.mark.parametrize('str, expected',
    [('Sentence 1. Next sentence 2.', ['Next']),
     ('Sentence 1\nSame sentence.', []),
     ('Sentence 1\n.Second sentence.', ['Second']),
     ('Only one sentence', []),
     ('Only one sentence!', []),
     ('Sentence 1\n.More sentences! Even more! Yet more.', ['More', 'Even', 'Yet']),
     ('First. More-sentences! Even-more more! -Yet- more.', ['More-sentences', 'Even-more', 'Yet']),
     ('F-.G', ['G']),
     ('F-.G-H', ['G-H']),
    ])
def test_nextfirstwords(str, expected):
    import sentences
    firstwordlist = [word for word in sentences.nextfirstwords(str)]
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
    ])
def test_nextstartpos(str, result):
    import sentences
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
    ])
def test_sentenceCount(str, expected):
    import sentences
    returned = sentences.sentenceCount(str)
    assert returned == expected

@pytest.mark.parametrize('str, checkquotes, expected',
    [('Sentence 1. Sentence 2.', False, True),
     ('Sentence 1. Sentence 2.', True, True),
     ('Sentence 1?" ', False, True),
     ('Sentence 1?" ', True, True),
     ('Sentence.——', False, True),
     ('Sentence.——', True, True),
     ('Sentence?——', False, True),
     ('Sentence?——', True, False),
     ('Sentence."', False, True),
     ('Sentence."', True, True),
     ('  ', False, False),
     ('.', False, True),
     ('.', True, True),
     ('Only sentence ABC!  ', False, True),
     ('Only sentence XYZ  ', False, False),
     ('.;-%  ', False, True),
     ('" Only sentence XYZ "  ', False, False),
     ('" Only sentence XYZ "  ', True, False),
     ('"A sentence XYZ;', False, False),
     ('One\n sentence.»', False, True),
     ('One\n sentence.»', True, True),
     ('\\v 3 Verse three.', False, True),
     ('ለእስራኤል አዘዘው፡፡ለያህዌ ከበግችህ፤ ከፍየሎችህ  ይሁን፡፡', False, True),
     ('ለእስራኤል አዘዘው፡፡ለያህዌ ከበግችህ፤ ከፍየሎችህ  ይሁን፡፡“', True, False),
     ('Incorrectly quoted sentence!‘', False, True),
     ('Incorrectly quoted sentence!‘', True, False),
     ('মহিমার মত হব’।”', False, True),
     ('মহিমার মত হব’।”', True, True),
    ])
def test_endsSentence(str, checkquotes, expected):
    import sentences
    returned = sentences.endsSentence(str, checkquotes)
    assert returned == expected
