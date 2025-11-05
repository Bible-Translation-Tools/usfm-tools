# Usfm Wizard Version history

## 1.4.4 - 11/5/25
* Updated the online user manual.
* txt2Usfm - supply correct \c when missing from text files.
* txt2Usfm - consider \p markers in the text files as erroneous and don't copy.
* txt2Usfm, verifyUsfm - exclude certain verses from section title consideration.
* txt2Usfm - forestall creation of bad project info on language code error.
* txt2Usfm - convert periods to Arabic full stops in Arabic texts.
* verifyUsfm - generate manifest.yaml file.
* verifyUsfm - don't display voluminous list of issues in the GUI.
* verifyUsfm - remove 'low paragraph count' warning.
* verifyUsfm - remove ability to suppress 'no \p after \c' warnings.
* verifyUsfm - remove ability to suppress warnings about useless markers.
* verifyUsfm - eliminate redundant "back to back marker" warnings.
* verifyusfm - refine wordlist and mixed case words identification.
* verifyUsfm - use source text to compare verse counts per chapter.
* verifyUsfm - don't require capitalization for Gurmukhi script (affects section title recognition only, at this point)
* verifyUsfm - support verse bridges when checking for very short translations.
* usfm_cleanup - eliminate space before \f.
* mark_paragraphs - new option: translate chunk markers to \p.
* mark_paragraphs - generate separate issues file, including missing end-of-paragraph punctuation.
* plaintext2usfm - handle more types of invalid inputs.
* all tools - observe Arabic full stop character.
* other minor enhancements and bug fixes.

## 1.4.3 - 8/11/25
* replace USFM parser - eliminates bugs and performance bottlenecks.
* txt2Usfm - improve verse number resolution.
* txt2Usfm - added help message for section headings.
* mark_paragraphs - capture model directory from Verify step.
* mark_paragraphs - GUI input autofill and validation enhancements.
* verifyUsfm - GUI input autofill and validation enhancements.
* miscellaneous bug fixes

## 1.4.2 - 7/16/25
* txt2Usfm - incremental improvements around verse numbering.
* usfm_cleanup - preserve line breaks.
* mark_paragraphs - preserve line breaks.
* mark_paragraphs - incremental improvements in marking section titles.
* mark_paragraphs - in most cases, it now copies paragraph ending punctuation from model text where missing.
* mark_paragraphs - bug fixes
* all tools - recognize Arabic question mark ؟

## 1.4.1 - 7/2/25
* plaintext2Usfm - support more different chapter and verse markers, to facilitate conversions from Word.
* txt2Usfm - default to English book title when title.txt is missing.
* tx2Usfm - suppress blank \cl lines.
* txt2Usfm - 35% performance improvement
* txt2Usfm - improved correction of corrupt chapter and verse markers
* txt2Usfm - improved correction of spacing around punctuation
* verifyUsfm - validate \ide field.
* verifyUsfm - report too-sparse section headings.
* verifyUsfm - improve Ethiopic word definition.
* verifyUsfm GUI - display reasons why the VERIFY button is disabled.
* usfm_cleanup - further quotes cleanup.

## 1.4.0 - 5/22/25
* Wizard - configured to run on Linux and iOS, in addition to Windows.
* Wizard - added a step to the Usfm2Usx process.
* verifyUsfm - make footnote warnings source text-specific.
* verifyUsfm - report verse translations that are very short compared to source text.
* verifyUsfm - report possible section titles by verse reference rather than line number.
* verifyUsfm - further refinement of section title recognition.
* verifyUsfm - fix overcount of poetry paragraphs.
* verifyUsfm - eliminate 'Ascii content' option from GUI; detect automatically.
* verifyUsfm - take language code automatically from manifest.yaml.
* verifyUsfm - source text folder dialog now suggests what folder to look for.
* usfm_cleanup - exclude end of JHN 19:19 from section title check.
* usfm_cleanup - improved verse number cleanup.
* usfm_cleanup - fix most floating quotes.
* usfm_cleanup - remove 'Capitalization fix' option from GUI.
* usfm_cleanup - further refinement of section title markup.
* txt2Usfm - relax folder name requirement.
* verifyManifest - stop warning about common source languages like 'sw'.

## 1.3.6
* txt2Usfm - generate manifest.yaml file.
* txt2Usfm - generate project info file with downstream benefits listed below.
* verifyUsfm - strengthen GUI input validation.
* verifyUsfm - show source text identification hint in GUI.
* verifyManifest - expose the resource type option in the GUI.
* verifyManifest - expanded some warning messages.
* usfm_wizard - moved Help files to shared folder on OneDrive, still accessible from the Help menu.

## 1.3.5 - 3/20/25
* usfm_cleanup - remove periods after verse numbers.
* usfm_cleanup - add chapter label finder function.
* usfm_cleanup - remove standard fix options from GUI.
* txt2Usfm and usfm_cleanup - some improvements to section title recognition.
* verifyUsfm - improve possible footnote recognition.
* verifyUsfm - eliminated incorrect warning about needing paragraph marker after \s5.
* verifyUsfm - eliminate some redundant warnings.
* verifyUsfm - eliminate warnings about apparent footnotes between square brackets.

## 1.3.4 - 3/6/25
* verifyUsfm - use TSV file for wordlist.
* verifyUsfm - report hapax legomena.
* verifyUsfm - change naming scheme for backup issues.txt files.
* verifyUsfm - list suppressed issues in issues.txt.
* verifyUsfm - improved detection of possible section headings.
* verifyUsfm - ignore punctuation before \m.
* verifyUsfm - fix bug identifying inconsistent chapter titles.
* usfm_cleanup - handle truncated usfm files.
* usfm_cleanup - remove stray verse numbers at start of verse.
* usfm_cleanup - spacing (nonbreak if any) before Devanagari Danda characters.
* usfm_cleanup - spacing after right paren, brace or bracket.
* mark_paragraphs - insert remark in target USFM file to identify model text.

## 1.3.3
* txt2usfm - optionally, mark section headings
* usfm_cleanup - improve section heading markup
* fix rare wizard startup bug
* verifyUsfm - handle character encoding exceptions

## 1.3.2
* Bug fixes
* txt2usfm - don't overwrite the projects and contributors lists on single book conversions.
* verifyUsfm - ignore most numbering issues in intro paragraphs.
* verifyUsfm - report section headings not followed by paragraph mark.
* usfm_cleanup - ensure \p mark after section headings.
* usfm_cleanup - punctuation, spacing improvements.
* word2text - handle more file name variations.

## 1.3.1
* Make check for mixed case words optional.
* usfm_cleanup - ensure space before left paren
* usfm_cleanup - make section title recognition optional.

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
