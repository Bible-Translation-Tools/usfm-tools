# -*- coding: utf-8 -*-
# Manages language-specific information.
# Changes to the langauge info are held in memory until save() is called.
# Language info is saved to a json file in parent folder of project directory.
# The config file is named according to the language code. Such as mgv.json.
# If the json file already exists, it is loaded on LangaugeInfo initialization.

import json
import os
import io
import operator

class LanguageInfo:
    def __init__(self, project_dir, language_code):
        self.info = {}
        self.jsonpath = ""
        if os.path.exists( os.path.dirname(project_dir) ):
            self.jsonpath = os.path.join(os.path.dirname(project_dir), language_code+".json")
            if os.path.isfile(self.jsonpath):
                with io.open(self.jsonpath, 'r') as json_file:
                    self.info = json.load(json_file)
                assert 'language' in self.info
                assert 'source_translations' in self.info
                if not 'source_dir' in self.info:
                    self.info['source_dir'] = ""
                if not 'standard_chapter_title' in self.info:
                    self.info['standard_chapter_title'] = ""
                if not 'said_words' in self.info:
                    self.info['said_words'] = {}
        if not self.info:
            self.info = {'language': {'id': language_code, 'name': ""},
                        'source_translations': [],
                        'source_dir': "",
                        'standard_chapter_title': "",
                        'said_words': {} }

    def __repr__(self):
        return f'LanguageInfo({self.jsonpath})'

    # Saves the current information in the json file.
    def save(self):
        self.info['source_translations'].sort(reverse=True, key=operator.itemgetter('count'))    # sorts in place
        with io.open(self.jsonpath, 'w', newline='\n') as json_file:
            json.dump(self.info, json_file, indent=4)

    def setLanguageName(self, name):
        self.info['language']['name'] = name

    def getLanguageCode(self):
        return self.info['language']['id']
    def getLanguageName(self):
        return self.info['language']['name'] if 'name' in self.info['language'] else ""
    def getLanguageDirection(self):
        return self.info['language']['direction'] if 'direction' in self.info['language'] else ""

    # Overwrites the list of source translations
    def resetSources(self):
        self.info['source_translations'].clear()

    def addSource(self, language_id, resource_id, version):
        source = None
        assert 'source_translations' in self.info
        source = self.findSource(language_id, resource_id, version)
        if source:
            source['count'] = source['count'] + 1
        else:
            self.info['source_translations'].append( {'language_id': language_id,
                                                    'resource_id': resource_id,
                                                    'version': version,
                                                    'count': 1} )

    def getSources(self):
        return self.info['source_translations']
    def getMainSource(self):
        mainsource = None
        if len(self.info['source_translations']) > 0:
            self.info['source_translations'].sort(reverse=True, key=operator.itemgetter('count'))
            mainsource = self.info['source_translations'][0]
        return mainsource

    # used by self.addSource()
    def findSource(self, language_id, resource_id, version):
        found = None
        for source in self.getSources():
            if source['language_id'] == language_id and source['resource_id'] == resource_id and\
                source['version'] == version:
                found = source
                break
        return found

    def addChapterTitle(self, title):
        self.info['standard_chapter_title'] = title
    def getChapterTitle(self):
        assert 'standard_chapter_title' in self.info
        return self.info['standard_chapter_title']

    def setSourceDir(self, source_dir):
        self.info['source_dir'] = source_dir
    def getSourceDir(self):
        assert 'source_dir' in self.info
        return self.info['source_dir']

    # Adds or updates the specified word in LanguageInfo.
    def addWord(self, word, count):
        assert 'said_words' in self.info
        if word not in self.info['said_words'] or self.info['said_words'][word] < count:
            self.info['said_words'][word] = count

    # Returns the list of words with count greater than mincount.
    def getWords(self, mincount=1):
        return [word for word in self.info['said_words'] if self.info['said_words'][word] >= mincount]

    def clearWords(self):
        self.info['said_words'] = dict()
