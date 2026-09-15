# patch-fidelity-meter

**Quantify patch fidelity for coding-agent evaluation.** Score any candidate patch against a minimal oracle diff, measuring bloat (unnecessary changes), sprawl (extra files touched), and unrelated hunks. Pure diff analysis using stdlib—no LLM, no black-box scoring. Designed for benchmarks, agent harnesses, and CI quality gates where you need objective, reproducible patch quality metrics.

## Installation

```bash
# From source (editable install)
pip install -e .

# With dev dependencies
pip install -e ".[dev]"
```

## Quick Start

```bash
# Score a candidate patch against an oracle
patch-fidelity-meter score --oracle oracle.patch --candidate candidate.patch

# JSON output
patch-fidelity-meter score --oracle oracle.patch --candidate candidate.patch --json

# Exit code 1 if fidelity below threshold (useful in CI)
patch-fidelity-meter score --oracle oracle.patch --candidate candidate.patch --min-fidelity 0.8
```

You can also run as a module:

```bash
python -m patch_fidelity_meter score --oracle oracle.patch --candidate candidate.patch
```

## Metrics

The tool computes the following metrics:

### Fidelity Score (F1)

Composite score combining precision and recall using the F1 formula. Range: [0, 1], where 1 is perfect.

**Formula:** `fidelity = 2 × (precision × recall) / (precision + recall)`

### Recall

Fraction of oracle changed lines present in the candidate.

**Formula:** `recall = |oracle_lines ∩ candidate_lines| / |oracle_lines|`

- **1.0**: Candidate includes all oracle changes
- **< 1.0**: Candidate is missing some oracle changes

### Precision

Fraction of candidate changed lines that appear in the oracle.

**Formula:** `precision = |oracle_lines ∩ candidate_lines| / |candidate_lines|`

- **1.0**: All candidate changes are in the oracle
- **< 1.0**: Candidate has extra changes beyond the oracle

### Bloat

Extra changes in the candidate beyond what the oracle specifies.

**Formula:** `bloat = 1 - precision`

- **0.0**: No bloat (perfect precision)
- **> 0**: Candidate made unnecessary changes

### Sprawl

Number of files touched by the candidate that the oracle did not touch.

**Formula:** `sprawl = |candidate_files - oracle_files|`

- **0**: No extra files touched
- **> 0**: Candidate modified files the oracle didn't

### Unrelated Hunks

Number of candidate hunks that have no overlap with any oracle hunk.

**Definition of overlap:** Two hunks overlap if they affect the same file AND their line ranges overlap in either the old or new version of the file.

- **0**: All candidate hunks relate to oracle hunks
- **> 0**: Candidate has hunks in unrelated regions

## Input Format

The tool accepts unified diff format, including:

- Standard `diff -u` output
- Git-style diffs (`git diff`, `git format-patch`)
- Diffs with `a/` and `b/` path prefixes

Example patch:

```diff
--- a/hello.py
+++ b/hello.py
@@ -1,3 +1,3 @@
 def greet(name):
-    return "Hello, " + name
+    return f"Hello, {name}!"
```

## Examples

See the `examples/` directory for sample patches demonstrating each metric:

- `oracle_simple.patch` - Minimal correct change
- `candidate_exact_match.patch` - Perfect match (fidelity = 1.0)
- `candidate_with_bloat.patch` - Extra changes (bloat > 0)
- `candidate_with_sprawl.patch` - Extra files touched (sprawl > 0)
- `candidate_missing_oracle.patch` - Missing oracle changes (recall < 1.0)
- `candidate_unrelated.patch` - Completely unrelated changes (fidelity = 0.0)

Try them:

```bash
# Perfect match
patch-fidelity-meter score \
  --oracle examples/oracle_simple.patch \
  --candidate examples/candidate_exact_match.patch

# With bloat
patch-fidelity-meter score \
  --oracle examples/oracle_simple.patch \
  --candidate examples/candidate_with_bloat.patch --json
```

## Use Cases

### 1. SWE-bench Patch Quality Gate

Reject candidates that sprawl beyond the minimal fix. Given a gold-standard patch for SWE-bench task `django/django#12345`, score each agent's submission:

```bash
# Extract minimal fix from gold patch
patch-fidelity-meter score \
  --oracle swebench/django-12345-minimal.patch \
  --candidate agent-submissions/gpt-4.patch \
  --min-fidelity 0.75

# Exit code 1 if fidelity < 0.75
```

**Example: sprawl detection**
```diff
Oracle touches: src/django/db/models/query.py
Candidate touches: src/django/db/models/query.py, tests/fixtures/data.json
Sprawl: 1 → fidelity drops, flags unnecessary test fixture change
```

