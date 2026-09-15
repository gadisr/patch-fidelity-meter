"""Command-line interface for patch-fidelity-meter."""
import argparse
import json
import sys
from pathlib import Path

from patch_fidelity_meter import parse_unified_diff
from patch_fidelity_meter.scoring import compute_fidelity


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="patch-fidelity-meter",
        description="Score patches vs minimal oracle diff (bloat/sprawl/unrelated hunks). No LLM."
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    score_parser = subparsers.add_parser("score", help="Score a candidate patch against an oracle")
    score_parser.add_argument(
        "--oracle",
        required=True,
        type=Path,
        help="Path to oracle patch file (minimal correct change)"
    )
    score_parser.add_argument(
        "--candidate",
        required=True,
        type=Path,
        help="Path to candidate patch file (agent/model-produced change)"
    )
    score_parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    score_parser.add_argument(
        "--min-fidelity",
        type=float,
        help="Minimum fidelity score required (0.0-1.0). Exit code 1 if below threshold."
    )
    
    args = parser.parse_args()
    
    if args.command == "score":
        run_score(args)
    else:
        parser.print_help()
        sys.exit(1)


def run_score(args: argparse.Namespace) -> None:
    """Run the score command."""
    oracle_path = args.oracle
    candidate_path = args.candidate
    
    if not oracle_path.exists():
        print(f"Error: Oracle patch file not found: {oracle_path}", file=sys.stderr)
        sys.exit(1)
    
    if not candidate_path.exists():
        print(f"Error: Candidate patch file not found: {candidate_path}", file=sys.stderr)
        sys.exit(1)
    
    oracle_text = oracle_path.read_text()
    candidate_text = candidate_path.read_text()
    
    oracle_patch = parse_unified_diff(oracle_text)
    candidate_patch = parse_unified_diff(candidate_text)
    
    score = compute_fidelity(oracle_patch, candidate_patch)
    
    if args.json:
        output = {
            "fidelity": score.fidelity,
            "recall": score.recall,
            "precision": score.precision,
            "bloat": score.bloat,
            "sprawl": score.sprawl,
            "unrelated_hunks": score.unrelated_hunks,
            "oracle_line_count": score.oracle_line_count,
            "candidate_line_count": score.candidate_line_count,
            "matched_line_count": score.matched_line_count
        }
        print(json.dumps(output, indent=2))
    else:
        print("Patch Fidelity Metrics")
        print("=" * 50)
        print(f"Fidelity Score (F1):     {score.fidelity:.3f}")
        print(f"Recall:                  {score.recall:.3f}")
        print(f"Precision:               {score.precision:.3f}")
        print(f"Bloat (1-precision):     {score.bloat:.3f}")
        print(f"Sprawl (extra files):    {score.sprawl}")
        print(f"Unrelated hunks:         {score.unrelated_hunks}")
        print()
        print(f"Oracle lines changed:    {score.oracle_line_count}")
        print(f"Candidate lines changed: {score.candidate_line_count}")
        print(f"Matched lines:           {score.matched_line_count}")
    
    if args.min_fidelity is not None:
        if score.fidelity < args.min_fidelity:
            if not args.json:
                print(f"\nFidelity score {score.fidelity:.3f} below minimum threshold {args.min_fidelity:.3f}")
            sys.exit(1)


if __name__ == "__main__":
    main()
