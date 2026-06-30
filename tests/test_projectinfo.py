# pytest unit tests for functions in projectinfo.py
# Before running all the tests as a whole:
#   Manifest.yaml in test_dir should have a valid language direction and a language identifer.
#   Manifest.yaml should have one, syntactially complete source.
#   C:\DCS\Test\test.json should have no "said_words" defined.

import os
import sys

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
from projectinfo import ProjectInfo, SaidWords
from manifestyaml import ManifestYaml
from scripture_burrito import Burrito

test_dir = r'C:\DCS\Test\test_pi'
saidwords_dir = r'C:\DCS\Test\test_reg'
language_code = 'test-pi'
saidwords_language_code = "test"

def test_init_newfile():
    # This test function backs up the existing .json file before deleting it.
    path = os.path.join(os.path.dirname(test_dir), language_code+'.json')
    bakpath = path + ".bak"
    if os.path.exists(path):
        if not os.path.exists(bakpath):
            os.rename(path, bakpath)
        else:
            os.remove(path)
    projectInfo = ProjectInfo(test_dir, language_code)
    projectInfo.useManifest(docreate=True)
    assert projectInfo.getLanguageCode() == language_code
    projectInfo.save()
    assert projectInfo.getLanguageCode() == language_code

def test_init_badid():
    newcode = 'xyz'
    projectInfo = ProjectInfo(test_dir, newcode)
    assert projectInfo.getLanguageCode() == newcode

def test_init_noid():
    newcode = ''
    projectInfo = ProjectInfo(test_dir, newcode)
    assert projectInfo.getLanguageCode() == newcode
    projectInfo.save()
    projectInfo = ProjectInfo(test_dir, newcode)
    assert projectInfo.getLanguageCode() == newcode

def test_init_oldfile():
    projectInfo = ProjectInfo(test_dir, language_code)
    assert projectInfo.getLanguageCode() == language_code
    projectInfo = ProjectInfo(test_dir, '')
    assert projectInfo.getLanguageCode() == ''

def test_bad_dir():
    bad_dir = r'C:\DCS\Test\nonexistent_dir'
    language_code = 'test_bad_dir'
    projectInfo = ProjectInfo(bad_dir, language_code)
    assert projectInfo
    projectInfo.useManifest(True)
    assert not projectInfo.manifest
    assert projectInfo.getSources() == []
    assert not projectInfo.getMainSource()
    assert projectInfo.getWords() == []
    assert projectInfo.getLanguageCode() == language_code

def test_language_name():
    language_name = 'Test ProjectInfo'
    projectInfo = ProjectInfo(test_dir, language_code)
    projectInfo.setLanguage(language_name, 'en', 'rtl')
    projectInfo.save()
    assert projectInfo.getLanguageName() == language_name

def test_mainsource():
    source_lang = 'test-source'
    source_resource_id = 'uub'
    source_ver = "1.8"
    test_lang = 'test-pi'

    my = ManifestYaml()
    my.load(test_dir)
    sources = my.getSources()
    if len(sources) > 0:
        assert sources[0]['language'] == source_lang
        assert sources[0]['identifier'] == source_resource_id
        assert sources[0]['version'] == source_ver
    else:
        my.addSource(source_lang, source_resource_id, source_ver)
    my.save()

    pi = ProjectInfo(test_dir, test_lang)
    assert pi.getMainSource()
    pi.resetSources()   # doesn't affect manifest.yaml which is not used yet
    assert pi.getMainSource() == None
    pi.useManifest(docreate=True)
    source = pi.getMainSource()     # gets it from manifest.yaml
    assert source['language_id'] == source_lang
    assert source['resource_id'] == source_resource_id
    assert source['version'] == source_ver
    assert source['count'] == 1

def test_sources():
    add1source('swedish', 'bible', '1.99')
    projectInfo = ProjectInfo(test_dir, language_code)
    projectInfo.addSource('en', 'ulb', '7.6')
    projectInfo.addSource('en', 'ulb', '7.6')
    projectInfo.addSource('en', 'ulb', '2')
    assert len(projectInfo.getSources()) == 3
    projectInfo.save()
    pi2 = ProjectInfo(test_dir, language_code)
    source = pi2.getMainSource()
    assert source['version'] == "7.6"

def add1source(lang, resource_id, ver):
    lang = 'swedish'
    # resource_id = 'bible'
    ver = '1.99'
    projectInfo = ProjectInfo(test_dir, language_code)
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

