"""Merge share outputs into the rung's main file, keeping the first line per design id.
Usage: python3 merge.py rung2|rung3"""
import glob, json, sys
import stats_layer as S
stage = sys.argv[1]; main = f"{S.OUT}/{stage}.jsonl"
seen, out = set(), []
for f in [main] + sorted(glob.glob(f"{S.OUT}/{stage}_part*.jsonl")):
    try:
        lines = open(f).read().splitlines()
    except FileNotFoundError:
        continue
    for l in lines:
        if l.strip() and json.loads(l)["id"] not in seen:
            seen.add(json.loads(l)["id"]); out.append(l + "\n")
open(main, "w").writelines(out); print(f"{stage}: {len(out)} designs merged")
