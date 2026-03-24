# Manages Scripture resource metadata in a metadata.json file.
# Changes are held in memory until save() is called.

import os
import io
import json
import scripture_burrito_validator

def strNow():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()

def size_and_checksum(path):
    import hashlib
    size = 0
    hash_md5 = hashlib.md5()
    with open(path, 'rb') as f:  # Open in binary read mode
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
            size += len(chunk)
    md5_hash = hash_md5.hexdigest()
    return size, md5_hash

class Burrito:
    def __init__(self, resource_dir):
        self.resource_dir = resource_dir
        self.contents:dict = {}

    def __repr__(self):
        return f'Burrito({self.resource_dir})'

    # Loads specified file into self.contents, overwriting current contents.
    # Returns tuple of (is_valid: bool, message: str).
    def load(self):
        is_valid = False
        path = os.path.join(self.resource_dir, "metadata.json")
        if os.path.isfile(path):
            with open(path, "r", encoding='utf-8') as file:
                try:
                    self.contents = json.load(file)
                    is_valid, msg = scripture_burrito_validator.validate_burrito(self.contents)
                    if not is_valid:
                        msg = f"Validation error in {path}: {msg}"
                except json.JSONDecodeError as e:
                    line_info = f" at or before line {e.lineno}" if e.lineno else ""
                    msg = f"JSON syntax error{line_info} in: {path}"
        else:
            msg = f"File not found: {path}"
        return is_valid, msg

    # Creates the skeleton of a WA-specific Scripture Burrito in memory.
    # It is not a valid Burrito until an ingredient is added.
    def create(self):
        # self.contents = {"format":"scripture burrito","meta":{"version":"1.0.0","category":"source","defaultLocale":"en","dateCreated":strNow()},"idAuthorities":{"wycliffeassociates":{"id":"https://www.wycliffeassociates.org","name":{"en":"Wycliffe Associates"}}},"identification":{"primary":{"wacs":{"Tech_Advance:":{"revision":"latest","timestamp":strNow()}}},"name":{"en":"Bible"}},"confidential":False,"languages":[{"tag":"xx","name":{"en":"Placeholder"},"scriptDirection":"ltr"}],"type":{"flavorType":{"name":"scripture","flavor":{"name":"textTranslation","projectType":"standard","translationType":"newTranslation","audience":"common","usfmVersion":"3.0"}}},"copyright":{"licenses":[{"ingredient":"LICENSE.md"}]}}
        self.contents = {"format":"scripture burrito","meta":{"version":"1.0.0","category":"source","defaultLocale":"en","dateCreated":strNow()},"idAuthorities":{"wycliffeassociates":{"id":"https://www.wycliffeassociates.org","name":{"en":"Wycliffe Associates"}}},"identification":{"primary":{"wacs":{"Tech_Advance:":{"revision":"latest","timestamp":strNow()}}},"name":{"en":"Bible"}},"confidential":False,"type":{"flavorType":{"name":"scripture","flavor":{"name":"textTranslation","projectType":"standard","translationType":"newTranslation","audience":"common","usfmVersion":"3.0"}}},"copyright":{"licenses":[{"ingredient":"LICENSE.md"}]}}

    # Saves the current contents to metadata.json. Overwrites file if it exists.
    # Returns Tuple of (is_valid: bool, message: str)
    def save(self):
        is_valid = True
        msg = ""
        if self.resource_dir and self.contents:
            is_valid, msg = scripture_burrito_validator.validate_burrito(self.contents)
            if is_valid:
                path = os.path.join(self.resource_dir, "metadata.json")
                with io.open(path, 'w', newline='\n') as json_file:
                    json.dump(self.contents, json_file, indent=2)
        return (is_valid, msg)

    def setGenerator(self, name, version):
        if name and version:
            self.contents['meta']['generator'] = {"softwareName": name, "softwareVersion": version}

    def setIdentification(self, repo, rev="latest"):
        if repo:
            primaryrepo = {repo: {"revision": rev, "timestamp": strNow()}}
            self.contents['identification']['primary']['wacs'] = primaryrepo

    # Per WA rules, there should only be one language, but this allows for adding more if needed.
    def setLanguage(self, tag, locale, name, direction):
        section = "languages"
        if not section in self.contents:
            self.contents[section] = []
        for language in self.contents["languages"]:
            if language["tag"] == tag:
                language["name"][locale] = name
                language["scriptDirection"] = direction
                return
        self.contents["languages"].append({"tag": tag, "name": {locale: name}, "scriptDirection": direction})

    def addName(self, bookId, locale, shortname, longname="", abbr=""):
        section = "localizedNames"
        if not section in self.contents:
            self.contents[section] = {}
        localized_names = self.contents[section]
        localized_names[bookId] = {"short": {locale: shortname}}
        if longname:
            localized_names[bookId]["long"] = {locale: longname}
        if abbr:
            localized_names[bookId]["abbr"] = {locale: abbr}

    def addProject(self, bookId, path):
        section = "ingredients"
        if section not in self.contents:  # create() doesn't create this section
            self.contents[section] = {}
        filename = os.path.basename(path)
        size, checksum = size_and_checksum(path)
        md5 = {"md5": checksum}
        bookId = bookId.upper()
        self.contents[section][filename] = {"checksum": md5, "mimeType": "text/x-usfm", "size": size, "scope":{bookId: []}}

        section = "currentScope"
        if section not in self.contents['type']['flavorType']:
            self.contents['type']['flavorType'][section] = {}
        self.contents['type']['flavorType'][section][bookId] = []
