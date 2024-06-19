# pytest unit tests for usfm-tools/src functions
# New and very incomplete as of June 2024.

import os
import sys
tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path, "src"))
sys.path.append(src_path)
import pytest

@pytest.mark.parametrize('str, result',
                             [
                                 ('Jackson."', 'Jackson.”'),
                                 ('" Jackson."', '" Jackson.”'),
                                 (' "\'Jackson."', ' “‘Jackson.”'),
                                 (' "Jackson.\'"', ' “Jackson.’”'),
                             ])
def test_promoteQuotes(str, result):
    import quotes
    assert quotes.promoteQuotes(str) == result
