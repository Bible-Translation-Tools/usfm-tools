# -*- coding: utf-8 -*-
# Parses a USFM source text and store information about it for easy, efficient retrieval.
# Provides a centralized, indexed, read-only representation of Scripture text.
# Each ScriptureBook object represents a single book. The object will be read-only.

import os
import usfmReader
import io
import re
import usfm_utils
import sentences

class ScriptureBook:
    def __init__(self, usfmpath):
        self.usfmpath = usfmpath
        self.ID = ""
        self.booklength = 0
        self.nchunks = 0
        self.errors = []
        self.chapter = self.verse = self.bridge = 0
        self.paragraphs_model = {}
        self.sections_model = {}
        self.sections_model_real = {}   # sections other than \s5
        self.endPunctuation = ''
        self.unicodeBlock = ''
        self.text = {}    # verse-reference: verse-text
        self.footnote = {}    # verse-reference: footnote(s)
        self.nverses = {}  # chapter-reference: number of verses
        self._scanText()

    def __repr__(self):
        return f'ScriptureBook({self.usfmpath})'

    def getErrors(self):
        return self.errors
    def getBookId(self):
        return self.ID
    def getBookLength(self):
        return self.booklength
    def getChunkCount(self):
        return self.nchunks
    def getVerseCount(self, chapter):
        return self.nverses[chapter] if chapter in self.nverses else 0
    def getText(self, chapter, verse ):
        ref = f"{chapter}:{verse}"
        return self.text[ref] if ref in self.text else ""
    def getVerseLength(self, chapter, verse):
        ref = f"{chapter}:{verse}"
        return len(self.text[ref]) if ref in self.text else 0
    def getFootnote(self, chapter, verse ):
        ref = f"{chapter}:{verse}"
        return self.footnote[ref] if ref in self.footnote else ""
    def getPmark(self, chapter, verse ):
        # returns the ending punctuation and paragraph mark before the specified verse.
        # Does not return paragraph marks within verses, only between verses.
        pmark = punct = ""
        ref = f"{chapter}:{verse}"
        if ref in self.paragraphs_model:
            pmark = self.paragraphs_model[ref]['mark']
            punct = self.paragraphs_model[ref]['endPunc']
        return (pmark, punct)
    def getSmark(self, chapter, verse ):
        # returns the ending punctuation and section mark following the specified verse.
        smark = punct = ""
        ref = f"{chapter}:{verse}"
        if ref in self.sections_model:
            smark = self.sections_model[ref]['mark']
            punct = self.sections_model[ref]['endPunc']
        return (smark, punct)
    # Returns a count of sections **other than \s5 sections**
    def countRealSections(self):
        return len(self.sections_model_real)
    # Returns True if a section is marked at the specified verse in the source text.
    def has_section(self, chapter, verse):
        ref = f"{chapter}:{verse}"
        if ref in self.sections_model:
            has_section = (self.sections_model[ref]['mark'] in {'s','s1','s2','s3','s4'})
        else:
            has_section = False
        return has_section

    # Parses the self.usfmpath USFM file.
    def _scanText(self):
        self.errors = usfm_utils.usfm_errors(self.usfmpath)
        if not self.errors:
            with io.open(self.usfmpath, "tr", 1, encoding="utf-8-sig") as input:
                contents = input.read(-1)
                if "lemma=" in contents or "x-occurrences" in contents:
                    contents = usfm_utils.unalign_usfm(contents)
                self.booklength = len(contents)
                tokens = usfmReader.parseString(contents)
                for token in tokens:
                    self._take(token)

    # Analyzes the specified token in the model file.
    # Only cares about locations of paragraphs.
    def _take(self, token):
        if token.type == 'c':
            self._takeC(token.value)
        elif token.type == 'v':
            self._takeV(token.value)
        elif token.type == 'text':
            self._takeText(token.value)
        elif token.isParagraph() or token.isPoetry() or token.type in {'d','sp'}:
            self._takePQ(token.type)
        elif token.isSection():
            self._takeS(token.type)
        elif token.isFootnoteInterior():
            self._takeFootnote(token.value)
        elif token.type== 'id':
            self.ID = token.value[0:3].upper()
            self.chapter = 0
            self.verse = 0
            self.bridge = 0
            # self.expectText = False
            # self.midSentence = False

# Sets the chapter number.
# If there is still a tentative paragraph mark, remove it.
    def _takeC(self, c):
        lastref = f"{self.chapter}:{self.verse+1}"
        if lastref in self.paragraphs_model:
            del self.paragraphs_model[lastref]
        if c.isnumeric():
            self.chapter = int(c)
            self.verse = 0
            self.bridge = 0
            self.nverses[self.chapter] = 1

    def _takeFootnote(self, text):
        ref = f"{self.chapter}:{self.verse}"
        if text and ref in self.footnote:
            self.footnote[ref] += text
        else:
            self.footnote[ref] = text

    # Save the paragraph mark and its location (attach to next verse).
    def _takePQ(self, type):
        ref = f"{self.chapter}:{self.verse+1}"
        p = {}
        p['mark'] = type
        p['endPunc'] = self.endPunctuation
        self.paragraphs_model[ref] = p

    # Save the section mark and its location.
    # Unlike paragraph marks, sections marks take the previous verse number as their location.
    def _takeS(self, type):
        section = {}
        section['mark'] = type
        section['endPunc'] = self.endPunctuation
        ref = f"{self.chapter}:{self.verse}"
        if not ref in self.sections_model:      # save only the first section mark per verse
            self.sections_model[ref] = section
            if type != 's5':
                self.sections_model_real[ref] = section
        if type == 's5':
            self.nchunks += 1

    # Records the text of the current verse.
    # Deletes any section or paragraph mark associated with the next verse
    # because it apparently occurred in the middle of the current verse.
    def _takeText(self, text):
        ref = f"{self.chapter}:{self.verse}"
        if ref in self.text:
            self.text[ref] += " " + text
        else:
            self.text[ref] = text
        self.endPunctuation = sentences.endsSentence(text) # endPunctuation is a temporary holding place
        if not self.unicodeBlock and self.verse > 0 and len(text) > 10:
            self.unicodeBlock = usfm_utils.unicodeBlock(text)

        # Forget section and paragraph marks in the middle of a verse.
        if ref in self.sections_model:
            del self.sections_model[ref]
        if ref in self.sections_model_real:
            del self.sections_model_real[ref]
        nextref = f"{self.chapter}:{self.verse+1}"
        if nextref in self.paragraphs_model:
            del self.paragraphs_model[nextref]


    # v is the verse number or range
    # Assign the verse number to the preceding paragraph mark, if any.
    # Unlike sections, paragraphs take the location of the following verse.
    def _takeV(self, v):
        v1 = v.split('-')[0]
        v2 = v.split('-')[-1]
        if v1.isnumeric() and v2.isnumeric():
            self.verse = int(v1)
            self.bridge = int(v2)
            self.nverses[self.chapter] = int(v2)
