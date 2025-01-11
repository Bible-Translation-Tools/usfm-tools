# pytest unit tests for usfm-tools/src/sentences.py functions

import os
import sys

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
import pytest

# Note that nextfirstwords() disregards the first sentence or partial sentence in the string.
@pytest.mark.parametrize('str, expected',
    [('Sentence 1. Next sentence 2.', ['Next']),
     ('Sentence 1\nSame sentence.', []),
     ('Sentence 1\n.Second sentence.', ['Second']),
     ('Only one sentence', []),
     ('Only one sentence!', []),
    ])
def test_nextfirstword(str, expected):
    import sentences
    firstwordlist = [word for word in sentences.nextfirstwords(str)]
    if type(expected) is list:
        assert firstwordlist == expected
    else:
        assert firstwordlist != expected

@pytest.mark.parametrize('str, result',
    [('Sentence 1. Sentence 2.', [0,12]),
     ('Sentence 1." Sentence 2.', [0,13]),
     ('Sentence 1?" Sentence 2.', [0]),
     ('Sentence 1! "Sentence 2.', [0,13]),
     ('Sentence 1. Sentence 2', [0,12]),
     ('Only sentence ABC.  ', [0]),
     ('Only sentence XYZ  ', [0]),
     ('.;-%  ', []),
     ('" Only sentence XYZ  ', [2]),
     ('"A sentence XYZ; a phrase!A sentence-dash?    Another sentence  ', [1,26,46]),
     ('One\n sentence.\nTwo', [0,15]),
     ('\\v 3 Verse three.', 'Undefined'),   # Undefined result because usfm markers are not supported
     ('ለእስራኤል አዘዘው፡፡ለያህዌ ከበግችህ፤ ከፍየሎችህ  ይሁን፡፡', [0,13]),
     ('Quoted sentence!" does not make a sentence! Why not?', [0,44]),
     ('মহিমার মত হব’।” সদাপ্রভু বলেন, এস! এস! ', [0,35])
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
     ('Sentence 1?" Sentence 2.', 1),
     ('Sentence 1! "Sentence 2.', 2),
     ('Sentence 1. Sentence 2', 2),
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
     ('Quoted sentence!" does not make a sentence! Why not?', 2),
     ('মহিমার মত হব’।” সদাপ্রভু বলেন, এস! এস! ', 2),
    ])
def test_sentenceCount(str, expected):
    import sentences
    returned = sentences.sentenceCount(str)
    assert returned == expected
