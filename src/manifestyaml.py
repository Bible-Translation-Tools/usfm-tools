# -*- coding: utf-8 -*-
# Manages project-specific information in manifest.yaml file.
# Changes are held in memory until save() is called.
# This class can give access to any yaml file, but the create() and setter functions
#    only work for resource container manifest.yaml files. These files are identified
#    by having a 'dublin_core' element.
# The yaml contents are exposed via the contents member.
# Note: contents a mutable object. Changes made to it affects the contents here.

import os
import io
import yaml
import codecs
import operator

class ManifestYaml:
    # Creates manifest.yaml file if it doesn't already exist, or fails to load.
    # Sets self.contents.
    def __init__(self):
        self.project_dir = ""
        self.contents:dict = {}
        self.path = ""

    def __repr__(self):
        return f'ManifestYaml({self.project_dir})'

    # Loads specified file and sets self.contents.
    # Returns list of error strings if not successful.
    def load(self, project_dir, filename="manifest.yaml"):
        self.path = os.path.join(project_dir, filename)
        errors = []
        if os.path.isfile(self.path):
            if has_bom(self.path):
                errors.append(f"{self.path} file has a Byte Order Mark. Remove it.")
            with io.open(self.path, "tr", encoding='utf-8-sig') as file:
                try:
                    self.contents = yaml.safe_load(file)
                except yaml.scanner.ScannerError as e:
                    errors.append(f"Yaml syntax error at or before line {e.problem_mark.line} in: {self.path}")
                except yaml.parser.ParserError as e:
                    errors.append(f"Yaml parsing error at or before line {e.problem_mark.line} in: {self.path}")
        else:
            errors.append(f"File not found: {self.path}")
        return errors

    # Creates a resource container manifest.yaml file in the specified folder.
    def create(self, project_dir: str):
        self.contents = {'dublin_core': {'conformsto': 'rc0.2', 'contributor': [],
'creator': 'Bible translation community', 'description': 'An unrestricted literal Bible',
'format': 'text/usfm', 'identifier': 'reg', 'issued': '2025-03-31',
'language': {'direction': '', 'identifier': '', 'title': ''}, 'modified': '2025-03-31',
'publisher': 'Wycliffe Associates', 'relation': [], 'rights': 'CC BY-SA 4.0', 'source': [],
'subject': 'Bible', 'title': 'Bible', 'type': 'bundle', 'version': ''},
'checking': {'checking_entity': [], 'checking_level': '1'},
'projects': []}
        self.path = os.path.join(project_dir, "manifest.yaml")
        self.save()

    # Sorts the projects and contributors.
    # [Over]writes the current manifest.yaml file.
    # Does nothing if contents is not initialized.
    def save(self):
        if self.path and self.contents:
            self.contents['projects'].sort(key=operator.itemgetter('sort'))
            self.contents['dublin_core']['contributor'].sort()
            with io.open(self.path, "tw", encoding='utf-8', newline='\n') as file:
                # yaml.safe_dump(self.contents, file, default_flow_style=False, default_style="'")
                yaml.safe_dump(self.contents, file)

    def setLanguage(self, id, name, direction):
        if self.contents and 'dublin_core' in self.contents:
            self.contents['dublin_core']['language']['identifier'] = id
            self.contents['dublin_core']['language']['title'] = name
            self.contents['dublin_core']['language']['direction'] = direction

    # Returns (id, name, direction) tuple
    def getLanguage(self):
        if self.contents and 'dublin_core' in self.contents:
            id = self.contents['dublin_core']['language']['identifier']
            name = self.contents['dublin_core']['language']['title']
            direction = self.contents['dublin_core']['language']['direction']
            language = (id, name, direction)
        else:
            language = None
        return language

    # Returns the language id found in the manifest, or ""
    def getLanguageId(self):
        languageId = ""
        language = self.getLanguage()
        if language:
            languageId = language[0]
        return languageId

    # Returns the text identifier, like "ulb"
    def getResourceId(self):
        if self.contents and 'dublin_core' in self.contents:
            id = self.contents['dublin_core']['identifier']
        else:
            id = ""
        return id

    # Sets the issued and modified dates to the specified value,
    # or to the current date if not specified.
    def setDates(self, date=None):
        if self.contents and 'dublin_core' in self.contents:
            import datetime
            if not date:
                date = datetime.datetime.today().strftime('%Y-%m-%d')
            self.contents['dublin_core']['issued'] = date
            self.contents['dublin_core']['modified'] = date

    def setResourceType(self, rsrc_id):
        if self.contents and 'dublin_core' in self.contents:
            self.contents['dublin_core']['identifier'] = rsrc_id
            self.addRelation(self.contents['dublin_core']['language']['identifier'], rsrc_id)

    # If version is currently empty, sets it to vrsn.
    # Resets version if vrsn is empty.
    def setVersion(self, vrsn):
        if self.contents and 'dublin_core' in self.contents:
            if vrsn == "" or self.contents['dublin_core']['version'] == "":
                self.contents['dublin_core']['version'] = vrsn

    def resetSources(self):
        if self.contents and 'dublin_core' in self.contents:
            self.contents['dublin_core']['source'].clear()
    # Appends source to the source list if it is not already present there.
    # Also sets target resource version if it is not already set.
    def addSource(self, lang, resource, version):
        if self.contents and 'dublin_core' in self.contents:
            src = {'identifier': resource, 'language': lang, 'version': version}
            if not src in self.contents['dublin_core']['source']:
                self.contents['dublin_core']['source'].append(src)

    # Converts contributor to title case and adds it to the list, if unique.
    def addContributor(self, contributor):
        candidate = contributor.title().strip()
        if candidate and not candidate in self.contents['dublin_core']['contributor']:
            self.contents['dublin_core']['contributor'].append(candidate)

    # Appends or replaces the specified project
    def addProject(self, project):
        for i,proj in enumerate(self.contents['projects']):
            if proj['identifier'] == project['identifier']:
                self.contents['projects'].pop(i)
        self.contents['projects'].append(project)

    def addRelation(self, lang, rsrc):
        relation = lang + "/" + rsrc
        rels = self.contents['dublin_core']['relation']
        if not relation in rels:
            self.contents['dublin_core']['relation'].append(relation)

# Returns True if the file has a BOM
def has_bom(path):
    with open(path, 'rb') as f:
        raw = f.read(4)
    for bom in [codecs.BOM_UTF8, codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE, codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE]:
        if raw.startswith(bom):
            return True
    return False
