# pytest unit tests for functions in projectinfo.py

import os
import sys
import pytest

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
from projectinfo import ProjectInfo, SaidWords

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
    projectInfo = ProjectInfo(dir, language_code)
    projectInfo.useManifest()
    assert projectInfo.getLanguageCode() == language_code
    projectInfo.save()
    assert projectInfo.getLanguageCode() == language_code

def test_init_badid():
    newcode = 'xyz'
    projectInfo = ProjectInfo(dir, newcode)
    assert projectInfo.getLanguageCode() == newcode

def test_init_noid():
    newcode = ''
    projectInfo = ProjectInfo(dir, newcode)
    assert projectInfo.getLanguageCode() == newcode
    projectInfo.save()
    projectInfo = ProjectInfo(dir, newcode)
    assert projectInfo.getLanguageCode() == newcode

def test_init_oldfile():
    projectInfo = ProjectInfo(dir, language_code)
    assert projectInfo.getLanguageCode() == language_code
    projectInfo = ProjectInfo(dir, '')
    assert projectInfo.getLanguageCode() == ''

def test_language_name():
    projectInfo = ProjectInfo(dir, language_code)
    projectInfo.setLanguage(language_name, 'rtl')
    projectInfo.save()
    assert projectInfo.getLanguageName() == language_name

@pytest.mark.parametrize('lang, rsrc, ver',
    [
        ('en', 'ulb', '1'),
        ('en', 'ulb', '1'),
        ('en', 'ulb', '2'),
    ])
def test_addsource(lang, rsrc, ver):
    badrsrc = rsrc + 'X'
    projectInfo = ProjectInfo(dir, language_code)
    projectInfo.save()
    # sources = projectInfo.getSources()
    # assert findSource(sources, lang, badrsrc, ver) == None
    orig_source = projectInfo.findSource(lang, rsrc, ver)
    orig_count = orig_source['count'] if orig_source else 0
    projectInfo.addSource(lang, rsrc, ver)
    # sources = projectInfo.getSources()
    modified_source = projectInfo.findSource(lang, rsrc, ver)
    assert modified_source['language_id'] == lang
    assert modified_source['resource_id'] == rsrc
    assert modified_source['version'] == ver
    assert modified_source['count'] == orig_count + 1
    projectInfo.save()
    modified_source = projectInfo.findSource(lang, rsrc, ver)
    assert modified_source['language_id'] == lang
    assert modified_source['resource_id'] == rsrc
    assert modified_source['version'] == ver
    assert modified_source['count'] == orig_count + 1
    projectInfo.addSource(lang, badrsrc, ver)
    # sources = projectInfo.getSources()
    modified_source = projectInfo.findSource(lang, rsrc, ver)
    assert modified_source != None
    assert modified_source['language_id'] == lang
    assert modified_source['resource_id'] == rsrc
    assert modified_source['version'] == ver
    assert modified_source['count'] == orig_count + 1
    other_source = projectInfo.findSource(lang, badrsrc, ver)
    assert other_source['language_id'] == lang
    assert other_source['resource_id'] == badrsrc
    assert other_source['version'] == ver
    assert other_source['count'] == 1

# Before running this test, sort the sources_translations in mgv.json randomly,
# and make version 7.6 the version with the highest count.
def test_getMainSource():
    projectInfo = ProjectInfo(dir, language_code)
    source = projectInfo.getMainSource()
    assert source['version'] == "7.6"

def test_sync():
    dir = r'C:\DCS\Test\test_reg'
    language_code = 'test'
    pi = ProjectInfo(dir, language_code)
    pi.resetSources()
    pi.setLanguage("")
    n = len(pi.getSources())
    assert n == 0
    assert pi.getLanguageName() == ""

    pi.useManifest()        # sync happens here
    newlen = len(pi.getSources())
    assert newlen > n
    newname = pi.getLanguageName()
    assert newname != ""
    pi.setLanguage("Mangled name", "mangled direction")
    assert pi.getLanguageName() == "Mangled name"
    pi.addSource('bogus', 'ulllll', '99')
    pi.save(savePI=True, saveM=False)

    from manifestyaml import ManifestYaml
    my = ManifestYaml()
    my.load(dir)
    assert my.getLanguageName() != "Mangled name"   # bad value wasn't saved
    assert my.getLanguageDirection() in {'rtl','ltr'}   # bad value wasn't saved

    pi.useManifest()        # sync happens again
    assert pi.getLanguageName() == "Mangled name"   # existing name wasn't overwritten
    assert len(pi.getSources()) == newlen + 1   # no sources were added or removed

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
    saidWords()
    savedSaidWords( )

def nowords():
    pi = ProjectInfo(dir, language_code)
    words = pi.getWords()
    assert words == []

def addwords():
    pi = ProjectInfo(dir, language_code)
    pi.addWord('aaa', 2)
    pi.addWord('bbb', 3)
    pi.addWord('ccc', 1)
    pi.addWord('ddd', 0)
    words = pi.getWords(mincount=1)
    assert words == ['aaa', 'bbb', 'ccc']
    words = pi.getWords(mincount=2)
    assert words == ['aaa', 'bbb']
    pi.save()

# Run this test after running test_addwords()
def savedwords():
    pi = ProjectInfo(dir, language_code)
    words = pi.getWords(mincount=1)
    assert words == ['aaa', 'bbb', 'ccc']
    words = pi.getWords(mincount=2)
    assert words == ['aaa', 'bbb']

def add_to_savedwords():
    pi = ProjectInfo(dir, language_code)
    pi.addWord('bbb', 1)    # no effect
    pi.addWord('ccc', 3)
    words = pi.getWords(mincount=2)
    assert words == ['aaa', 'bbb', 'ccc']
    pi.save()

# Run this test after running test_savedwords()
def saidWords():
    saidwords = SaidWords(dir, language_code)
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
    pi = ProjectInfo(dir, language_code)
    words = pi.getWords(mincount=1)
    assert words == ['aaa', 'bbb', 'ccc', 'ddd']    # notice, 'eee' was not saved
    words = pi.getWords(mincount=3)
    assert words == ['aaa', 'bbb', 'ccc']
