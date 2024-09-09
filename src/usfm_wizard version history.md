# UsfmWizard Version history

## 1.3.1
* Make check for mixed case words optional.

## 1.3 - 9/4/24
* Add Usx-to-Usfm conversion process.
* mark_paragraphs - optionally, copy \s5 markers from model text.
* mark_paragraphs - new option to leave paragraph markers unchanged
* mark_paragraphs - ensure \p after \s
* usfm_cleanup - mark parenthesized section titles with high confidence.
* usfm_cleanup - other minor improvements.
* Support \pm, \pmo, \pmc, and \pmr USFM markers

## 1.2.4
* Add paratext / usfm file conversion.
* Improve quote mark conversions. Unit test verification.

## 1.2.3
* Bug fixes.
* verifyUsfm - fewer false positives of possible issues.
* verifyManifest - case sensitive file name checks.

## 1.2.2
* verifyUsfm - omit punctuation warning before Acts 22.
* verifyUsfm - report mixed case words.
* verifyUsfm - report likely section titles.

## 1.2.1
* verifyManifest - detect book title inconsistencies.
* verifyManifest - fewer low priority warnings.

## 1.2.0 - 5/15/24
* Add Word-to-text conversion for simple cases.
* Detect untranslated verses.
* Fix verifyUsfm overreporting of back to back markers.
* Fix usfm_cleanup bug placing all title fields on a single line.
* Other bug fixes.
* Omit numbers from word list.
* Eliminate extra characters from book titles.
* List source text resources in contributors.txt.
* Reduce warnings from verifyManifest.
* Redesigned plaintext2usfm to handle broader variety of input texts.

## 1.1.3
* Add Plaintext2Usfm process.
* Add chapter label finder function.
* Add option to fix chapter labels.
* Minor GUI improvements.
* Source code moved to https://github.com/Bible-Translation-Tools/usfm-tools.

## 1.1.2
* Solve button display inconsistency.
* Add helper buttons to open relevant files/folders.
* Bug fixes.

## 1.1.1
* Ensure wizard is top window initially.
* Minor GUI improvements.
* USFM verification: various improvements.
* Generate word list when verifying usfm.
* Add option in USFM Cleanup step to mark section headings.
* Add option in the Verify Manifest step to suppress warnings about ASCII book titles.
* Add option in the Mark Paragraphs step to disregard sentence boundaries. 
* Bug fixes

## 1.1.0 - 2/8/24
* Start with process selection screen.
* Add Usfm2Usx process.
* Add file/folder selection dialogs.
* Bug fixes.

## 1.0.2
* fixed usfm_cleanup crash

## 1.0.1
* fixed communication bugs between worker threads and GUI

## 1.0 - 1/11/24
* Initial version released
