#!/bin/bash
# Resume the queued runs (each resumes from its output file): ladder L3c and L4b on the exact path, the reasoning ladder, the R5 probe.
cd "$(dirname "$0")/.."
PY=/home/user/sycophancy-steering/.venv/bin/python
for r in L3c L4b; do
  FULL=1 $PY pilot/ladder.py $r >> pilot/out/ladder_$r.log 2>&1 || exit 1
done
$PY pilot/reason_ladder.py >> pilot/out/reason_ladder.log 2>&1
$PY pilot/reason_probe.py >> pilot/out/reason_probe_R5.log 2>&1