# The manifest.yaml file in workdir should have valid language info before running this.
# Manifest.yaml should have exactly one valid source before running this.
def test_manifest_connection():
    workdir = r'C:\DCS\Test\test_reg'
    working_lang_code = 'test'
    pi = ProjectInfo(workdir, working_lang_code)
    pi.resetSources()
    pi.setLanguage("")
    assert len(pi.getSources()) == 0
    assert pi.getLanguageName() == ""

    burrito = Burrito(workdir)
    (was_valid, msg) = burrito.load()
    my = ManifestYaml()
    my.load(workdir)
    myname = my.getLanguageName()
    mydirection = my.getLanguageDirection()
    mylen = len(my.getSources())
    assert mylen == 1   # Necessary for the following tests to work

    pi.useManifest(docreate=True)        # sync happens here
    pilen = len(pi.getSources())
    assert pilen == 1               # from the sync from manifest
    piname = pi.getLanguageName()
    assert piname != ""
    pi.save()

    burrito = Burrito(workdir)
    (is_valid,msg) = burrito.load()
    assert is_valid == was_valid  # empty language name means json file was not overwritten

    # New ProjectInfo object, not synced to Manifest
    pi_nosync = ProjectInfo(workdir, working_lang_code)
    assert len(pi_nosync.getSources()) == pilen
    pi_nosync.setLanguage("Mangled name", 'en', "mangled direction")
    assert pi_nosync.getLanguageName() == "Mangled name"
    pi_nosync.addSource('bogus', 'ulc', 'v2')
    assert len(pi_nosync.getSources()) == pilen + 1
    pi_nosync.sync()   # does not sync with manifest
    assert len(pi_nosync.getSources()) == pilen + 1
    pi_nosync.save()   # does not save manifest

    my.load(workdir)
    assert my.getLanguageId() == working_lang_code
    assert my.getLanguageName() == myname   # sync didn't happen
    assert my.getLanguageDirection() == mydirection   # bad value wasn't saved
    assert len(my.getSources()) == mylen

    pi.setLanguage("Sync name", "en", "bad direction")
    assert pi.getLanguageName() == "Sync name"
    pi.addSource('bogus', 'uld', 'v3')
    pi.save()
    my.load(workdir)
    assert my.getLanguageName() == "Sync name"   # existing name wasn't overwritten
    assert my.getLanguageDirection() in {'rtl','ltr'}   # direction is not affected
    assert len(my.getSources()) == mylen + 1

    (is_valid,msg) = burrito.load()
    assert is_valid == was_valid     # bad direction

    pi.setLanguage(myname, 'en', mydirection)
    pi.resetSources()
    pi.addSource('en', 'uxb', '12')
    pi.save()   # should restore language and source entries
    (is_valid,msg) = burrito.load()
    assert is_valid == was_valid     # validity unchanged

# Before running this test, test.json in saidwords_dir should have no "said_words" defined.
def test_saidwords():
    nowords()
    addwords()
    savedwords()
    add_to_savedwords()
    saidWords()
    savedSaidWords()
    clearwords()    # reset for next time

def nowords():
    pi = ProjectInfo(saidwords_dir, saidwords_language_code)
    words = pi.getWords()
    assert words == []

def addwords():
    pi = ProjectInfo(saidwords_dir, saidwords_language_code)
    pi.addWord('aaa', 2)
    pi.addWord('bbb', 3)
    pi.addWord('ccc', 1)
    pi.addWord('ddd', 0)
    words = pi.getWords(mincount=1)
    assert words == ['aaa', 'bbb', 'ccc']
    words = pi.getWords(mincount=2)
    assert words == ['aaa', 'bbb']
    pi.save()

def savedwords():
    pi = ProjectInfo(saidwords_dir, saidwords_language_code)
    words = pi.getWords(mincount=1)
    assert words == ['aaa', 'bbb', 'ccc']
    words = pi.getWords(mincount=2)
    assert words == ['aaa', 'bbb']

def add_to_savedwords():
    pi = ProjectInfo(saidwords_dir, saidwords_language_code)
    pi.addWord('bbb', 1)    # no effect
    pi.addWord('ccc', 3)
    words = pi.getWords(mincount=2)
    assert words == ['aaa', 'bbb', 'ccc']
    pi.save()

def saidWords():
    saidwords = SaidWords(saidwords_dir, saidwords_language_code)
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
    pi = ProjectInfo(saidwords_dir, saidwords_language_code)
    words = pi.getWords(mincount=1)
    assert words == ['aaa', 'bbb', 'ccc', 'ddd']    # notice, 'eee' was not saved
    words = pi.getWords(mincount=3)
    assert words == ['aaa', 'bbb', 'ccc']

def clearwords():
    saidwords = SaidWords(saidwords_dir, saidwords_language_code)
    saidwords._clearWords()
    saidwords.save(mincount=1000)   # this clears the words in the language info file

def test_addSourceDir():
    workdir = r'C:\DCS\Test\test_reg'
    sourcedir = r'C:\DCS\Nepali\invaliddir'
    pi = ProjectInfo(workdir, 'test')
    pi.setSourceDir(sourcedir)
    assert pi.getSourceDir() == sourcedir
    pi.save()
    assert pi.getSourceDir() == sourcedir

def test_addChapterTitle():
    workdir = r'C:\DCS\Test\test_reg'
    title = 'sample chapter title'
    pi = ProjectInfo(workdir, 'test')
    pi.setStandardChapterTitle(title)
    assert pi.getStandardChapterTitle() == title
    pi.save()
    assert pi.getStandardChapterTitle() == title

def test_setGenerator():
    workdir = r'C:\DCS\Test\no_manifest'
    name = "Generator Test"
    version = "0"
    pi = ProjectInfo(workdir, 'test')
    pi.setGenerator(name, version)
    pi.save()

    burrito = Burrito(workdir)
    is_valid, msg = burrito.load()
    assert is_valid
    assert 'generator' in burrito.contents['meta']
    assert burrito.contents['meta']['generator']['softwareName'] == name
    assert burrito.contents['meta']['generator']['softwareVersion'] == version

    # Reset generator to something else
    name += " Undo"
    version += "99"
    pi.setGenerator(name, version)
    pi.save()
    is_valid, msg = burrito.load()
    assert is_valid
    assert burrito.contents['meta']['generator']['softwareName'] == name
    assert burrito.contents['meta']['generator']['softwareVersion'] == version
