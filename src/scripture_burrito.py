# Manages Scripture resource metadata in a metadata.json file.
# Changes are held in memory until save() is called.

import hashlib
import os
import io
import json
import scripture_burrito_validator

# def strNow():
#     from datetime import datetime, timezone
#     return datetime.now(timezone.utc).isoformat()

def strToday():
    from datetime import datetime
    return datetime.today().strftime('%Y-%m-%d')

# Returns the size and md5 checksum of a file at the given path.
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
                    is_valid, msg = scripture_burrito_validator.validate(self.contents)
                    if not is_valid:
                        msg = f"Validation error in {path}: {msg}"
                except json.JSONDecodeError as e:
                    line_info = f" at or before line {e.lineno}" if e.lineno else ""
                    msg = f"JSON syntax error{line_info} in: {path}"
        else:
            msg = f"File not found: {path}"
        return is_valid, msg

    # Creates the skeleton of a WA-specific Scripture Burrito in memory.
    # It is not a valid Burrito until copyright, language and one ingredient are added.
    def create(self):
        # self.contents = {"format":"scripture burrito","meta":{"version":"1.0.0","category":"source","defaultLocale":"en","dateCreated":strNow()},"idAuthorities":{"wycliffeassociates":{"id":"https://www.wycliffeassociates.org","name":{"en":"Wycliffe Associates"}}},"identification":{"primary":{"wacs":{"Tech_Advance:":{"revision":"latest","timestamp":strNow()}}},"name":{"en":"Bible"}},"confidential":False,"languages":[{"tag":"xx","name":{"en":"Placeholder"},"scriptDirection":"ltr"}],"type":{"flavorType":{"name":"scripture","flavor":{"name":"textTranslation","projectType":"standard","translationType":"newTranslation","audience":"common","usfmVersion":"3.0"}}},"copyright":{"licenses":[{"ingredient":"LICENSE.md"}]}}
          self.contents = {"format":"scripture burrito","meta":{"version":"1.0.0","category":"source","defaultLocale":"en","dateCreated":strToday()},"idAuthorities":{"wycliffeassociates":{"id":"https://www.wycliffeassociates.org","name":{"en":"Wycliffe Associates"}}},"identification":{"primary":{"wacs":{"owner/repo":{"revision":"latest","timestamp":strToday()}}},"name":{"en":"Bible"},"abbreviation":{"en":"Bible"}},"confidential":False,"type":{"flavorType":{"name":"scripture","flavor":{"name":"textTranslation","projectType":"standard","translationType":"newTranslation","audience":"common","usfmVersion":"3.0"}}},"copyright":{"licenses":[{"ingredient":"LICENSE.md"}]}}

    # Saves the current contents to metadata.json. Overwrites file if it exists.
    # Returns Tuple of (is_valid: bool, message: str)
    def save(self):
        self.updateFileInfo()
        is_valid = True
        msg = ""
        if self.resource_dir and self.contents:
            is_valid, msg = scripture_burrito_validator.validate(self.contents)
            if is_valid:
                path = os.path.join(self.resource_dir, "metadata.json")
                with io.open(path, 'w', newline='\n') as json_file:
                    json.dump(self.contents, json_file, indent=2)
        return (is_valid, msg)

    def setGenerator(self, software, version):
        if software and version:
            self.contents['meta']['generator'] = {"softwareName": software, "softwareVersion": version}

    def setIdentification(self, locale:str, identity:str, abbrev:str, repo:str):
        if locale and identity:
            self.contents['identification']['name'] = {locale: identity}
        if locale and abbrev:
            self.contents['identification']['abbreviation'] = {locale: abbrev}
        if repo:
            primaryrepo = {repo: {"revision": "latest", "timestamp": strToday()}}
            self.contents['identification']['primary']['wacs'] = primaryrepo

    # There may be only one language in a WA burrito, but the name may vary by locale.
    def setLanguage(self, language_code, locale, name, direction):
        if not "languages" in self.contents:
            self.contents["languages"] = []
            self.contents["languages"].append({"tag": language_code, "name": {locale: name}, "scriptDirection": direction})
        else:
            language = self.contents["languages"][0]
            if language["tag"] != language_code:      # different language
                self.contents["languages"][0] = {"tag": language_code, "name": {locale: name}, "scriptDirection": direction}
            elif not locale in language["name"]:
                language["name"][locale] = name
            if language["scriptDirection"] != direction:
                language["scriptDirection"] = direction

    def addName(self, bookId, locale, shortname, longname="", abbr=""):
        if not "localizedNames" in self.contents:
            self.contents["localizedNames"] = {}
        localized_names = self.contents["localizedNames"]
        bookId = bookId.upper()
        localized_names[bookId] = {"short": {locale: shortname}}
        if longname:
            localized_names[bookId]["long"] = {locale: longname}
        if abbr:
            localized_names[bookId]["abbr"] = {locale: abbr}

    def addProject(self, bookId, path):
        if "ingredients" not in self.contents:  # create() doesn't create this section
            self.contents["ingredients"] = {}
        filename = os.path.basename(path)
        size, checksum = size_and_checksum(path)
        md5 = {"md5": checksum}
        bookId = bookId.upper()
        self.contents["ingredients"][filename] = {"checksum": md5, "mimeType": "text/x-usfm", "size": size, "scope":{bookId: []}}

        if "currentScope" not in self.contents['type']['flavorType']:
            self.contents['type']['flavorType']["currentScope"] = {}
        self.contents['type']['flavorType']["currentScope"][bookId] = []

    # Recalculates size and checksum for each ingredient.
    def updateFileInfo(self):
        if "ingredients" in self.contents:
            for filename in self.contents["ingredients"]:
                path = os.path.join(self.resource_dir, filename)
                if os.path.isfile(path):
                    size, checksum = size_and_checksum(path)
                    md5 = {"md5": checksum}
                    self.contents["ingredients"][filename]["checksum"] = md5
                    self.contents["ingredients"][filename]["size"] = size
