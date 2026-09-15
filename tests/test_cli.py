"""Tests for CLI functionality."""
import json
import sys
from pathlib import Path

import pytest

from patch_fidelity_meter.cli import main


def test_cli_score_exact_match(tmp_path, monkeypatch, capsys):
    """Test CLI with exact match patches."""
    oracle_file = tmp_path / "oracle.patch"
    candidate_file = tmp_path / "candidate.patch"
    
    patch_content = """--- a/file.py
+++ b/file.py
@@ -1,2 +1,2 @@
-old
+new
"""
    oracle_file.write_text(patch_content)
    candidate_file.write_text(patch_content)
    
    monkeypatch.setattr(sys, "argv", [
        "patch-fidelity-meter",
        "score",
        "--oracle", str(oracle_file),
        "--candidate", str(candidate_file)
    ])
    
    main()
    
    captured = capsys.readouterr()
    assert "Fidelity Score (F1):     1.000" in captured.out
    assert "Recall:                  1.000" in captured.out
    assert "Precision:               1.000" in captured.out


def test_cli_score_json_output(tmp_path, monkeypatch, capsys):
    """Test CLI with JSON output."""
    oracle_file = tmp_path / "oracle.patch"
    candidate_file = tmp_path / "candidate.patch"
    
    patch_content = """--- a/file.py
+++ b/file.py
@@ -1,2 +1,2 @@
-old
+new
"""
    oracle_file.write_text(patch_content)
    candidate_file.write_text(patch_content)
    
    monkeypatch.setattr(sys, "argv", [
        "patch-fidelity-meter",
        "score",
        "--oracle", str(oracle_file),
        "--candidate", str(candidate_file),
        "--json"
    ])
    
    main()
    
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    
    assert result["fidelity"] == 1.0
    assert result["recall"] == 1.0
    assert result["precision"] == 1.0
    assert result["bloat"] == 0.0
    assert result["sprawl"] == 0
    assert result["unrelated_hunks"] == 0


def test_cli_min_fidelity_pass(tmp_path, monkeypatch):
    """Test CLI with min-fidelity threshold that passes."""
    oracle_file = tmp_path / "oracle.patch"
    candidate_file = tmp_path / "candidate.patch"
    
    patch_content = """--- a/file.py
+++ b/file.py
@@ -1,2 +1,2 @@
-old
+new
"""
    oracle_file.write_text(patch_content)
    candidate_file.write_text(patch_content)
    
    monkeypatch.setattr(sys, "argv", [
        "patch-fidelity-meter",
        "score",
        "--oracle", str(oracle_file),
        "--candidate", str(candidate_file),
        "--min-fidelity", "0.8"
    ])
    
    main()


def test_cli_min_fidelity_fail(tmp_path, monkeypatch, capsys):
    """Test CLI with min-fidelity threshold that fails."""
    oracle_file = tmp_path / "oracle.patch"
    candidate_file = tmp_path / "candidate.patch"
    
    oracle_content = """--- a/file.py
+++ b/file.py
@@ -1,2 +1,2 @@
-old
+new
"""
    candidate_content = """--- a/other.py
+++ b/other.py
@@ -1,2 +1,2 @@
-unrelated
+change
"""
    oracle_file.write_text(oracle_content)
    candidate_file.write_text(candidate_content)
    
    monkeypatch.setattr(sys, "argv", [
        "patch-fidelity-meter",
        "score",
        "--oracle", str(oracle_file),
        "--candidate", str(candidate_file),
        "--min-fidelity", "0.8"
    ])
    
    with pytest.raises(SystemExit) as exc_info:
        main()
    
    assert exc_info.value.code == 1


def test_cli_missing_oracle(tmp_path, monkeypatch):
    """Test CLI with missing oracle file."""
    candidate_file = tmp_path / "candidate.patch"
    candidate_file.write_text("dummy")
    
    monkeypatch.setattr(sys, "argv", [
        "patch-fidelity-meter",
        "score",
        "--oracle", str(tmp_path / "nonexistent.patch"),
        "--candidate", str(candidate_file)
    ])
    
    with pytest.raises(SystemExit) as exc_info:
        main()
    
    assert exc_info.value.code == 1


def test_cli_example_files(monkeypatch, capsys):
    """Test CLI with example fixture files."""
    examples_dir = Path(__file__).parent.parent / "examples"
    
    if not examples_dir.exists():
        pytest.skip("Examples directory not found")
    
    oracle_file = examples_dir / "oracle_simple.patch"
    candidate_file = examples_dir / "candidate_exact_match.patch"
    
    if not oracle_file.exists() or not candidate_file.exists():
        pytest.skip("Example files not found")
    
    monkeypatch.setattr(sys, "argv", [
        "patch-fidelity-meter",
        "score",
        "--oracle", str(oracle_file),
        "--candidate", str(candidate_file),
        "--json"
    ])
    
    main()
    
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert result["fidelity"] == 1.0
