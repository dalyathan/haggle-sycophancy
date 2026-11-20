#!/bin/bash
# Remaining ladder rungs on the exact path (LADDER.md v2.1), then resume the R5 reasoning probe.
cd "$(dirname "$0")/.."
PY=/home/user/sycophancy-steering/.venv/bin/python
for r in L2 L2y L3 L3b L3c L4b; do
  FULL=1 $PY pilot/ladder.py $r > pilot/out/ladder_$r.log 2>&1 || exit 1
done
$PY pilot/reason_probe.py >> pilot/out/reason_probe_R5.log 2>&1
