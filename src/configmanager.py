# -*- coding: utf-8 -*-
# USFM Wizard tools config file manager

from configparser import ConfigParser, SectionProxy
import os, platform
import io

class ToolsConfigManager:
    _instance = None

    # Singleton implementation - don't override __init__()
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolsConfigManager, cls).__new__(cls)
            cls._instance._init_config()
        return cls._instance

    # Parses the config file.
    # Creates it with default values if necessary.
    def _init_config(self):
        match platform.system():
            case "Windows":
                path = os.path.expanduser("~/AppData/Local/usfm_wizard")
            case "Linux":
                path = os.path.expanduser("~/.config/usfm_wizard")
            case "Darwin":
                path = os.path.expanduser("~/Library/Application Support/usfm_wizard")
        if not os.path.exists(path):
            os.mkdir(path)
        self.configpath = os.path.join(path, "tools_config.ini")
        self.cfgParser = ConfigParser()
        self.cfgParser.read(self.configpath, encoding='utf-8')
        if not self.cfgParser.sections():
            self._make_default_config()
            self.cfgParser.read(self.configpath, encoding='utf-8')

    def __repr__(self):
        return f'ToolsConfigManager({self.configpath})'

    def _make_default_config(self):
        for section in ['MarkParagraphs','RevertChanges','SelectProcess',
                        'Txt2USFM','UsfmCleanup','VerifyManifest','VerifyUSFM']:
            self.cfgParser.add_section(section)
            self.cfgParser[section] = self.default_section(section)
        with io.open(self.configpath, "tw", encoding='utf-8', newline='\n') as file:
            self.cfgParser.write(file)

    # Reads the last saved version of the config file.
    # Used by unit tests only.
    def _reread(self):
        self.cfgParser.read(self.configpath, encoding='utf-8')

    # Returns the config file path.
    def config_path(self):
        return self.configpath

    def get(self, sectionname, option):
        value = ""
        if not self.cfgParser.has_section(sectionname) or len(self.cfgParser[sectionname]) == 0:
            defaultvalues = self.default_section(sectionname)
            if defaultvalues:
                self.set_section(sectionname, defaultvalues)
                value = self.cfgParser.get(sectionname, option, fallback="")
        else:
            value = self.cfgParser.get(sectionname, option, fallback="")
        return value

    def getboolean(self, sectionname, option):
        value = self.get(sectionname, option)
        return (value in {'True', 'true', '1'})

    # Deprecated; use get() and getboolean()
    def get_section(self, sectionname) -> SectionProxy:
        if not self.cfgParser.has_section(sectionname) or len(self.cfgParser[sectionname]) == 0:
            values = self.default_section(sectionname)
            self.set_section(sectionname, values)
        return self.cfgParser[sectionname]

    def set(self, section:str, option:str, value: str|bool):
        if not self.cfgParser.has_section(section):
            self.cfgParser.add_section(section)
        if isinstance(value, bool):
            value = "True" if value else "False"
        self.cfgParser.set(section, option, value)

    # Updates the section with the specified values.
    # Doesn't overwrite options not specified.
    def set_section(self, sectionname, values:dict):
        for value in values:
            self.set(sectionname, value, values[value])

    # Rewrites the entire configuration file with current values.
    def save(self):
        with io.open(self.configpath, "tw", encoding='utf-8', newline='\n') as file:
            self.cfgParser.write(file)

    # Returns a default dict for the specified section.
    def default_section(self, sectionname):
        match sectionname:
            case 'MarkParagraphs':
                sec = {'language_code': "",
                    'source_dir': "",
                    'model_dir': "",
                    'filename': "",
                    'copy_nb': False,
                    'removeS5markers': True,
                    's5_to_p': False,
                    'mark_every_verse': False }
            case 'Plaintext2Usfm':
                sec = {'source_dir': "",
                       'filename': "",
                       'target_dir': ""}
            case 'Paratext2Usfm':
                sec = {'paratext_dir': "",
                       'target_dir': "",
                       'filename': ""}
            case 'RevertChanges':
                sec = {'source_dir': "",
                       'backupExt': "",
                       'correctExt': ".usfm" }
            case 'SelectProcess':
                sec = {'selection': 'Txt2USFM'}
            case 'Txt2USFM':
                sec = {'source_dir': "",
                       'target_dir': "",
                       'mark_chunks': False,
                       'language_code': "",
                       'section_headings': False }
            case 'UsfmCleanup':
                sec = {'language_code': "",
                    'source_dir': "",
                    'filename': "",
                    'standard_chapter_title': "",
                    'enable1': True,
                    'enable2': True,
                    'enable3': False,
                    'enable4': False,
                    'enable5': False,
                    'enable6': True,
                    'enable7': False,
                    'enable8': False,
                    'sourcetext_dir': "" }
            case 'Usfm2Usx':
                sec = {'source_dir': "",
                       'rc_dir': "",
                       'language_name': "",
                       'language_code': "",
                       'bible_name': "",
                       'bible_id': "",
                       'direction': "ltr",
                       'pub_date': "",
                       'license': "",
                       'version': "" }
            case 'Usx2Usfm':
                sec = {'usx_dir': "",
                       'filename': "",
                       'usfm_dir': "",
                       'notes': False }
            case 'VerifyManifest':
                sec = {'source_dir': "",
                       'expectascii': False,
                       'bibletype': True }
            case 'VerifyUSFM':
                sec = {'source_dir': "",    # location of usfm files to be checked
                       'filename': "",
                       'compare_dir': "",   # the source language folder, for comparisons
                       'language_code': "",
                       'standard_chapter_title': "",
                    #    'usfm_version': "2.0",
                       'suppress1': False,
                       'suppress2': False,
                       'suppress3': False,
                       'suppress4': False,
                       'suppress5': False,
                       'suppress6': False,
                       'suppress7': False,
                       'suppress8': False,
                       'suppress9': False,
                       'suppress10': False,
                       'suppress11': False,
                       'suppress12': False, }
            case 'Word2text':
                sec = {'source_dir': "",
                       'filename': "",
                       'target_dir': ""}
            case _:
                sec = {}
        return sec
