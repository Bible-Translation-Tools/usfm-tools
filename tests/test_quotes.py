# pytest unit tests for usfm-tools/src/quotes.py functions

import os
import sys

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
import pytest

@pytest.mark.parametrize('str, result',
    [
        ('“phrase partially quoted" ', '“phrase partially quoted” '),
        ('‘phrase partially quoted" ', '‘phrase partially quoted" '),
        ('‘phrase partially quoted\' ', '‘phrase partially quoted’ '),
        ('‘phrase partially quoted\'embedded ', '‘phrase partially quoted\'embedded '),
        ('‘phrase “partially quoted\' ', '‘phrase “partially quoted\' '),
        ('“phrase “partially quoted" ', '“phrase “partially quoted” '),
        ('“phrase "partially quoted" ', '“phrase “partially quoted” '),
        ('“phrase \'partially quoted" ', '“phrase ‘partially quoted" '),

        (' \'word\' ', ' ‘word’ '),    # single word in quotes
        (' "word")',  ' “word”)'),
        ('X"word"', 'X"word"'),
        (' ["word"]', ' [“word”]'),
        ('""word""', '"“word”"'),
        ('\n"start".', '\n“start”.'),
        (' " start " ' , ' " start " '),
        (' "start ' , ' “start '),         # SPACE|PAREN quotes word
        (' "\'Jackson."', ' “‘Jackson.”'),
        (' "Jackson.\'"', ' “Jackson.’”'),
        ('("hello ', '(“hello '),
        (' "Jackson.\'"', ' “Jackson.’”'),
        (': " float', ': “ float'),   # colon SPACE quote
        (':  "  float', ':  “  float'),
        (': ")', ': ")'),
        (': "?', ': "?'),
        (': "(', ': “('),
        (':  "boat', ':  “boat'),
        ('They said:  ‘"boat', 'They said:  ‘“boat'),
        ('They said:  "‘boat', 'They said:  “‘boat'),
        ('thus: "\n', 'thus: “\n'),
        ('thus: " \n', 'thus: “ \n'),
        (';"")', ';””)'),     # comma/semicolon quotes SPACE|PAREN
        ("apple,'\n", "apple,'\n"),
        ("apple,' ", "apple,' "),
        ("apple,']", "apple,’]"),
        ('end of phrase,\'next phrase', 'end of phrase,\'next phrase'),
        ('end of phrase, \'next phrase', 'end of phrase, ‘next phrase'),
        ('end of phrase,\' ', 'end of phrase,\' '),
        ('end of phrase,\')', 'end of phrase,’)'),
        ('Jackson."', 'Jackson.”'),     # period, quotes
        ('" Jackson."', '" Jackson.”'),
        ('!"', '!”'),
        ('questions ?"next', 'questions ?”next'),
        ('end of phrase eol,\'\n', 'end of phrase eol,\'\n'),   # word quote EOL
        ('end of phrase eol, "\n', 'end of phrase eol, "\n'),
        ('end of phrase eol,  "\n', 'end of phrase eol,  "\n'),
        ('end of phrase eol\'\n', 'end of phrase eol’\n'),
        ('end of phrase eol\'  \n', 'end of phrase eol’  \n'),
        ('\n"start of line', '\n“start of line'),   # quotes word at start of line
        ('\n "start of line', '\n “start of line'),
        ('\n" start of line', '\n" start of line'),
        (' \'The Teacher says, "My time is at hand. I will keep the Passover at your house with my disciples."\'"\n',
         ' ‘The Teacher says, “My time is at hand. I will keep the Passover at your house with my disciples.”’”\n'),
        ('''\v 17 Now on the first day of unleavened bread the disciples came to Jesus and said, "Where do you want us to prepare for you to eat the Passover meal?"
\p
\v 18 He said, "Go into the city to a certain man and say to him, 'The Teacher says, "My time is at hand. I will keep the Passover at your house with my disciples."'"
\v 19 The disciples did as Jesus directed them, and they prepared the Passover meal.

\s5
\p
\v 20 When evening came, he sat down to eat with the twelve disciples.
\v 21 As they were eating, he said, "Truly I say to you that one of you will betray me."
\p
\v 22 They were very sorrowful, and each one began to ask him, "Surely not I, Lord?"

\s5
\p
\v 23 He answered, "The one who dips his hand with me in the dish is the one who will betray me.
\v 24 The Son of Man will go, just as it is written about him. But woe to that man by whom the Son of Man is betrayed! It would be better for that man if he had not been born."
\p
\v 25 Judas, who would betray him said, "Is it I, Rabbi?"
\p He said to him, "You have said it yourself."

\s5
\p
\v 26 As they were eating, Jesus took bread, blessed it, and broke it. He gave it to the disciples and said, "Take, eat. This is my body."

\s5
',
''',
'''\v 17 Now on the first day of unleavened bread the disciples came to Jesus and said, “Where do you want us to prepare for you to eat the Passover meal?”
\p
\v 18 He said, “Go into the city to a certain man and say to him, ‘The Teacher says, “My time is at hand. I will keep the Passover at your house with my disciples.”’”
\v 19 The disciples did as Jesus directed them, and they prepared the Passover meal.

\s5
\p
\v 20 When evening came, he sat down to eat with the twelve disciples.
\v 21 As they were eating, he said, “Truly I say to you that one of you will betray me.”
\p
\v 22 They were very sorrowful, and each one began to ask him, “Surely not I, Lord?”

\s5
\p
\v 23 He answered, “The one who dips his hand with me in the dish is the one who will betray me.
\v 24 The Son of Man will go, just as it is written about him. But woe to that man by whom the Son of Man is betrayed! It would be better for that man if he had not been born.”
\p
\v 25 Judas, who would betray him said, “Is it I, Rabbi?”
\p He said to him, “You have said it yourself.”

\s5
\p
\v 26 As they were eating, Jesus took bread, blessed it, and broke it. He gave it to the disciples and said, “Take, eat. This is my body.”

\s5
',
'''),
    ])
def test_promoteQuotes(str, result):
    import quotes
    assert quotes.promoteQuotes(str) == result

@pytest.mark.parametrize('str, expected',
    [
        ('“phrase partially quoted" ', 0),
        ('asdf\'', 4),
        ('qwert"', 5),
        ('\n‘"', 1),
        ('....,;asdf-no quotes!', -1),
        ('', -1),
        ('finally’”', 7),
        ('”’’’’’’', 0),
    ])
def test_quotepos(str, expected):
    import quotes
    assert quotes.quotepos(str) == expected

@pytest.mark.parametrize('str, expected',
    [
        ('“phrase quoted" ', False),
        ('asdf\'', True),
        ('qwert"', True),
        ('\n‘"', False),
        ('....,;asdf-no quotes!', False),
        ('', False),
        ('finally’”', True),
        ('”’’’’’’', False),
        ('  « Begins a quote.', True),
        ('embedded "quote"', False),
        ('"embedded "quote', False),
        ('"Look, "At this."', True),
        ('they said, "At this"', False),
        ('Single quotes\' don\'t count as internal \'quotes', False)
    ])
def test_partialQuote(str, expected):
    import quotes
    assert quotes.partialQuote(str) == expected
