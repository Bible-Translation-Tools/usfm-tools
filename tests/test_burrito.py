# pytest unit tests for Burrito class

import os
import sys
import shutil
import pytest

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
from scripture_burrito import Burrito

testdir = r'C:\DCS\Test\no_manifest'
# testdir = r'C:\DCS\Test'
# testdir = r'C:\DCS\Rai\bap-x-rai_reg'

def backup():
    # backup existing file
    path = os.path.join(testdir, "metadata.json")
    bakpath = os.path.join(testdir, "metadata_backup.json")
    if os.path.isfile(path) and not os.path.isfile(bakpath):
        shutil.copyfile(path, bakpath)
    elif os.path.isfile(bakpath) and not os.path.isfile(path):
        shutil.copyfile(bakpath, path)

@pytest.mark.parametrize('testdir',
    [(r'C:\DCS\Test\no_manifest'),
     (r'C:\DCS\Test'),
     (r'C:\DCS\Rai\bap-x-rai_reg'),
    ])
def test_validate(testdir):
    # Validates existing file.
    burrito = Burrito(testdir)
    is_valid, msg = burrito.load()
    if not is_valid:
        print(msg)
    assert is_valid

def test_init_burrito():
# Create a minimal, WA-specific Burrito.
    backup()
    burrito = Burrito(testdir)
    burrito.create()
    assert burrito.contents != {}
    burrito.addProject("COL", os.path.join(testdir, "52-COL.usfm"))
    is_valid, msg = burrito.save()
    print(msg)
    assert is_valid

def test_rewrite():
    backup()
    burrito = Burrito(testdir)
    is_valid, msg = burrito.load()
    assert is_valid
    content1 = burrito.contents
    is_valid, msg = burrito.save()
    assert is_valid
    is_valid, msg = burrito.load()
    assert is_valid
    content2 = burrito.contents
    assert content1 == content2

def test_change_generator():
    backup()
    burrito = Burrito(testdir)
    is_valid, msg = burrito.load()
    assert is_valid
    origname = burrito.contents['meta']['generator']['softwareName'] if 'generator' in burrito.contents['meta'] else None
    origversion = burrito.contents['meta']['generator']['softwareVersion'] if 'generator' in burrito.contents['meta'] else None
    name = "Another Generator"
    version = "2.0"
    burrito.setGenerator(name, version)
    assert 'generator' in burrito.contents['meta']
    assert burrito.contents['meta']['generator']['softwareName'] == name
    assert burrito.contents['meta']['generator']['softwareVersion'] == version
    is_valid, msg = burrito.save()
    assert is_valid
    if origname and origversion and (origname != name or origversion != version):
        burrito.setGenerator(origname, origversion)
        assert burrito.contents['meta']['generator']['softwareName'] == origname
        assert burrito.contents['meta']['generator']['softwareVersion'] == origversion
        is_valid, msg = burrito.save()
        assert is_valid
    else:
        name = "Test Generator"
        version = "1.0"
        burrito.setGenerator("Test Generator", "1.0")
        assert burrito.contents['meta']['generator']['softwareName'] == name
        assert burrito.contents['meta']['generator']['softwareVersion'] == version
        is_valid, msg = burrito.save()
        assert is_valid

def test_change_identification():
    backup()
    burrito = Burrito(testdir)
    is_valid, msg = burrito.load()
    assert is_valid
    locale = "fr"
    identity = "French Louis Segond 1910 Bible"
    abbrev = "Louis Segond Bible"
    repo = "Tech_Advance/auh_reg"
    burrito.setIdentification(locale, identity, abbrev, repo)
    assert 'wacs' in burrito.contents['identification']['primary']
    assert repo in burrito.contents['identification']['primary']['wacs']
    assert burrito.contents['identification']['primary']['wacs'][repo]['revision'] == "latest"
    assert 'timestamp' in burrito.contents['identification']['primary']['wacs'][repo]
    is_valid, msg = burrito.save()
    if not is_valid:
        print(msg)
    assert is_valid

