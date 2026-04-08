#!/bin/bash
# reproduce.sh — Full reproduction of Memory Poisoning Persistence Bounds experiments
#
# Usage: bash reproduce.sh
# Requirements: Python 3.10+, pip
# Expected runtime: ~5-10 minutes on commodity hardware
# Expected outputs: outputs/experiments/e0_results.json through e5_*.json + summary.json

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Memory Poisoning Persistence Bounds — Reproduction ==="
echo "Date: $(date -Iseconds)"
echo ""

# Check lock_commit
grep -q "lock_commit.*TO BE SET\|lock_commit.*PENDING" EXPERIMENTAL_DESIGN.md && echo "FAIL: lock_commit not set" && exit 1
echo "PASS: lock_commit is set"

# Install dependencies
echo ""
echo "--- Installing dependencies ---"
pip install -e ".[dev]" --quiet 2>&1 | tail -1
echo "Dependencies installed."

# Run tests
echo ""
echo "--- Running tests ---"
python -m pytest tests/ -v --tb=short 2>&1
TEST_EXIT=$?
if [ $TEST_EXIT -ne 0 ]; then
    echo "FAIL: Tests failed with exit code $TEST_EXIT"
    exit $TEST_EXIT
fi
echo "PASS: All tests passed."

# Run experiments
echo ""
echo "--- Running experiments ---"
python -c "
from src.experiments import run_all_experiments
results = run_all_experiments('outputs/experiments')
"
EXPERIMENT_EXIT=$?
if [ $EXPERIMENT_EXIT -ne 0 ]; then
    echo "FAIL: Experiments failed with exit code $EXPERIMENT_EXIT"
    exit $EXPERIMENT_EXIT
fi

# Verify outputs exist
echo ""
echo "--- Verifying outputs ---"
EXPECTED_FILES=(
    "outputs/experiments/e0_results.json"
    "outputs/experiments/e1_architecture_comparison.json"
    "outputs/experiments/e2_p0_threshold.json"
    "outputs/experiments/e3_parameter_importance.json"
    "outputs/experiments/e4_cross_domain_transfer.json"
    "outputs/experiments/e5_consolidation_amplification.json"
    "outputs/experiments/summary.json"
)

MISSING=0
for f in "${EXPECTED_FILES[@]}"; do
    if [ -f "$f" ]; then
        echo "  PASS: $f exists ($(wc -c < "$f") bytes)"
    else
        echo "  FAIL: $f missing"
        MISSING=$((MISSING+1))
    fi
done

if [ $MISSING -gt 0 ]; then
    echo "FAIL: $MISSING expected output files missing"
    exit 1
fi

# Print summary
echo ""
echo "--- Summary ---"
python -c "
import json
with open('outputs/experiments/summary.json') as f:
    summary = json.load(f)
for k, v in summary.items():
    print(f'  {k}: {v}')
"

echo ""
echo "=== Reproduction complete ==="
