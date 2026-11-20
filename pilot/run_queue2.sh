#!/bin/bash
# After the current queue (L3c, L4b, RL, R5): the RL2 robustness extension, then the thinking-mode probe. Each resumes from its file.
cd "$(dirname "$0")/.."
while pgrep -f run_queue.sh >/dev/null; do sleep 30; done
PY=/home/user/sycophancy-steering/.venv/bin/python
$PY pilot/reason_ladder2.py >> pilot/out/reason_ladder2.log 2>&1
$PY pilot/think_probe.py >> pilot/out/think_probe.log 2>&1
