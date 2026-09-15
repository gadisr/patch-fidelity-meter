"""Tests for scoring functionality."""
import pytest

from patch_fidelity_meter import parse_unified_diff, Patch, Hunk
from patch_fidelity_meter.scoring import compute_fidelity


def test_exact_match():
    """Test fidelity when candidate exactly matches oracle."""
    diff = """--- a/file.py
+++ b/file.py
@@ -1,2 +1,2 @@
-old line
+new line
"""
    oracle = parse_unified_diff(diff)
    candidate = parse_unified_diff(diff)
    
    score = compute_fidelity(oracle, candidate)
    
    assert score.recall == 1.0
    assert score.precision == 1.0
    assert score.bloat == 0.0
    assert score.sprawl == 0
    assert score.unrelated_hunks == 0
    assert score.fidelity == 1.0


def test_bloat_extra_changes():
    """Test detection of extra changes (bloat)."""
    oracle_diff = """--- a/file.py
+++ b/file.py
@@ -1,2 +1,2 @@
-old line
+new line
"""
    candidate_diff = """--- a/file.py
+++ b/file.py
@@ -1,4 +1,4 @@
-old line
+new line
 context
-another old
+another new
"""
    oracle = parse_unified_diff(oracle_diff)
    candidate = parse_unified_diff(candidate_diff)
    
    score = compute_fidelity(oracle, candidate)
    
    assert score.recall == 1.0
    assert score.precision < 1.0
    assert score.bloat > 0.0
    assert score.sprawl == 0
    assert score.candidate_line_count > score.oracle_line_count


def test_sprawl_extra_files():
    """Test detection of extra files touched (sprawl)."""
    oracle_diff = """--- a/file1.py
+++ b/file1.py
@@ -1,2 +1,2 @@
-old
+new
"""
    candidate_diff = """--- a/file1.py
+++ b/file1.py
@@ -1,2 +1,2 @@
-old
+new
--- a/file2.py
+++ b/file2.py
@@ -1,2 +1,2 @@
-extra old
+extra new
"""
    oracle = parse_unified_diff(oracle_diff)
    candidate = parse_unified_diff(candidate_diff)
    
    score = compute_fidelity(oracle, candidate)
    
    assert score.sprawl == 1


def test_missing_oracle_changes():
    """Test when candidate is missing some oracle changes."""
    oracle_diff = """--- a/file.py
+++ b/file.py
@@ -1,4 +1,4 @@
-old1
+new1
 context
-old2
+new2
"""
    candidate_diff = """--- a/file.py
+++ b/file.py
@@ -1,2 +1,2 @@
-old1
+new1
"""
    oracle = parse_unified_diff(oracle_diff)
    candidate = parse_unified_diff(candidate_diff)
    
    score = compute_fidelity(oracle, candidate)
    
    assert score.recall < 1.0
    assert score.precision == 1.0


def test_unrelated_hunks():
    """Test detection of completely unrelated hunks."""
    oracle_diff = """--- a/file1.py
+++ b/file1.py
@@ -1,2 +1,2 @@
-old
+new
"""
    candidate_diff = """--- a/file2.py
+++ b/file2.py
@@ -1,2 +1,2 @@
-unrelated old
+unrelated new
"""
    oracle = parse_unified_diff(oracle_diff)
    candidate = parse_unified_diff(candidate_diff)
    
    score = compute_fidelity(oracle, candidate)
    
    assert score.unrelated_hunks == 1
    assert score.recall == 0.0
    assert score.precision == 0.0
    assert score.fidelity == 0.0


def test_partial_overlap():
    """Test when candidate has both matching and non-matching changes."""
    oracle_diff = """--- a/file.py
+++ b/file.py
@@ -1,2 +1,2 @@
-old line
+new line
"""
    candidate_diff = """--- a/file.py
+++ b/file.py
@@ -1,4 +1,4 @@
-old line
+new line
-different old
+different new
"""
    oracle = parse_unified_diff(oracle_diff)
    candidate = parse_unified_diff(candidate_diff)
    
    score = compute_fidelity(oracle, candidate)
    
    assert 0 < score.recall <= 1.0
    assert 0 < score.precision < 1.0
    assert 0 < score.fidelity < 1.0


def test_empty_patches():
    """Test handling of empty patches."""
    oracle = Patch([])
    candidate = Patch([])
    
    score = compute_fidelity(oracle, candidate)
    
    assert score.recall == 1.0
    assert score.precision == 1.0
    assert score.fidelity == 1.0


def test_fidelity_f1_calculation():
    """Test that fidelity is correctly calculated as F1 score."""
    oracle = Patch([Hunk("f.py", 1, 5, 1, 5, ["-a", "-b", "-c", "-d", "-e"])])
    candidate = Patch([Hunk("f.py", 1, 5, 1, 5, ["-a", "-b", "-c", "+x", "+y"])])
    
    score = compute_fidelity(oracle, candidate)
    
    expected_f1 = 2 * (score.precision * score.recall) / (score.precision + score.recall)
    assert abs(score.fidelity - expected_f1) < 0.001
