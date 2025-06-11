# -*- coding: utf-8 -*-
# Manages project-specific information.
# Changes to the project info are held in memory until save() is called.
# Project info can be saved to a json configuration file in parent folder of project directory.
# The config file is named according to the language code. Such as mgv.json.
# If the json file already exists, it is loaded on ProjectInfo initialization.
# Other parts of project info can be saved to a manifest.yaml file in project directory.
# The contents of the two files overlap.
# ProjectInfo also manages manifest.yaml via the manifestyaml module.
# The SaidWords class, defined in this file, is a helper class.

import json
import os
import io
import operator
from manifestyaml import ManifestYaml

class ProjectInfo:
    def __init__(self, project_dir, language_code):
        self.project_dir = project_dir      # will need self.project_dir for manifest support
        self.info = {}
        self.jsonpath = ""
        self.manifest = None
        if os.path.exists( os.path.dirname(project_dir) ):
            self.jsonpath = os.path.join(os.path.dirname(project_dir), language_code+".json")
            if os.path.isfile(self.jsonpath):
                with io.open(self.jsonpath, 'r') as json_file:
                    self.info = json.load(json_file)
                assert 'language' in self.info
                assert 'source_translations' in self.info
                if not 'said_words' in self.info:
                    self.info['said_words'] = {}
        if not self.info:
            self.info = {'language': {'id': language_code, 'name': ""},
                        'source_translations': [],
                         'said_words': {} }

    def __repr__(self):
        return f'ProjectInfo({self.jsonpath})'

    # Loads the manifest file, if any.
    # Does not report any load errors, but creates a template yaml in that case.
    # Syncs the project info and manifest info.
    def useManifest(self):
        self.manifest = ManifestYaml()
        errors = self.manifest.load(self.project_dir)
        if len(errors) > 0:
            self.manifest.create(self.project_dir, self.getLanguageCode())
        self.sync()

    # Syncs self.info and self.manifest if either is missing any values.
    def sync(self):
        if my := self.manifest:
            # Sync language attributes
            if not my.getLanguageId():
                my.setLanguageId(self.info['language']['id'])
            if not my.getLanguageName() and 'name' in self.info['language']:
                my.setLanguageName(self.info['language']['name'])
            elif not 'name' in self.info['language'] or not self.info['language']['name']:
                self.info['language']['name'] = my.getLanguageName()

            # Sync source translations
            # One-way sync from MY to PI. Different projects in the same langauge
            # may have different sources. It is helpful to combine sources from
            # any of them into PI. Copying sources from PI into individual
            # MY files, however, would not be valid.
            for source in my.getSources():
                if not self.knownSource(source['language'], source['identifier'], source['version']):
                    self.addSource(source['language'], source['identifier'], source['version'])

    # Returns True if the specified language resource exists in project info.
    # The version parameter may be left unspecified, in which case version is not checked.
    def knownSource(self, language_id, resource_id, version=None):
        known = False
        for source in self.getSources():
            if source['language_id'] == language_id and source['resource_id'] == resource_id and\
               (not version or source['version'] == version):
                known = True
                break
        return known

    # Saves the current information in the project json file if savePI is True.
    # Implicitly saves the manifest file also, if it is in use, and saveM is True.
    def save(self, savePI=True, saveM=True):
        if savePI:
            self.info['source_translations'].sort(reverse=True, key=operator.itemgetter('count'))    # sorts in place
            with io.open(self.jsonpath, 'w') as json_file:
                json.dump(self.info, json_file, indent=4)
        if saveM and self.manifest:
            if mainsource := self.getMainSource():
                self.manifest.setVersion(mainsource['version'])
            self.manifest.setDates()
            self.manifest.save()

    def setLanguage(self, name, direction=""):
        self.info['language']['name'] = name
        if my := self.manifest:
            my.setLanguageId(self.info['language']['id'])
            if name:
                my.setLanguageName(name)
            if direction:
                my.setLanguageDirection(direction)  # this function rejects invalid directions

    def getLanguageCode(self):
        return self.info['language']['id']
    def getLanguageName(self):
        return self.info['language']['name'] if 'name' in self.info['language'] else ""

    # Overwrites the list of source translations
    def resetSources(self):
        self.info['source_translations'].clear()
        if self.manifest:
            self.manifest.resetSources()
            self.manifest.setVersion("")
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
        if self.manifest:
            self.manifest.addSource(language_id, resource_id, version)

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
        for source in self.info['source_translations']:
            if source['language_id'] == language_id and source['resource_id'] == resource_id and\
                source['version'] == version:
                found = source
                break
        return found

    def setResourceType(self, id):
        if self.manifest:
            self.manifest.setResourceType(id)

    def addContributors(self, contributors):
        if self.manifest:
            for contributor in contributors:
                if contributor:     # yes, it is possible to have a null contributor
                    self.manifest.addContributor(contributor)

    def addProject(self, project):
        if self.manifest:
            self.manifest.addProject(project)

    # Adds or updates the specified word in ProjectInfo.
    def addWord(self, word, count):
        assert 'said_words' in self.info
        if word not in self.info['said_words'] or self.info['said_words'][word] < count:
            self.info['said_words'][word] = count

    # Returns the list of words with count greater than mincount.
    def getWords(self, mincount=1):
        return [word for word in self.info['said_words'] if self.info['said_words'][word] >= mincount]

class SaidWords:
    def __init__(self, project_dir, language_code):
        self.words = {}
        self.project_dir = project_dir
        self.language_code = language_code

    # For convenience, this function would return the list of words saved in the project info file.
    # Would not change anything in the SaidWords object.
    # I decided not to muddy the waters by implementing this function.
    # def getSavedWords(self, mincount=1):

    # Increments the counter for the specified word.
    def addWord(self, word: str):
        if word in self.words:
            self.words[word] += 1
        else:
            self.words[word] = 1

    def getWords(self, mincount=1):
        return [word for word in self.words if self.words[word] >= mincount]

    # Saves the current information to ProjectInfo, which serializes the
    # top "said" words in the project info file.
    def save(self, mincount=1):
        projectInfo = ProjectInfo(self.project_dir, self.language_code)
        for word in self.words:
            if self.words[word] >= mincount:
                projectInfo.addWord(word, self.words[word])
        projectInfo.save(savePI=True, saveM=False)