### 2. Meta-Harness Edit Bloat Comparison

Track precision regression across agent versions. Compare edit bloat when evolving a coding harness:

```bash
# Score agent v1 vs v2 on the same task set
for task in tasks/*.json; do
  oracle="oracles/$(basename $task .json).patch"
  
  patch-fidelity-meter score --oracle "$oracle" \
    --candidate "v1-output/$(basename $task .json).patch" \
    --json | jq -r '.bloat' >> v1-bloat.txt
  
  patch-fidelity-meter score --oracle "$oracle" \
    --candidate "v2-output/$(basename $task .json).patch" \
    --json | jq -r '.bloat' >> v2-bloat.txt
done

# Compare: mean bloat v1 vs v2
paste v1-bloat.txt v2-bloat.txt | awk '{sum1+=$1; sum2+=$2; n++} END {print "v1:", sum1/n, "v2:", sum2/n}'
```

**Example output:**
```
v1: 0.42  v2: 0.31  →  26% bloat reduction
```

### 3. CI Scoreboard: Reject Sprawling PRs

Add a CI check that fails when a PR touches unrelated files:

```yaml
# .github/workflows/patch-fidelity.yml
- name: Check patch fidelity
  run: |
    git diff origin/main...HEAD > candidate.patch
    patch-fidelity-meter score \
      --oracle minimal-expected.patch \
      --candidate candidate.patch \
      --json | tee fidelity.json
    
    sprawl=$(jq -r '.sprawl' fidelity.json)
    if [ "$sprawl" -gt 0 ]; then
      echo "❌ PR touches $sprawl unrelated files"
      exit 1
    fi
```

**Example: prevent accidental changes**
```
Task: Fix auth bug in auth/login.py
Oracle: auth/login.py
Candidate: auth/login.py, static/css/styles.css, README.md
→ Sprawl = 2, CI fails with clear message
```

## Output Formats

### Human-Readable (default)

```
Patch Fidelity Metrics
==================================================
Fidelity Score (F1):     0.857
Recall:                  1.000
Precision:               0.750
Bloat (1-precision):     0.250
Sprawl (extra files):    0
Unrelated hunks:         0

Oracle lines changed:    2
Candidate lines changed: 4
Matched lines:           2
```

### JSON

```json
{
  "fidelity": 0.857,
  "recall": 1.0,
  "precision": 0.75,
  "bloat": 0.25,
  "sprawl": 0,
  "unrelated_hunks": 0,
  "oracle_line_count": 2,
  "candidate_line_count": 4,
  "matched_line_count": 2
}
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=patch_fidelity_meter --cov-report=term-missing

# Run specific test file
pytest tests/test_scoring.py -v
```

## Requirements

- Python 3.11 or higher
- No external dependencies (stdlib only)

## Testing

The test suite includes:

- **Unit tests** for diff parsing (`test_parser.py`)
- **Unit tests** for scoring logic (`test_scoring.py`)
- **Integration tests** for CLI (`test_cli.py`)
- **Example-based tests** using fixture files (`test_examples.py`)

Run with `pytest` or `python -m pytest`.

## Implementation Details

### Line Matching

Changed lines are compared as exact string matches. A changed line is any line starting with `+` or `-` (excluding file markers `+++` and `---`).

### Hunk Overlap Detection

Two hunks overlap if:
1. They affect the same file, AND
2. Their line ranges overlap in either the old version OR the new version

Line range `[start, start+count)` overlaps with `[start2, start2+count2)` if:
- `start < start2 + count2` AND `start2 < start + count`

### Empty Patch Handling

When both patches are empty, all metrics return 1.0 (perfect score).

## License

MIT License - see [LICENSE](LICENSE) file.

## With failstrata

When integrated into [failstrata](https://github.com/your-org/failstrata) or cursor-audit-cycle workflows, use `patch-fidelity-meter` to score agent iterations automatically:

```bash
# In failstrata harness: score each attempt
patch-fidelity-meter score \
  --oracle "${ORACLE_PATCH}" \
  --candidate "${AGENT_OUTPUT_PATCH}" \
  --json > "${ATTEMPT_DIR}/fidelity.json"

# Surface bloat and sprawl in the failstrata summary
```

The tool outputs structured JSON that failstrata can aggregate across iterations, surfacing regressions in edit quality.

## Contributing

This is a minimal v0 implementation. Future improvements could include:

- Fuzzy line matching (e.g., ignoring whitespace)
- Weighted metrics (e.g., prioritize certain files)
- Hunk-level granularity scoring
- Support for other diff formats

## See Also

- [Unified diff format](https://en.wikipedia.org/wiki/Diff#Unified_format)
- [Git diff documentation](https://git-scm.com/docs/git-diff)
