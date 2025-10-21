# pytest unit tests for functions in manifestjson.py

import os
import sys
import pytest

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
from manifestjson import ManifestJson

dir = r'C:\DCS\Test\llx_mrk_text_reg'
nomanifest_dir = r'C:\DCS\Test\no_manifest'
# language_code = 'test'
# language_name = 'Test Language'

def test_nonexistent_manifest():
    mj = ManifestJson()
    errors = mj.load(nomanifest_dir)
    assert errors and errors[0].startswith('File not found:')
    assert mj.getLanguageId() == ""
    assert not mj.contents

def test_all():
    mj = ManifestJson()
    assert mj.load(dir) == []
    assert mj.getLanguageId() == "llx"
    assert mj.getLanguageName() == "Lauan"
    assert mj.getLanguageDirection() == "ltr"
    assert mj.getBookId() == "mrk"
    assert mj.getResourceId() == "reg"
    assert len(mj.getTranslators()) == 4
    assert mj.getTranslators()[3] == "ezar.chandra"
    assert len(mj.getSources()) == 3
    assert mj.getSources()[1]['version'] == "9"
    assert mj.getSources()[2]['version'] == "12"
