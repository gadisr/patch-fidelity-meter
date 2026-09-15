"""Scoring functions for patch fidelity metrics."""
from dataclasses import dataclass

from patch_fidelity_meter import Patch


@dataclass
class FidelityScore:
    """Container for all fidelity metrics.
    
    Metrics:
    - recall: fraction of oracle changed lines present in candidate [0,1]
    - precision: fraction of candidate changed lines present in oracle [0,1]
    - bloat: extra lines changed in candidate beyond oracle (1 - precision)
    - sprawl: number of files touched by candidate that oracle did not touch
    - unrelated_hunks: number of candidate hunks with no overlap to any oracle hunk
    - fidelity: composite score from precision and recall (F1 score) [0,1]
    
    Formulas:
    - recall = |oracle_lines ∩ candidate_lines| / |oracle_lines|
    - precision = |oracle_lines ∩ candidate_lines| / |candidate_lines|
    - bloat = 1 - precision
    - sprawl = |candidate_files - oracle_files|
    - unrelated_hunks = count of candidate hunks with no file+region overlap to oracle
    - fidelity = 2 * (precision * recall) / (precision + recall)  [F1 score]
    """
    
    recall: float
    precision: float
    bloat: float
    sprawl: int
    unrelated_hunks: int
    fidelity: float
    
    oracle_line_count: int
    candidate_line_count: int
    matched_line_count: int


def compute_fidelity(oracle: Patch, candidate: Patch) -> FidelityScore:
    """Compute fidelity metrics comparing candidate patch against oracle.
    
    Args:
        oracle: The minimal correct patch
        candidate: The agent/model-produced patch to score
    
    Returns:
        FidelityScore with all computed metrics
    """
    oracle_lines = oracle.get_changed_lines()
    candidate_lines = candidate.get_changed_lines()
    
    oracle_line_set = set(oracle_lines)
    candidate_line_set = set(candidate_lines)
    
    matched_lines = oracle_line_set & candidate_line_set
    matched_count = len(matched_lines)
    
    oracle_count = len(oracle_lines)
    candidate_count = len(candidate_lines)
    
    recall = matched_count / oracle_count if oracle_count > 0 else 1.0
    precision = matched_count / candidate_count if candidate_count > 0 else 1.0
    
    bloat = 1.0 - precision
    
    oracle_files = oracle.get_files()
    candidate_files = candidate.get_files()
    sprawl = len(candidate_files - oracle_files)
    
    unrelated_hunks = 0
    for candidate_hunk in candidate.hunks:
        has_overlap = any(
            candidate_hunk.overlaps_with(oracle_hunk)
            for oracle_hunk in oracle.hunks
        )
        if not has_overlap:
            unrelated_hunks += 1
    
    if precision + recall > 0:
        fidelity = 2 * (precision * recall) / (precision + recall)
    else:
        fidelity = 0.0
    
    return FidelityScore(
        recall=recall,
        precision=precision,
        bloat=bloat,
        sprawl=sprawl,
        unrelated_hunks=unrelated_hunks,
        fidelity=fidelity,
        oracle_line_count=oracle_count,
        candidate_line_count=candidate_count,
        matched_line_count=matched_count
    )
