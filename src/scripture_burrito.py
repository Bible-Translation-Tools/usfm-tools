# Manages Scripture resource metadata in a metadata.json file.
# Changes are held in memory until save() is called.

import os
import io
import json
import scripture_burrito_validator

class Burrito:
    def __init__(self, resource_dir):
        self.resource_dir = resource_dir
        self.contents:dict = {}

    def __repr__(self):
        return f'Burrito({self.resource_dir})'

    # Loads specified file into self.contents, overwriting current contents.
    # Returns list of error strings if not successful.
    def load(self):
        path = os.path.join(self.resource_dir, "metadata.json")
        errors = []
        if os.path.isfile(path):
            with open(path, "r", encoding='utf-8') as file:
                try:
                    self.contents = json.load(file)
                    is_valid, msg = scripture_burrito_validator.validate_burrito(self.contents)
                    if not is_valid:
                        errors.append(f"Validation error in {path}: {msg}")
                except json.JSONDecodeError as e:
                    line_info = f" at or before line {e.lineno}" if e.lineno else ""
                    errors.append(f"JSON syntax error{line_info} in: {path}")
        else:
            errors.append(f"File not found: {path}")
        return errors

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
