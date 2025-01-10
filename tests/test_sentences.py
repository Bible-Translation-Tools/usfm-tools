# pytest unit tests for usfm-tools/src/sentences.py functions

import os
import sys

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
import pytest

@pytest.mark.parametrize('str, result',
    [('Sentence 1. Sentence 2.', [0,12]),
     ('Sentence 1." Sentence 2.', [0,13]),
     ('Sentence 1. "Sentence 2.', [0,13]),
     ('Sentence 1. Sentence 2', [0,12]),
     ('Only sentence ABC.  ', [0]),
     ('Only sentence XYZ  ', [0]),
     ('.;-%  ', []),
     ('" Only sentence XYZ  ', [2]),
     ('"A sentence XYZ; a phrase!A sentence-dash?    Another sentence  ', [1,26,46]),
     ('\\v 3 Verse three.', 'Undefined'),   # Undefined result because usfm markers are not supported
     ('ለእስራኤል አዘዘው፡፡ለያህዌ ከበግችህ፤ ከፍየሎችህ  ይሁን፡፡', [0,13]),
     ('মহিমার মত হব’।” সদাপ্রভু বলেন, এস! এস! ', [0,16,35])
    ])
def test_nextstartpos(str, result):
    import sentences
    startposlist = [pos for pos in sentences.nextstartpos(str)]
    if type(result) is list:
        assert startposlist == result
    else:
        assert startposlist != result
