import sys, os, json
sys.path.insert(0, "/home/user/haggle-sycophancy")
os.chdir("/home/user/haggle-sycophancy")
from pilot import reason_ladder2 as R
P = R.prompts()
print(len(P))
for p in P:
    if p["rung"].startswith("L2") and p["v"] == 10 and p["c"] == 7 or (p["rung"].startswith("L1") and p["v"] == 10):
        print("=====", p["frame"], p["para"], p["rung"], p["target"])
        print(p["messages"][0]["content"]); print("--- USER"); print(p["messages"][1]["content"])
# check hashes against the jsonl
rows = [json.loads(l) for l in open("pilot/out/reason_ladder2.jsonl")]
print("hash match", all(r["hash"] == p["hash"] for r, p in zip(rows, P)), len(rows), len(P))
