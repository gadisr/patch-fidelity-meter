"""Tests for diff parsing functionality."""
import pytest

from patch_fidelity_meter import parse_unified_diff, Patch, Hunk


def test_parse_simple_diff():
    """Test parsing a simple unified diff."""
    diff = """--- a/file.py
+++ b/file.py
@@ -1,3 +1,3 @@
 def foo():
-    return 1
+    return 2
"""
    patch = parse_unified_diff(diff)
    assert len(patch.hunks) == 1
    assert patch.hunks[0].file_path == "file.py"
    assert patch.hunks[0].old_start == 1
    assert patch.hunks[0].old_count == 3
    assert patch.hunks[0].new_start == 1
    assert patch.hunks[0].new_count == 3


def test_parse_multiple_hunks():
    """Test parsing a diff with multiple hunks."""
    diff = """--- a/file.py
+++ b/file.py
@@ -1,3 +1,3 @@
 def foo():
-    return 1
+    return 2
@@ -10,2 +10,2 @@
 def bar():
-    pass
+    return None
"""
    patch = parse_unified_diff(diff)
    assert len(patch.hunks) == 2
    assert patch.hunks[0].old_start == 1
    assert patch.hunks[1].old_start == 10


def test_parse_multiple_files():
    """Test parsing a diff with multiple files."""
    diff = """--- a/file1.py
+++ b/file1.py
@@ -1,2 +1,2 @@
-old line
+new line
--- a/file2.py
+++ b/file2.py
@@ -1,2 +1,2 @@
-another old
+another new
"""
    patch = parse_unified_diff(diff)
    assert len(patch.hunks) == 2
    assert patch.hunks[0].file_path == "file1.py"
    assert patch.hunks[1].file_path == "file2.py"


def test_get_changed_lines():
    """Test extracting changed lines from a hunk."""
    hunk = Hunk(
        file_path="test.py",
        old_start=1,
        old_count=3,
        new_start=1,
        new_count=3,
        lines=[
            " context line",
            "-removed line",
            "+added line",
            " another context"
        ]
    )
    changed = hunk.get_changed_lines()
    assert len(changed) == 2
    assert "-removed line" in changed
    assert "+added line" in changed
    assert " context line" not in changed


def test_hunk_overlap_same_file_overlapping_range():
    """Test that hunks in the same file with overlapping ranges overlap."""
    hunk1 = Hunk("file.py", 10, 5, 10, 5, [])
    hunk2 = Hunk("file.py", 12, 5, 12, 5, [])
    assert hunk1.overlaps_with(hunk2)
    assert hunk2.overlaps_with(hunk1)


def test_hunk_overlap_same_file_non_overlapping():
    """Test that hunks in the same file with non-overlapping ranges don't overlap."""
    hunk1 = Hunk("file.py", 10, 5, 10, 5, [])
    hunk2 = Hunk("file.py", 20, 5, 20, 5, [])
    assert not hunk1.overlaps_with(hunk2)
    assert not hunk2.overlaps_with(hunk1)


def test_hunk_overlap_different_files():
    """Test that hunks in different files never overlap."""
    hunk1 = Hunk("file1.py", 10, 5, 10, 5, [])
    hunk2 = Hunk("file2.py", 10, 5, 10, 5, [])
    assert not hunk1.overlaps_with(hunk2)


def test_patch_get_files():
    """Test getting all files from a patch."""
    patch = Patch([
        Hunk("file1.py", 1, 1, 1, 1, []),
        Hunk("file2.py", 1, 1, 1, 1, []),
        Hunk("file1.py", 10, 1, 10, 1, [])
    ])
    files = patch.get_files()
    assert len(files) == 2
    assert "file1.py" in files
    assert "file2.py" in files


def test_parse_git_style_paths():
    """Test parsing git-style a/ b/ prefixed paths."""
    diff = """--- a/src/module.py
+++ b/src/module.py
@@ -1,2 +1,2 @@
-old
+new
"""
    patch = parse_unified_diff(diff)
    assert patch.hunks[0].file_path == "src/module.py"
