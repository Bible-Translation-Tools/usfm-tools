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
from yaml.scanner import ScannerError
from yaml.parser import ParserError
from usfm_verses import verseCounts

class ManifestYaml:
    def __init__(self):
        self.project_dir = ""
        self.contents:dict = {}
        self.path = ""
        self.last_load_time = None  # Track last file modification time at load

    def __repr__(self):
        return f'ManifestYaml({self.project_dir})'

    # Loads specified file into self.contents, if not already loaded.
    # Returns list of error strings if not successful.
    def load(self, project_dir, filename="manifest.yaml"):
        path = os.path.join(project_dir, filename)
        errors = []
        reload_needed = False
        if path == self.path:
            # Check if file has been modified since last load or save
            if os.path.isfile(path):
                mtime = os.path.getmtime(path)
                if self.last_load_time is None or mtime > self.last_load_time:
                    reload_needed = True
            else:
                errors.append(f"File not found: {path}")
                return errors
        else:
            reload_needed = True
        if reload_needed:
            if os.path.isfile(path):
                self.path = path
                if has_bom(self.path):
                    errors.append(f"{self.path} file has a Byte Order Mark. Remove it.")
                with io.open(self.path, "tr", encoding='utf-8-sig') as file:
                    try:
                        self.contents = yaml.safe_load(file)
                    except ScannerError as e:
                        line_info = ''
                        if hasattr(e, 'problem_mark') and e.problem_mark is not None and hasattr(e.problem_mark, 'line'):
                            line_info = f" at or before line {e.problem_mark.line}"
                        errors.append(f"Yaml syntax error{line_info} in: {self.path}")
                    except ParserError as e:
                        line_info = ''
                        if hasattr(e, 'problem_mark') and e.problem_mark is not None and hasattr(e.problem_mark, 'line'):
                            line_info = f" at or before line {e.problem_mark.line}"
                        errors.append(f"Yaml parsing error{line_info} in: {self.path}")
                # Update last load time
                self.last_load_time = os.path.getmtime(self.path)
            else:
                errors.append(f"File not found: {path}")
        return errors

    # Creates a resource container manifest.yaml file in the specified folder.
    def create(self, project_dir: str, langcode):
        if os.path.isdir(project_dir):
            self.contents = {'dublin_core': {'conformsto': 'rc0.2', 'contributor': [],
    'creator': 'Bible translation community', 'description': 'An unrestricted literal Bible',
    'format': 'text/usfm', 'identifier': 'reg', 'issued': '2025-06-11',
    'language': {'direction': '', 'identifier': langcode, 'title': ''}, 'modified': '2025-06-11',
    'publisher': 'Wycliffe Associates', 'relation': [], 'rights': 'CC BY-SA 4.0', 'source': [],
    'subject': 'Bible', 'title': 'Bible', 'type': 'bundle', 'version': ''},
    'checking': {'checking_entity': [], 'checking_level': '1'},
    'projects': []}
            self.setDates()
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
                yaml.safe_dump(self.contents, stream=file, allow_unicode=True, sort_keys=False)
            self.last_load_time = os.path.getmtime(self.path)

    # Returns the full path of the current manifest file.
    def getPath(self):
        return self.path

    def setLanguageId(self, id):
        if id:
            self._setLanguageAttribute('identifier', id)
    def setLanguageName(self, name):
        if name:
            self._setLanguageAttribute('title', name)
    def setLanguageDirection(self, direction):
        if direction in ('ltr', 'rtl'):
            self._setLanguageAttribute('direction', direction)
    def _setLanguageAttribute(self, attr, value):
        try:
            self.contents['dublin_core']['language'][attr] = value
        except:
            pass

    def getLanguageId(self):
        return self.getLanguageAttribute('identifier')
    def getLanguageName(self):
        return self.getLanguageAttribute('title')
    def getLanguageDirection(self):
        return self.getLanguageAttribute('direction')
    def getLanguageAttribute(self, attr):
        try:
            value = self.contents['dublin_core']['language'][attr]
            if value is None:
                value = ""
        except KeyError as e:
            value = ''
        return value

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

    def getVersion(self):
        try:
            version = self.contents['dublin_core']['version']
        except KeyError as e:
            version = ""
        return version

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

    def getSources(self):
        try:
            srclist = self.contents['dublin_core']['source']
        except KeyError as e:
            srclist = []
        return srclist

    # Converts contributor to title case and adds it to the list, if unique.
    def addContributor(self, contributor: str):
        candidate = contributor.title().strip()
        if candidate and not candidate in self.contents['dublin_core']['contributor']:
            self.contents['dublin_core']['contributor'].append(candidate)

    # Appends or replaces the specified project
    def addProject(self, bookTitle, bookId, path):
        project = { "title": bookTitle, "identifier": bookId.lower(), "path": path}
        if bookId.upper() in verseCounts:
            category = 'bible-nt'
            sort = verseCounts[bookId.upper()]['sort']
            if sort < 40:
                category = 'bible-ot'
            elif sort > 66:
                category = "periph"
            project["sort"] = sort
            project["categories"] = [category]
        else:
            project["sort"] = 0
            project["categories"] = ["periph"]
        project["versification"] = "ufw"

        for i,proj in enumerate(self.contents['projects']):
            if proj['identifier'] == bookId.lower():
                self.contents['projects'].pop(i)
        self.contents['projects'].append(project)

    # For unit test purposes only
    def getProjects(self):
        return self.contents.get('projects', [])

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
