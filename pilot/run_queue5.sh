#!/bin/bash
# After the clause-swap queue (run_queue4.sh): reproducibility check of reused RL/RL2 cells (CS review R3).
cd "$(dirname "$0")/.."
while pgrep -f run_queue4.sh >/dev/null; do sleep 60; done
/home/user/sycophancy-steering/.venv/bin/python pilot/repro_check.py > pilot/out/repro_check.log 2>&1
