# pytest unit tests for ToolsConfigManager

import os
import sys
# import pytest
import shutil

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
from configmanager import ToolsConfigManager

'''
Test these functions:
  constructor   - does it create a default config file if none exists
                - does it read existing config file
                - does a second constructor return the same object (mgr1 is mgr2)
  config_path   - does it return the expected path
  set           - does it set string values correctly
                - does it set boolean values correctly
  set_section   - does it create new section with specified options
                - does it overwrite existing options with new values
                - does it preserve existing options where no new value is specified
  get           - does it return "" for a non-existing section
                - does it return "" for a non-existing option
                - does it return correct value for existing options
  getboolean    - does it return False for non-existing section or option
                - does it return True for "True", "true", and "1"
                - does it return False for other values
  save          - does it save values correctly
                - are values not saved when save() is not called
'''

def backup_keeper_ini():
    path = os.path.expanduser("~/AppData/Local/usfm_wizard")
    path = os.path.join(path, "tools_config.ini")
    bakpath = path + ".keep"
    if os.path.exists(path) and not os.path.exists(bakpath):
        shutil.copyfile(path, bakpath)

def test_new():
    backup_keeper_ini()
    path = os.path.expanduser("~/AppData/Local/usfm_wizard")
    path = os.path.join(path, "tools_config.ini")
    os.remove(path)
    mgr = ToolsConfigManager()
    mgr2 = ToolsConfigManager()
    assert mgr2 is mgr

    assert os.path.exists(path)
    assert mgr.get('RevertChanges', 'correctExt') == ".usfm"    # a default value
    assert mgr.get('Usfm2Usx', 'direction') == 'ltr'
    assert mgr.get('WWWWW', 'XXXXXXX') == ''

    mgr2 = ToolsConfigManager()
    assert mgr2 is mgr
    assert mgr.config_path() == path
    restore_keeper_ini()

def test_all():
    backup_keeper_ini()
    mgr = ToolsConfigManager()
    mgr.set('TESTSECTION', 'testoption', 'testvalue')
    assert mgr.get('TESTSECTION', 'testoption') == 'testvalue'
    assert mgr.getboolean('TESTSECTION', 'testoption') == False
    mgr.set('TESTSECTION', 'testoption', True)
    assert mgr.get('TESTSECTION', 'testoption') == 'True'
    assert mgr.getboolean('TESTSECTION', 'testoption') == True
    assert mgr.get('BADSECTION', 'testoption') == ""
    assert mgr.get('TESTSECTION', 'badoption') == ""
    assert mgr.getboolean('X', 'testoption') == False
    assert mgr.getboolean('TESTSECTION', 'x') == False
    mgr.set('TESTSECTION', 'testoption', False)
    assert mgr.get('TESTSECTION', 'testoption') == 'False'
    assert mgr.getboolean('TESTSECTION', 'testoption') == False
    mgr.save()

    assert mgr.get('TESTSECTION', 'testoption') == 'False'

    values = {'option1': 'value1', 'option2': 'value2'}
    mgr.set_section('TESTSECTION', values)
    assert mgr.get('TESTSECTION', 'option1') == 'value1'
    assert mgr.get('TESTSECTION', 'option2') == 'value2'
    assert mgr.get('TESTSECTION', 'testoption') == 'False'
    mgr.save()

    values = {'option1': 'newvalue', 'option2': 'value2', 'testoption': True}
    mgr.set_section('TESTSECTION', values)
    assert mgr.get('TESTSECTION', 'option1') == 'newvalue'
    assert mgr.get('TESTSECTION', 'option2') == 'value2'
    assert mgr.getboolean('TESTSECTION', 'testoption') == True
    # Do not save these values

    mgr._reread()     # read last saved value; lose the current in-memory values
    assert mgr.getboolean('TESTSECTION', 'testoption') == False
    assert mgr.get('TESTSECTION', 'option1') == 'value1'
    assert mgr.get('TESTSECTION', 'option2') == 'value2'
    restore_keeper_ini()

def restore_keeper_ini():
    path = os.path.expanduser("~/AppData/Local/usfm_wizard")
    path = os.path.join(path, "tools_config.ini")
    lastsavedpath = path + ".lastsaved"
    if os.path.exists(lastsavedpath):
        os.remove(lastsavedpath)
    shutil.copyfile(path, lastsavedpath)
    bakpath = path + ".keep"
    if os.path.exists(bakpath):
        if os.path.exists(path):
            os.remove(path)
        os.rename(bakpath, path)
