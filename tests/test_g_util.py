# pytest unit tests for functions in g_util.py

import os
import sys
import shutil
# import pytest

tests_path = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.join(os.path.dirname(tests_path), "src")
sys.path.append(src_path)
import g_util


def test_count_files(tmp_path):
    folder = tmp_path / "files"
    folder.mkdir()
    (folder / "alpha.txt").write_text("one", encoding="utf-8")
    (folder / "ALPHA.md").write_text("two", encoding="utf-8")
    (folder / "beta.txt").write_text("three", encoding="utf-8")

    assert g_util.count_files(str(folder), r"^alpha\..*$") == 2
    assert g_util.count_files(str(folder), r"^beta\.txt$") == 1
    assert g_util.count_files(str(tmp_path / "missing"), r"^alpha") == 0
    shutil.rmtree(str(tmp_path))

def test_count_folders(tmp_path):
    root = tmp_path / "root"
    (root / "alpha").mkdir(parents=True)
    (root / "alphabet").mkdir()
    (root / "beta").mkdir()

    assert g_util.count_folders(str(root), "alpha") == 2
    assert g_util.count_folders(str(root), "beta") == 1
    assert g_util.count_folders(str(tmp_path / "missing"), "alpha") == 0


def test_get_language_code_and_name(tmp_path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "manifest.yaml").write_text(
        "dublin_core:\n"
        "  language:\n"
        "    identifier: eng\n"
        "    title: English\n",
        encoding="utf-8",
    )

    assert g_util.get_language_code(str(project_dir)) == "eng"
    assert g_util.get_language_name(str(project_dir)) == "English"
    assert g_util.get_language_code(str(tmp_path / "missing")) == ""
