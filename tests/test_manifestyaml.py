# pytest unit tests for functions in projectinfo.py

import os
import sys
import pytest

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
from manifestyaml import ManifestYaml

dir = r'C:\DCS\Test\test_reg'
nomanifest_dir = r'C:\DCS\Test\no_manifest'
language_code = 'test'
language_name = 'Test Language'

def test_nonexistent_manifest():
    my = ManifestYaml()
    errors = my.load(nomanifest_dir)
    assert errors and errors[0].startswith('File not found:')
    assert my.getLanguageId() + "_" + my.getResourceId() == "_"
    assert not my.contents
    assert my.getLanguageId() == ""

def test_all():
    init_newfile()
    addContributors()
    dates()
    sources()
    replaceSources()
    addProjects()
    addRelations()

def init_newfile():
    # This test function backs up the existing .json file before deleting it.
    path = os.path.join(dir, 'manifest.yaml')
    bakpath = path + ".bak"
    if os.path.exists(path):
        if not os.path.exists(bakpath):
            os.rename(path, bakpath)
        else:
            os.remove(path)
    my = ManifestYaml()
    my.create(dir, language_code)
    my.setLanguageId(language_code)
    my.setLanguageName(language_name)
    my.setLanguageDirection('rtl')
    my.save()
    assert my.contents['dublin_core']['language']['identifier'] == language_code
    my2 = ManifestYaml()
    assert my2.load(dir) == []
    assert my2.contents['dublin_core']['language']['title'] == language_name
    assert my2.getLanguageId() == language_code
    assert my2.getLanguageName() == language_name
    assert my2.getLanguageDirection() == "rtl"
    assert my2.getResourceId() == 'reg'     # default value

# Creates a new manifest file, with contributors.
def addContributors():
    my = ManifestYaml()
    my.create(dir, language_code)
    my.setLanguageId(language_code)
    my.setLanguageName(language_name)
    my.setLanguageDirection('rtl')
    my.addContributor('david')
    my.addContributor('David')
    assert len(my.contents['dublin_core']['contributor']) == 1
    con = my.contents['dublin_core']['contributor'][0]
    assert con == 'David'
    my.addContributor('O\'Shea')
    assert len(my.contents['dublin_core']['contributor']) == 2
    con = my.contents['dublin_core']['contributor'][1]
    assert con == 'O\'Shea'
    my.addContributor('Allen')
    my.addContributor('     ')  # empty contributors should not be saved
    my.save()
    my2 = ManifestYaml()
    my2.load(dir)
    assert len(my2.contents['dublin_core']['contributor']) == 3
    con = my2.contents['dublin_core']['contributor'][0]
    assert con == 'Allen'
    con = my2.contents['dublin_core']['contributor'][1]
    assert con == 'David'
    con = my2.contents['dublin_core']['contributor'][2]
    assert con == 'O\'Shea'

def dates():
    my = ManifestYaml()
    date = "2025-01-01"
    if errors := my.load(dir):
        my.create(dir)
    my.setDates(date)
    my.save()
    my2 = ManifestYaml()
    assert my2.load(dir) == []
    assert my2.contents['dublin_core']['issued'] == date
    assert my2.contents['dublin_core']['modified'] == date
    con = my2.contents['dublin_core']['contributor'][2]
    assert con == 'O\'Shea'

