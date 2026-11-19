import os
for k in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS"): os.environ[k]="1"
import json, sys
sys.path.insert(0, os.getcwd())
import numpy as np
from collections import defaultdict, Counter
R = [json.loads(l) for l in open("pilot/out/pilot_4b.jsonl")]
for r in R:
    r["P"] = np.array(r["probs"]); 
Y = {(r["cell"], r["ctx"], r["para"]): r for r in R}
cells = {}
for r in R: cells.setdefault(r["cell"], r)
BASE, SCORED, TIED, CTRL, CTRLINFO = 0, 1, 2, 4, 5
