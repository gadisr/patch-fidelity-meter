"""Test using example files from the examples directory."""
from pathlib import Path

import pytest

from patch_fidelity_meter import parse_unified_diff
from patch_fidelity_meter.scoring import compute_fidelity


EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


@pytest.mark.skipif(not EXAMPLES_DIR.exists(), reason="Examples directory not found")
def test_exact_match_example():
    """Test exact match example."""
    oracle = parse_unified_diff((EXAMPLES_DIR / "oracle_simple.patch").read_text())
    candidate = parse_unified_diff((EXAMPLES_DIR / "candidate_exact_match.patch").read_text())
    
    score = compute_fidelity(oracle, candidate)
    
    assert score.fidelity == 1.0
    assert score.recall == 1.0
    assert score.precision == 1.0


@pytest.mark.skipif(not EXAMPLES_DIR.exists(), reason="Examples directory not found")
def test_bloat_example():
    """Test example with bloat (extra changes)."""
    oracle = parse_unified_diff((EXAMPLES_DIR / "oracle_simple.patch").read_text())
    candidate = parse_unified_diff((EXAMPLES_DIR / "candidate_with_bloat.patch").read_text())
    
    score = compute_fidelity(oracle, candidate)
    
    assert score.recall == 1.0
    assert score.precision < 1.0
    assert score.bloat > 0.0


@pytest.mark.skipif(not EXAMPLES_DIR.exists(), reason="Examples directory not found")
def test_sprawl_example():
    """Test example with sprawl (extra files)."""
    oracle = parse_unified_diff((EXAMPLES_DIR / "oracle_simple.patch").read_text())
    candidate = parse_unified_diff((EXAMPLES_DIR / "candidate_with_sprawl.patch").read_text())
    
    score = compute_fidelity(oracle, candidate)
    
    assert score.sprawl > 0
    assert score.unrelated_hunks > 0


@pytest.mark.skipif(not EXAMPLES_DIR.exists(), reason="Examples directory not found")
def test_missing_oracle_example():
    """Test example missing oracle changes."""
    oracle = parse_unified_diff((EXAMPLES_DIR / "oracle_simple.patch").read_text())
    candidate = parse_unified_diff((EXAMPLES_DIR / "candidate_missing_oracle.patch").read_text())
    
    score = compute_fidelity(oracle, candidate)
    
    assert score.recall < 1.0


@pytest.mark.skipif(not EXAMPLES_DIR.exists(), reason="Examples directory not found")
def test_unrelated_example():
    """Test example with completely unrelated changes."""
    oracle = parse_unified_diff((EXAMPLES_DIR / "oracle_simple.patch").read_text())
    candidate = parse_unified_diff((EXAMPLES_DIR / "candidate_unrelated.patch").read_text())
    
    score = compute_fidelity(oracle, candidate)
    
    assert score.fidelity == 0.0
    assert score.unrelated_hunks == 1