def sources():
    my = ManifestYaml()
    if errors := my.load(dir):
        my.create(dir)
    my.addSource('en', 'ulb', '12')
    assert len(my.contents['dublin_core']['source']) == 1
    src = my.contents['dublin_core']['source'][0]
    assert src['language'] == 'en'
    assert src['identifier'] == 'ulb'
    assert src['version'] == '12'
    assert my.contents['dublin_core']['version'] == ""

    my.addSource('en', 'ulb', '12') # try to add same source again
    assert len(my.contents['dublin_core']['source']) == 1
    my.addSource('am', 'udb', '1') # try to add another source
    assert len(my.contents['dublin_core']['source']) == 2
    src = my.contents['dublin_core']['source'][1]
    assert src['language'] == 'am'
    assert src['identifier'] == 'udb'
    assert src['version'] == '1'
    my.addSource('en', 'ulb', 'WA12') # try to add same source again
    assert len(my.contents['dublin_core']['source']) == 3
    my.setVersion("12.1")
    my.save()
    my2 = ManifestYaml()
    my2.load(dir)
    assert len(my2.contents['dublin_core']['source']) == 3
    src = my2.contents['dublin_core']['source'][0]
    assert src['language'] == 'en'
    assert src['identifier'] == 'ulb'
    assert src['version'] == '12'
    assert my2.contents['dublin_core']['version'] == "12.1"

def replaceSources():
    my = ManifestYaml()
    if errors := my.load(dir):
        my.create(dir)
    my.resetSources()
    my.setVersion("")
    assert my.contents['dublin_core']['version'] == ""
    assert len(my.contents['dublin_core']['source']) == 0
    my.addSource('en', 'ulb', '12') # try to add same source again
    assert len(my.contents['dublin_core']['source']) == 1
    assert my.contents['dublin_core']['version'] == ""
    my.setVersion("12.2")
    my.save()
    my2 = ManifestYaml()
    my2.load(dir)
    assert len(my2.contents['dublin_core']['source']) == 1
    src = my2.contents['dublin_core']['source'][0]
    assert src['language'] == 'en'
    assert src['identifier'] == 'ulb'
    assert src['version'] == '12'
    assert my2.contents['dublin_core']['version'] == "12.2"

def addProjects():
    my = ManifestYaml()
    if errors := my.load(dir):
        my.create(dir)
    proj66 = {'title': 'Revelation', 'versification': 'ufw', 'identifier': 'rev',
            'sort': 66, 'path': './67-REV.usfm', 'categories': [ 'bible-nt' ] }
    proj1 = {'title': 'Matthew', 'versification': 'ufw', 'identifier': 'mat',
            'sort': 40, 'path': './41-MAT.usfm', 'categories': [ 'bible-nt' ] }
    proj2 = {'title': 'Mark', 'versification': 'ufw', 'identifier': 'mrk',
            'sort': 41, 'path': './42-MRK.usfm', 'categories': [ 'bible-nt' ] }
    my.addProject(proj66)
    my.addProject(proj1)
    my.addProject(proj2)
    my.save()
    my2 = ManifestYaml()
    my2.load(dir)
    assert len(my2.contents['projects']) == 3
    assert my2.contents['projects'][0] == proj1
    assert my2.contents['projects'][1] == proj2
    assert my2.contents['projects'][2] == proj66
    proj2a = {'title': 'Markus', 'versification': 'ufw', 'identifier': 'mrk',
            'sort': 41, 'path': './42-MRK.usfm', 'categories': [ 'bible-nt' ] }
    assert my2.contents['projects'][1] != proj2a
    my2.addProject(proj2a)
    assert len(my2.contents['projects']) == 3
    my2.save()
    my.load(dir)
    assert len(my.contents['projects']) == 3
    assert my.contents['projects'][0] == proj1
    assert my.contents['projects'][1] == proj2a
    assert my.contents['projects'][2] == proj66

def addRelations():
    my = ManifestYaml()
    if errors := my.load(dir):
        my.create(dir)
    my.addRelation(language_code, 'reg')
    my.addRelation(language_code, 'tn')
    my.addRelation(language_code, 'reg')
    my.save()
    my2 = ManifestYaml()
    my2.load(dir)
    assert len(my2.contents['dublin_core']['relation']) == 2
    assert my2.contents['dublin_core']['relation'][0] == language_code + "/" + "reg"
    assert my2.contents['dublin_core']['relation'][1] == language_code + "/" + "tn"
