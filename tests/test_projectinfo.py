# pytest unit tests for functions in projectinfo.py
# Before running all the tests as a whole:
#   Manifest.yaml should have valid language info.
#   Manifest.yaml should each have one valid source.
#   remove "said_words" from test.json, or set it to an empty dict -- {}

import os
import sys

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
from projectinfo import ProjectInfo, SaidWords
from manifestyaml import ManifestYaml

dir = r'C:\DCS\Test\test_pi'
language_code = 'test-pi'
language_name = 'Test ProjectInfo'
source_lang = 'test-source'
source_resource_id = 'uub'
source_ver = "1.8"

def test_init_newfile():
    # This test function backs up the existing .json file before deleting it.
    path = os.path.join(os.path.dirname(dir), language_code+'.json')
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

def test_mainsource():
    my = ManifestYaml()
    my.load(dir)
    sources = my.getSources()
    if len(sources) > 0:
        assert sources[0]['language'] == source_lang
        assert sources[0]['identifier'] == source_resource_id
        assert sources[0]['version'] == source_ver
    else:
        my.addSource(source_lang, source_resource_id, source_ver)
    my.save()
    pi = ProjectInfo(dir, language_code)
    pi.resetSources()
    assert pi.getMainSource() == None
    pi.useManifest()
    source = pi.getMainSource()
    assert source['language_id'] == source_lang
    assert source['resource_id'] == source_resource_id
    assert source['version'] == source_ver
    assert source['count'] == 1

def test_sources():
    add1source('swedish', 'bible', '1.99')
    projectInfo = ProjectInfo(dir, language_code)
    projectInfo.addSource('en', 'ulb', '7.6')
    projectInfo.addSource('en', 'ulb', '7.6')
    projectInfo.addSource('en', 'ulb', '2')
    assert len(projectInfo.getSources()) == 3
    projectInfo.save()
    pi2 = ProjectInfo(dir, language_code)
    source = pi2.getMainSource()
    assert source['version'] == "7.6"

def add1source(lang, resource_id, ver):
    lang = 'swedish'
    # resource_id = 'bible'
    ver = '1.99'
    projectInfo = ProjectInfo(dir, language_code)
    projectInfo.addSource(lang, resource_id, ver)
    assert projectInfo.knownSource(lang, resource_id, ver) == True
    projectInfo.resetSources()
    assert projectInfo.knownSource(lang, resource_id, ver) == False
    projectInfo.addSource(lang, resource_id, ver)
    assert projectInfo.knownSource(lang, resource_id, ver) == True
    source = projectInfo.getMainSource()
    assert source['language_id'] == lang
    assert source['resource_id'] == resource_id
    assert source['version'] == ver
    assert source['count'] == 1
    projectInfo.save()

# Manifest.yaml should have valid language info before running this.
# Manifest.yaml should have exactly one valid source before running this.
def test_manifest_connection():
    dir = r'C:\DCS\Test\test_reg'
    language_code = 'test'
    pi = ProjectInfo(dir, language_code)
    pi.resetSources()
    pi.setLanguage("")
    n = len(pi.getSources())
    assert n == 0
    assert pi.getLanguageName() == ""

    my = ManifestYaml()
    my.load(dir)
    myname = my.getLanguageName()
    mydirection = my.getLanguageDirection()
    mylen = len(my.getSources())
    assert mylen == 1   # Necessary for the following tests to work

    pi.useManifest()        # sync happens here
    pilen = len(pi.getSources())
    assert pilen == 1  # the one is from the sync from manifest
    piname = pi.getLanguageName()
    assert piname != ""
    pi.save()

    # New ProjectInfo object, not synced to Manifest
    pi_nosync = ProjectInfo(dir, language_code)
    assert len(pi_nosync.getSources()) == pilen
    pi_nosync.setLanguage("Mangled name", "mangled direction")
    assert pi_nosync.getLanguageName() == "Mangled name"
    pi_nosync.addSource('bogus', 'ulc', 'v2')
    assert len(pi_nosync.getSources()) == pilen + 1
    pi_nosync.sync()   # does not sync with manifest
    assert len(pi_nosync.getSources()) == pilen + 1
    pi_nosync.save()   # does not save manifest

    my.load(dir)
    assert my.getLanguageId() == language_code
    assert my.getLanguageName() == myname   # sync didn't happen
    assert my.getLanguageDirection() == mydirection   # bad value wasn't saved
    assert len(my.getSources()) == mylen

    pi.setLanguage("Sync name", "bad direction")
    assert pi.getLanguageName() == "Sync name"
    pi.addSource('bogus', 'uld', 'v3')
    pi.save()
    my.load(dir)
    assert my.getLanguageName() == "Sync name"   # existing name wasn't overwritten
    assert my.getLanguageDirection() in {'rtl','ltr'}   # direction is not affected
    assert len(my.getSources()) == mylen + 1

    pi.setLanguage(myname, mydirection)
    pi.save()   # should restore language entry in both files

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

def test_addSourceDir():
    workdir = r'C:\DCS\Test\test_reg'
    sourcedir = r'C:\DCS\Nepali\invaliddir'
    pi = ProjectInfo(workdir, 'test')
    pi.setSourceDir(sourcedir)
    assert pi.getSourceDir() == sourcedir
    pi.save()
    assert pi.getSourceDir() == sourcedir

def savedSaidWords():
    pi = ProjectInfo(dir, language_code)
    words = pi.getWords(mincount=1)
    assert words == ['aaa', 'bbb', 'ccc', 'ddd']    # notice, 'eee' was not saved
    words = pi.getWords(mincount=3)
    assert words == ['aaa', 'bbb', 'ccc']
