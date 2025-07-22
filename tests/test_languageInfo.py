# pytest unit tests for functions in LanguageInfo.py

import os
import sys
import pytest

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
from languageinfo import LanguageInfo

dir = r'C:\DCS\Matengo\work'
language_code = 'mgv'
language_name = 'Matengo'

def test_init_newfile():
    # This test function backs up the existing .json file before deleting it.
    path = os.path.join(dir, language_code+'.json')
    bakpath = path + ".bak"
    if os.path.exists(path):
        if not os.path.exists(bakpath):
            os.rename(path, bakpath)
        else:
            os.remove(path)
    li = LanguageInfo(dir, language_code)
    assert li.getLanguageCode() == language_code
    li.save()
    assert li.getLanguageCode() == language_code

def test_init_badid():
    newcode = 'xyz'
    li = LanguageInfo(dir, newcode)
    assert li.getLanguageCode() == newcode

def test_init_noid():
    newcode = ''
    li = LanguageInfo(dir, newcode)
    assert li.getLanguageCode() == newcode
    li.save()
    li = LanguageInfo(dir, newcode)
    assert li.getLanguageCode() == newcode

def test_init_oldfile():
    li = LanguageInfo(dir, language_code)
    assert li.getLanguageCode() == language_code
    li = LanguageInfo(dir, '')
    assert li.getLanguageCode() == ''

def test_language_name():
    li = LanguageInfo(dir, language_code)
    li.setLanguage(language_name, 'rtl')
    li.save()
    assert li.getLanguageName() == language_name

@pytest.mark.parametrize('lang, rsrc, ver',
    [
        ('en', 'ulb', '1'),
        ('en', 'ulb', '1'),
        ('en', 'ulb', '2'),
    ])
def test_addsource(lang, rsrc, ver):
    badrsrc = rsrc + 'X'
    li = LanguageInfo(dir, language_code)
    li.save()
    # sources = li.getSources()
    # assert findSource(sources, lang, badrsrc, ver) == None
    orig_source = li.findSource(lang, rsrc, ver)
    orig_count = orig_source['count'] if orig_source else 0
    li.addSource(lang, rsrc, ver)
    # sources = li.getSources()
    modified_source = li.findSource(lang, rsrc, ver)
    assert modified_source['language_id'] == lang
    assert modified_source['resource_id'] == rsrc
    assert modified_source['version'] == ver
    assert modified_source['count'] == orig_count + 1
    li.save()
    modified_source = li.findSource(lang, rsrc, ver)
    assert modified_source['language_id'] == lang
    assert modified_source['resource_id'] == rsrc
    assert modified_source['version'] == ver
    assert modified_source['count'] == orig_count + 1
    li.addSource(lang, badrsrc, ver)
    # sources = li.getSources()
    modified_source = li.findSource(lang, rsrc, ver)
    assert modified_source != None
    assert modified_source['language_id'] == lang
    assert modified_source['resource_id'] == rsrc
    assert modified_source['version'] == ver
    assert modified_source['count'] == orig_count + 1
    other_source = li.findSource(lang, badrsrc, ver)
    assert other_source['language_id'] == lang
    assert other_source['resource_id'] == badrsrc
    assert other_source['version'] == ver
    assert other_source['count'] == 1

# Before running this test, sort the sources_translations in mgv.json randomly,
# and make version 7.6 the version with the highest count.
def test_getMainSource():
    li = LanguageInfo(dir, language_code)
    source = li.getMainSource()
    assert source['version'] == "7.6"

# Before running this, remove "said_words" from test.json.
# Or, set it to an empty dict -- {}
def test_saidwords():
    global dir
    dir = r'C:\DCS\Test\test_reg'
    global language_code
    language_code = 'test'

    nowords()
    addwords()
    savedwords()
    add_to_savedwords()
    # saidWords()
    # savedSaidWords( )

def nowords():
    li = LanguageInfo(dir, language_code)
    words = li.getWords()
    assert words == []

def addwords():
    li = LanguageInfo(dir, language_code)
    li.addWord('aaa', 2)
    li.addWord('bbb', 3)
    li.addWord('ccc', 1)
    li.addWord('ddd', 0)
    words = li.getWords(mincount=1)
    assert words == ['aaa', 'bbb', 'ccc']
    words = li.getWords(mincount=2)
    assert words == ['aaa', 'bbb']
    li.save()

# Run this test after running test_addwords()
def savedwords():
    li = LanguageInfo(dir, language_code)
    words = li.getWords(mincount=1)
    assert words == ['aaa', 'bbb', 'ccc']
    words = li.getWords(mincount=2)
    assert words == ['aaa', 'bbb']

def add_to_savedwords():
    li = LanguageInfo(dir, language_code)
    li.addWord('bbb', 1)    # no effect
    li.addWord('ccc', 3)
    words = li.getWords(mincount=2)
    assert words == ['aaa', 'bbb', 'ccc']
    li.save()

'''
def saidWords():
    # saidwords = SaidWords(dir, language_code)
    li = LanguageInfo(dir, language_code)
    saidwords.addWord('aaa')
    saidwords.addWord('aaa')
    saidwords.addWord('aaa')
    saidwords.addWord('bbb')
    saidwords.addWord('bbb')
    saidwords.addWord('ccc')
    saidwords.addWord('ccc')
    saidwords.addWord('ddd')
    saidwords.addWord('ddd')
    saidwords.addWord('eee')
    words = saidwords.getWords(mincount=1)
    assert words == ['aaa','bbb','ccc','ddd','eee']
    words = saidwords.getWords(mincount=2)
    assert words == ['aaa','bbb','ccc','ddd']
    words = saidwords.getWords(mincount=3)
    assert words == ['aaa']
    words = saidwords.getWords(mincount=4)
    assert words == []
    saidwords.save(mincount=2)

def savedSaidWords():
    li = LanguageInfo(dir, language_code)
    words = li.getWords(mincount=1)
    assert words == ['aaa', 'bbb', 'ccc', 'ddd']    # notice, 'eee' was not saved
    words = li.getWords(mincount=3)
    assert words == ['aaa', 'bbb', 'ccc']
'''
