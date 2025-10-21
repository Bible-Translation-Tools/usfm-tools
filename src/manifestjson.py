# -*- coding: utf-8 -*-
# Provides read-only access to information in manifest.json file.
# The file contents are exposed via the contents member.
# Note: contents is a mutable object. Changes made to it affects the contents here.

import os
import io
import json

class ManifestJson:
    def __init__(self):
        self.project_dir = ""
        self.contents:dict = {}
        self.path = ""

    def __repr__(self):
        return f'ManifestJson({self.path})'

    # Loads specified file into self.contents, if not already loaded.
    # Returns list of error strings if not successful.
    def load(self, project_dir, filename="manifest.json"):
        path = os.path.join(project_dir, filename)
        errors = []
        if path != self.path:
            if os.path.isfile(path):
                self.path = path
                with io.open(self.path, "tr", encoding='utf-8-sig') as file:
                    try:
                        self.contents = json.load(file)
                    except ValueError as e:
                        errors.append(f"JSON file fails to load: {self.path}")
            else:
                errors.append(f"File not found: {path}")
        return errors

    # Returns the full path of the current manifest file.
    def getPath(self):
        return self.path

    def getLanguageId(self):
        return self._getstring('target_language', 'id')
    def getLanguageName(self):
        return self._getstring('target_language', 'name')
    def getLanguageDirection(self):
        return self._getstring('target_language', 'direction')

    def getBookId(self):
        return self._getstring('project', 'id')

    # Returns the text identifier, like "ulb"
    def getResourceId(self):
        return self._getstring('resource', 'id')

    def getTranslators(self):
        return self._getlist('translators')

    def getSources(self):
        return self._getlist('source_translations')

    def _getstring(self, key1, key2):
        try:
            value = self.contents[key1][key2]
            if value is None:
                value = ""
        except KeyError as e:
            value = ''
        return value

    def _getlist(self, key):
        try:
            value = self.contents[key]
            if value is None:
                value = []
        except KeyError as e:
            value = []
        return value
