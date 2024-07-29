# pytest unit tests for functions in paratext2usfm.py

import os
import sys

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
import pytest

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
        ('\n\\p text \n\\s1 Heading\n', '\n\\p text \n\\s1 Heading\n'), # \p not standalone
        ('\n\\q\n\\s Heading \n', '\n\\s Heading \n'),
        ('\n\\m \n\\s2 Heading\n', '\n\\s2 Heading\n'),
        ('\n\\p \n\\s Heading\n', '\n\\s Heading\n'),
        ('\n\\pi\n\\s3 Heading\n', '\n\\s3 Heading\n'),
        ('\n\\q2\n\\s Heading\n', '\n\\s Heading\n'),
        ('\n\\q2\n\\s2xyz\n', '\n\\s2xyz\n'),
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

