#!/bin/bash
# After RL2 and TM: continue the R5 generations (R5b).
cd "$(dirname "$0")/.."
while pgrep -f run_queue2.sh >/dev/null; do sleep 30; done
/home/user/sycophancy-steering/.venv/bin/python pilot/r5_continue.py >> pilot/out/reason_probe_R5b.log 2>&1
