# pytest unit tests for usfm-tools/src functions
# New and very incomplete as of June 2024.

import os
import sys

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
import pytest

@pytest.mark.parametrize('str, result',
    [
        (' \'word\' ', ' ‘word’ '),    # single word in quotes
        (' "word")',  ' “word”)'),
        ('X"word"', 'X"word"'),
        (' ["word"]', ' [“word”]'),
        ('\n"start".', '\n“start”.'),
        (' " start " ' , ' " start " '),
        (' "start ' , ' “start '),         # SPACE|PAREN quotes word
        (' "\'Jackson."', ' “‘Jackson.”'),
        (' "Jackson.\'"', ' “Jackson.’”'),
        ('("hello ', '(“hello '),
        (' "Jackson.\'"', ' “Jackson.’”'),
        (': " float', ': “ float'),   # colon space quote
        (':  "  float', ': “  float'),
        (': ")', ': ")'),
        (': "?', ': "?'),
        (': "(', ': “('),
        (';"")', ';””)'),     # comma/semicolon quotes SPACE|PAREN
        ("apple,'\n", "apple,'\n"),
        ("apple,' ", "apple,’ "),
        (':  "boat', ':  “boat'),
        ('Jackson."', 'Jackson.”'),     # period, quotes
        ('" Jackson."', '" Jackson.”'),
        ('!"', '!”'),
        ('questions ?"next', 'questions ?”next'),
        ('end of phrase,\'next phrase', 'end of phrase,\'next phrase'),
        ('end of phrase, \'next phrase', 'end of phrase, ‘next phrase'),
        ('end of phrase eol,\'\n', 'end of phrase eol,\'\n'),
        ('end of phrase,\' ', 'end of phrase,’ '),
        ('\n"start of line', '\n"start of line'),
    ])
def test_promoteQuotes(str, result):
    import quotes
    assert quotes.promoteQuotes(str) == result
