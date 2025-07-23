# -*- coding: utf-8 -*-
# Manages project-specific information, including language-specific information.
# Changes to the project info are held in memory until save() is called.
# ProjectInfo is a composite class, using LanguageInfo and ManifestYaml.
# The SaidWords class is also implemented in this module, since it also uses LanguageInfo.

from manifestyaml import ManifestYaml
from languageinfo import LanguageInfo

class ProjectInfo:
    def __init__(self, project_dir, language_code):
        self.project_dir = project_dir
        self.languageInfo = LanguageInfo(project_dir, language_code)
        self.manifest = None

    def __repr__(self):
        return f'ProjectInfo(f"{self.project_dir}, {self.getLanguageCode()}")'

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
                my.setLanguageId(self.getLanguageCode())
            language_name = self.languageInfo.getLanguageName()
            if not my.getLanguageName() and language_name:
                my.setLanguageName(language_name)
            elif not language_name:
                self.languageInfo.setLanguageName(my.getLanguageName())

            # Sync source translations
            # One-way sync from MY to LI. Different projects in the same langauge
            # may have different sources. It is helpful to combine sources from
            # any of them into LI. Copying sources from LI into individual
            # manifest.yaml files, however, would not be valid.
            for mysource in my.getSources():
                if not self.languageInfo.knownSource(mysource['language'], mysource['identifier'], mysource['version']):
                    self.languageInfo.addSource(mysource['language'], mysource['identifier'], mysource['version'])

    # Returns True if the specified language resource exists in project info.
    # The version parameter may be left unspecified, in which case version is not checked.
    def knownSource(self, language_id, resource_id, version=None):
        return self.languageInfo.knownSource(language_id, resource_id, version)

    # Saves the current information in the project json file.
    # Also saves the manifest info in the manifest.yaml, if it is in use.
    def save(self):
        self.languageInfo.save()
        if self.manifest:
            if mainsource := self.getMainSource():
                self.manifest.setVersion(mainsource['version'] + ".1")
            self.manifest.setDates()
            self.manifest.save()

    def setLanguage(self, name, direction=""):
        self.languageInfo.setLanguageName(name)
        if my := self.manifest:
            assert my is self.
            my.setLanguageId(self.getLanguageCode())
            if name:
                my.setLanguageName(name)
            if direction:
                my.setLanguageDirection(direction)  # this function rejects invalid directions

    def getLanguageCode(self):
        return self.languageInfo.getLanguageCode()
    def getLanguageName(self):
        return self.languageInfo.getLanguageName()

    # Overwrites the list of source translations
    def resetSources(self):
        self.languageInfo.resetSources()
        if self.manifest:
            self.manifest.resetSources()
            self.manifest.setVersion("")
    def addSource(self, language_id, resource_id, version):
        self.languageInfo.addSource(language_id, resource_id, version)
        if self.manifest:
            self.manifest.addSource(language_id, resource_id, version)

    def getSources(self):
        return self.languageInfo.getSources()
    def getMainSource(self):
        return self.languageInfo.getMainSource()

    def setSourceDir(self, source_dir):
        self.languageInfo.setSourceDir(source_dir)
    def getSourceDir(self):
        return self.languageInfo.getSourceDir()

    def setResourceType(self, id):
        if self.manifest:
            self.manifest.setResourceType(id)

    def addContributors(self, contributors):
        if self.manifest:
            for contributor in contributors:
                if contributor:     # yes, it is possible to have a null contributor
                    self.manifest.addContributor(contributor)

    # Adds or replaces the project information in the manifest.
    def addProject(self, project):
        if self.manifest:
            self.manifest.addProject(project)

    # Adds or updates the specified word in ProjectInfo.
    def addWord(self, word, count):
        self.languageInfo.addWord(word, count)

    # Returns the list of words with count greater than mincount.
    def getWords(self, mincount=1):
        return self.languageInfo.getWords(mincount)

class SaidWords:
    def __init__(self, project_dir, language_code):
        self.words = {}
        self.project_dir = project_dir
        self.language_code = language_code

    # For convenience, this function would return the list of words saved in the language info file.
    # Would not change anything in the SaidWords object.
    # This function is not needed so far.
    # def getSavedWords(self, mincount=1):

    # Increments the counter for the specified word.
    def addWord(self, word: str):
        if word in self.words:
            self.words[word] += 1
        else:
            self.words[word] = 1

    def getWords(self, mincount=1):
        return [word for word in self.words if self.words[word] >= mincount]

    # Saves the current information to LanguageInfo, which serializes the
    # top "said" words in the language info file.
    def save(self, mincount=1):
        li = LanguageInfo(self.project_dir, self.language_code)
        for word in self.words:
            if self.words[word] >= mincount:
                li.addWord(word, self.words[word])
        li.save()