def test_set_language():
    backup()
    burrito = Burrito(testdir)
    is_valid, msg = burrito.load()
    assert is_valid
    tag = "fr"
    locale = "en"
    name = "French"
    direction = "ltr"
    burrito.setLanguage(tag, locale, name, direction)
    assert 'languages' in burrito.contents
    assert len(burrito.contents['languages']) == 1
    assert burrito.contents['languages'][0]['tag'] == tag
    assert burrito.contents['languages'][0]['scriptDirection'] == direction
    assert locale in burrito.contents['languages'][0]['name']
    assert burrito.contents['languages'][0]['name'][locale] == name
    is_valid, msg = burrito.save()
    assert is_valid

    locale_fr = "fr"
    name_fr = "Français"
    burrito.setLanguage(tag, locale_fr, name_fr, direction)
    assert 'languages' in burrito.contents
    assert len(burrito.contents['languages']) == 1
    assert burrito.contents['languages'][0]['tag'] == tag
    assert burrito.contents['languages'][0]['scriptDirection'] == direction
    assert locale_fr in burrito.contents['languages'][0]['name']
    assert burrito.contents['languages'][0]['name'][locale_fr] == name_fr
    assert locale in burrito.contents['languages'][0]['name']
    assert burrito.contents['languages'][0]['name'][locale] == name
    is_valid, msg = burrito.save()
    assert is_valid

    tag = "es-419"
    locale = "en"
    name = "Spanish (Latin America and Caribbean)"
    direction = "ltr"
    burrito.setLanguage(tag, locale, name, direction)
    assert 'languages' in burrito.contents
    assert len(burrito.contents['languages']) == 1
    assert burrito.contents['languages'][0]['tag'] == tag
    assert burrito.contents['languages'][0]['scriptDirection'] == direction
    assert locale in burrito.contents['languages'][0]['name']
    assert burrito.contents['languages'][0]['name'][locale] == name
    is_valid, msg = burrito.save()
    assert is_valid

def test_add_names():
    backup()
    burrito = Burrito(testdir)
    is_valid, msg = burrito.load()
    assert is_valid
    obj = "REV"
    locale = "en"
    shortname = "Revelation"
    longname = "Book of Revelation"
    abbr = "REV"
    burrito.addName(obj, locale, shortname, longname, abbr=abbr)
    assert 'localizedNames' in burrito.contents
    assert obj in burrito.contents['localizedNames']
    assert burrito.contents['localizedNames'][obj]['short'][locale] == shortname
    assert burrito.contents['localizedNames'][obj]['long'][locale] == longname
    assert burrito.contents['localizedNames'][obj]['abbr'][locale] == abbr

    obj = "COL"
    locale = "en"
    shortname = "Colossians"
    longname = "Book of Colossians"
    abbr = "COL"
    burrito.addName(obj, locale, shortname, longname, abbr=abbr)
    assert obj in burrito.contents['localizedNames']
    assert len(burrito.contents['localizedNames']) >= 2
    assert burrito.contents['localizedNames'][obj]['short'][locale] == shortname
    assert burrito.contents['localizedNames'][obj]['long'][locale] == longname
    assert burrito.contents['localizedNames'][obj]['abbr'][locale] == abbr

    is_valid, msg = burrito.save()
    if not is_valid:
        print(msg)
    assert is_valid

def test_add_projects():
    backup()
    burrito = Burrito(testdir)
    is_valid, msg = burrito.load()
    assert is_valid
    bookId = "COL"
    filename = "52-COL.usfm"
    path = os.path.join(testdir, filename)
    # if not "ingredients" in burrito.contents or not filename in burrito.contents['ingredients'] if 'ingredients' in burrito.contents else []:
    burrito.addProject(bookId, path)
    assert 'ingredients' in burrito.contents
    assert filename in burrito.contents['ingredients']
    assert burrito.contents['ingredients'][filename]['scope'] == {bookId: []}

    bookId = "PHP"
    filename = "51-PHP.usfm"
    path = os.path.join(testdir, filename)
    burrito.addProject(bookId, path)
    assert filename in burrito.contents['ingredients']
    assert burrito.contents['ingredients'][filename]['scope'] == {bookId: []}

    bookId = "MAT"
    filename = "41-MAT.usfm"
    path = os.path.join(testdir, filename)
    burrito.addProject(bookId, path)
    assert filename in burrito.contents['ingredients']
    assert burrito.contents['ingredients'][filename]['scope'] == {bookId: []}
    assert len(burrito.contents['ingredients']) >= 3

    is_valid, msg = burrito.save()
    if not is_valid:
        print(msg)
    assert is_valid
