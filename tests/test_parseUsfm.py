# pytest unit tests for promoteDoubleQuotes() functions in quotes.py

import os
import sys
import io

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
import pytest
import parseUsfm
from line_profiler import LineProfiler

def test_speed():
    path = r'C:\DCS\EnglishTest\en_ulb.WA.v24-02\39-MAL.usfm'
    with io.open(path, "tr", encoding="utf-8-sig") as input:
        contents = input.read(-1)
    lp = LineProfiler()
    lp_wrapper = lp(parseUsfm.parseString)
    lp_wrapper(contents)
    lp.print_stats()

if __name__ == "__main__":
    test_speed()
