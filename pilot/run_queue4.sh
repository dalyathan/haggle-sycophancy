#!/bin/bash
# Clause-swap test: part A (greedy, 80 prompts), then part B (3 sampled answers, 40 prompts).
cd "$(dirname "$0")/.."
PY=/home/user/sycophancy-steering/.venv/bin/python
$PY pilot/clause_swap.py > pilot/out/clause_swap.log 2>&1
SAMPLE=1 $PY pilot/clause_swap.py > pilot/out/clause_swap_sampled.log 2>&1
