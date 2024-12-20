# Downloads the lower resolution, chapter level mp3 files from https://audio-content.bibleineverylanguage.org/content/.
# Renames the files for better sorting.

# User instructions:
# 1. Install the python requests library, if not already done.
#      > pip install requests
# 2. Set the desired location for the mp3 files on your computer.
#      (Set the folder variable below.)
# 3. Set the range of Bible books to be downloaded, in the main() function (about line 54 in this file).
#      Example:  53 < usfm_verses.verseCounts[book]['sort'] < 56  will get 1 & 2 Timothy
#      Example:  0 < usfm_verses.verseCounts[book]['sort'] < 67  will get all 66 books
# 4. Run the script.
#      > python download_mp3.py

import os
import sys
import requests

folder = r"c:\DCS\Tamil\Audio"  # Top level folder
urlbase = r"https://audio-content.bibleineverylanguage.org/content/"
misc_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(misc_path), "src")
sys.path.append(src_path)
import usfm_verses

# Copies the specified URL resource to the specified location.
def download(urlpath, localpath):
    try:
        req = requests.get(urlpath)
        with open(localpath, 'wb') as outfile:
            for chunk in req.iter_content(64 * 1024):
                outfile.write(chunk)
        result = os.path.basename(localpath)
    except Exception as e:
        result = str(e)
    return result

# Retrieves each chapter .mp3 file from the specified book.
# Places the files into the specified folder.
def getbook(book, folder):
    for chapter in range(1, usfm_verses.verseCounts[book]['chapters'] + 1):
        urlfile = f"ta_ulb_{book.lower()}_c{chapter}.mp3"
        urlpath = urlbase + f"ta/ulb/{book.lower()}/{chapter}/CONTENTS/mp3/low/chapter/{urlfile}"
        zchapstr = f"{chapter:02}"
        localname = f"{usfm_verses.verseCounts[book]['usfm_number']}-{book.upper()}_{zchapstr}_{urlfile}"
        localpath = os.path.join(folder, localname)
        result = download(urlpath, localpath)
        print(result)
        sys.stdout.flush()

def main():
    global folder
    for book in usfm_verses.verseCounts:
        if 53 < usfm_verses.verseCounts[book]['sort'] < 56:
            bookfolder = f"{folder}/{book.lower()}"
            os.makedirs(bookfolder, exist_ok = True)
            getbook(book, bookfolder)

if __name__ == "__main__":
    main()
