# -*- coding: utf-8 -*-
# Implements usfmWriter object to write usfm file with proper spacing.
# By default, all usfm tags except footnotes start on a new line.
# The caller can modify placement of line breaks:
#    by calling setInlineTags() to specify a different set of usfm tags that should not start on a new line
#    by including line breaks in arguments to writeStr()
#    by calling newline() to insert extra line breaks

import io

class usfmWriter:
    def __init__(self, path):
        self._path = path
        self._file = io.open(path, "tw", encoding='utf-8', newline='\n')
        self._spaced = True
        self._newlined = True
        self._inline_tags = {"f", "ft", "f*", "rq", "rq*", "fe", "fe*", "fr", "fk", "fq", "fqa", "fqa*"}

    def close(self):
        if self._file:
            if not self._newlined:
                self._file.write("\n")
            self._file.close()
            self._file = None

    # Specify a set of usfm tags that do not have to start on a new line
    # See __init__() for the defaults.
    def setInlineTags(self, tags):
        self._inline_tags = tags

    # Writes specified string to the usfm file, inserting spaces where needed.
    # Technical debt: the beginning of the string should be checked for inline tags. Currently
    # this function places all leading usfm markers on a new line.
    def writeStr(self, s):
        if s:
            if not self._newlined and s[0] == '\\':
                s = "\n" + s
            elif not self._spaced and s[0] not in '.?!;:,)’”»›\n ':
                s = " " + s
            self._file.write(s)
            self._spaced = (s[-1] == ' ')
            self._newlined = (s[-1] == '\n')

    # Writes a usfm tagged value, insert newline if needed
    def writeUsfm(self, key, value=None):
        if key in self._inline_tags:
            intro = "\\" if (self._newlined or self._spaced) else " \\"
        else:
            intro = "\\" if self._newlined else "\n\\"
        self._file.write(f"{intro}{key}")
        self._spaced = False
        self._newlined = False
        if value:
            self.writeStr(value)

    # Inserts the specified number of line breaks (defualt 1) into the file.
    def newline(self, n=1):
        for i in range(n):
            self._file.write("\n")
        self._spaced = True
        self._newlined = True
