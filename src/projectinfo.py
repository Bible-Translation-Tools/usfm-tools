# -*- coding: utf-8 -*-
# Manages project-specific information, including language-specific information.
# New project data is held in memory until save() is called.
# ProjectInfo is a composite class, using LanguageInfo, ManifestYaml, and Burrito.
# The SaidWords class is also implemented in this module, since it also uses LanguageInfo.

from manifestyaml import ManifestYaml
from languageinfo import LanguageInfo
from scripture_burrito import Burrito

import os

class ProjectInfo:
    instances = 0

    def __init__(self, project_dir, language_code):
        self.project_dir = project_dir
        self.languageInfo = LanguageInfo(project_dir, language_code)
        self.burrito = Burrito(project_dir)
        ProjectInfo.instances += 1
        is_valid, _ = self.burrito.load()
        if not is_valid:
            self.burrito.create()
        self.manifest = None

    def __repr__(self):
        return f'ProjectInfo(f"{self.project_dir}, {self.getLanguageCode()}")'

    # Creates manifest if it is missing or invalid, and docreate is True.
    # Loads the manifest file, if any.
    # Syncs the project info and manifest info, if any.
    def useManifest(self, docreate):
        if os.path.isdir(self.project_dir):
            if not self.manifest:
                if docreate:
                    self._makeManifest()     # makes and loads manifest
            else:
                self.manifest.load(self.project_dir)
            if self.manifest and self.manifest.getLanguageId() != self.getLanguageCode():
                self.manifest = None
            if self.manifest:
                self.sync()

    def disuseManifest(self):
        self.manifest = None

    # Creates manifest file if it does not exist.
    # Overwrites manifest if it exists and is corrupted.
    # Does not overwrite a syntactically valid manifest.
    def _makeManifest(self):
        if os.path.isdir(self.project_dir) and not self.manifest:
            self.manifest = ManifestYaml()
            errors = self.manifest.load(self.project_dir)
            if errors:
                if yamlpath := self.manifest.getPath():
                    timestamp = get_timestamp(yamlpath)
                    bakpath = os.path.join(os.path.dirname(yamlpath), f"manifest-{timestamp}.yaml")
                    if not os.path.exists(bakpath):
                        os.rename(yamlpath, bakpath)
                self.manifest.create(self.project_dir, self.getLanguageCode())

    # Syncs self.info and self.manifest if either is missing any values.
    def sync(self):
        if my := self.manifest:
            # Sync language attributes
            if not my.getLanguageId():
                my.setLanguageId(self.languageInfo.getLanguageCode())

            language_name = self.languageInfo.getLanguageName()
            if not language_name:
                self.languageInfo.setLanguageName(my.getLanguageName())
            elif not my.getLanguageName():
                my.setLanguageName(language_name)

            # Sync source translations
            # One-way sync from MY to LI. Different projects in the same langauge
            # may have different sources. It is helpful to combine sources from
            # any of them into LI. Copying sources from LI into individual
            # manifest.yaml files, however, would not be valid.
            for mysource in my.getSources():
                if not self.languageInfo.findSource(mysource['language'], mysource['identifier'], mysource['version']):
                    self.languageInfo.addSource(mysource['language'], mysource['identifier'], mysource['version'])

        self.burrito.setLanguage(self.languageInfo.getLanguageCode(),
                                  locale='en', name=self.languageInfo.getLanguageName(),
                                  direction=self.languageInfo.getLanguageDirection())

    # Returns True if the specified language resource exists in project info.
    def knownSource(self, language_id, resource_id, version):
        return self.languageInfo.findSource(language_id, resource_id, version) is not None

    # Saves the current information in the project json file, burrito metadata file,
    # and manifest.yaml, if it is in use.
    def save(self):
        self.languageInfo.save()
        is_valid1, msg1 = self.burrito.save()
        is_valid2 = True
        msg2 = ""
        if self.manifest:
            # Utilize this opportunity to set version if missing
            if self.manifest.getVersion() == "":
                if mainsource := self.getMainSource():
                    self.manifest.setVersion(mainsource['version'] + ".1")
            is_valid2, msg2 = self.manifest.save()
        return (is_valid1 and is_valid2), ("Burrito: " + msg1 if msg1 else "Manifest: " + msg2)

    # Sets the generator information in LanguageInfo and burrito metadata.
    def setGenerator(self, name, version):
        self.burrito.setGenerator(name, version)
        self.languageInfo.setGenerator(version)
    def get_LI_Generator(self):
        return self.languageInfo.getGenerator()

    def setLanguage(self, name, locale='en', direction=""):
        if locale == 'en':
            self.languageInfo.setLanguageName(name)
        self.languageInfo.setLanguageDirection(direction)
        self.burrito.setLanguage(self.getLanguageCode(), locale=locale, name=name, direction=direction)
        if my := self.manifest:
            my.setLanguageId(self.getLanguageCode())
            if name:
                my.setLanguageName(name)
            if direction:
                my.setLanguageDirection(direction)  # this function rejects invalid directions

    def getLanguageCode(self):
        return self.languageInfo.getLanguageCode()
    def getLanguageName(self, locale='en'):
        name = self.burrito.getLanguageName(locale)
        if not name and locale == 'en':
            name = self.languageInfo.getLanguageName()
        return name

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
        mainsrc = self.languageInfo.getMainSource()
        if not mainsrc and self.manifest:
            self.sync()
            if sources := self.manifest.getSources():
                mainsrc = sources[0]
        return mainsrc

    def setSourceDir(self, source_dir):
        self.languageInfo.setSourceDir(source_dir)
    def getSourceDir(self) -> str:
        return self.languageInfo.getSourceDir()
    def setStandardChapterTitle(self, title):
        self.languageInfo.addChapterTitle(title)
    def getStandardChapterTitle(self):
        return self.languageInfo.getChapterTitle()

    def setResourceType(self, id):
        if self.manifest:
            self.manifest.setResourceType(id)

    def addContributors(self, contributors):
        if self.manifest:
            for contributor in contributors:
                if contributor:     # yes, it is possible to have a null contributor
                    self.manifest.addContributor(contributor)

    # Adds or replaces the project information in the manifest.
    def addProject(self, bookTitle, bookId, path):
        if self.manifest:
            relpath = "./" + os.path.basename(path)
            self.manifest.addProject(bookTitle, bookId, relpath)
        self.burrito.addProject(bookId, path)
        self.burrito.addName(bookId, self.getLanguageCode(), bookTitle)

    def addLicense(self, filename, rights):
        if self.manifest:
            self.manifest.setLicense(rights)
        self.burrito.addLicense(filename)

    def setIdentification(self, owner, name):
        identity = self.languageInfo.getLanguageName() + " Bible"
        self.burrito.setIdentification(locale='en', identity=identity, abbrev="Bible", repo=f"{owner}/{name}")

    def clearWords(self):
        self.languageInfo.clearWords()

    # Adds or updates the specified word in LanguageInfo.
    def addWord(self, word, count):
        self.languageInfo.addWord(word, count)

    # Returns the list of words with count >= mincount.
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

    def _clearWords(self):
        self.words = dict()

    # Saves the top "said" words to LanguageInfo, which serializes
    # them in the language info file.
    # To be saved, at least 12% of the occurrences of the word must have been in a "said" context,
    # and it must not be capitalized.
    def save(self, wordlist, mincount=4):
        li = LanguageInfo(self.project_dir, self.language_code)
        for word in self.words:
            saidcount = self.words[word]
            if saidcount >= mincount:
                allcount = wordlist[word][0] if word in wordlist else 9999
                if saidcount / allcount >= 0.12:
                    li.addWord(word, saidcount)
        if not self.words and mincount >= 1000:
            li.clearWords()
        li.save()

# Returns the modified date/time of the specified file, formatted as a string.
def get_timestamp(path):
    from datetime import datetime
    mtime = os.path.getmtime(path)
    dt = datetime.fromtimestamp(mtime)
    s = dt.strftime("%Y%m%d%H%M")
    return s[2:]
