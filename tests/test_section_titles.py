# pytest unit tests for usfm-tools/src/sentences.py functions

import os
import sys

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
import pytest

@pytest.mark.parametrize('str, expected',
    [('Sentence 1. Sentence 2.', False),
     ('Sentence 1 Sentence 2', True),
     ('Only Sentence ABC  ', True),     # > 50% title case
     ('Only Sentence Xyz  ', True),
     ('.;-%  ', False),
     ('" Sentence With Quotes"  ', True),
     ('A sentence XYZ; a phrase!A sentence-dash?    Another sentence  ', False),
     ('\\v 3 Verse Three.', False),
     ('', False),
     ('This Fine House', True),
     ('\\c 1 \\v 1 this is a verse', False),
     ('\\c 2 St      \v 2 asdfasdf', False),
     ('\\c 3 String Possibility \\v 3', False), # Headings cannot include usfm markers
    ])
def test_is_heading(str, expected):
    import section_titles
    assert section_titles.is_heading(str) == expected
