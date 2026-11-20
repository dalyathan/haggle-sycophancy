#!/bin/bash
# Run the reasoning ladder once the current chain (ladder rungs, then the R5 probe) has finished.
cd "$(dirname "$0")/.."
while pgrep -f run_ladder_rest.sh >/dev/null; do sleep 30; done
/home/user/sycophancy-steering/.venv/bin/python pilot/reason_ladder.py > pilot/out/reason_ladder.log 2>&1
