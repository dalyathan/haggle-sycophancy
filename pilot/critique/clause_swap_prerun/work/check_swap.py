"""Pre-run review check (no model): CS prompts differ from the RL2 prompts of the same cell only in the acceptance clause;
stored RL/RL2 rows match the prompts the current code builds; CS (W,C) prompts equal RL2 (C,C)-paraphrase prompts in the swapped part."""
import sys, os, json, difflib, hashlib
sys.path.insert(0, os.getcwd())
from pilot import clause_swap as CS, reason_ladder2 as R2, reason_ladder as R1
cs = CS.prompts(False)
rl2 = R2.prompts()
# all four conditions of RL2 (all cells), rebuilt
full = {}
for frame in ("third", "you"):
    for para in (0, 1):
        for base in ("L1", "L2"):
            rung = base + ("y" if frame == "you" else "")
            for p in R2.rung_prompts(rung, para, "all"):
                full[frame, para, rung, p["v"], p["c"]] = p
rows2 = [json.loads(l) for l in open("pilot/out/reason_ladder2.jsonl")]
rows1 = [json.loads(l) for l in open("pilot/out/reason_ladder.jsonl")]
# stored hashes (ladder.build hash, before ASK) match rebuilt
bad = 0
for r in rows2:
    p = full[r["frame"], r["para"], r["rung"], r["v"], r["c"]]
    bad += r["hash"] != p["hash"]
for r in rows1:
    p = full["third", 0, r["rung"], r["v"], r["c"]]
    bad += r["hash"] != p["hash"]
print("stored RL/RL2 hash mismatches vs rebuilt:", bad, "of", len(rows1) + len(rows2))
# hashes in ladder cover messages before ASK? check
import pilot.ladder as L
p = full["third", 0, "L1", 2, None]
print("RL2 hash covers instruction?", hashlib.sha1(json.dumps(p["messages"]).encode()).hexdigest()[:12] == p["hash"])
# diff each CS prompt with its same-wording RL2 prompt
kinds = set()
for p in cs:
    q = full[p["frame"], p["wording"], p["rung"], p["v"], p["c"]]
    assert p["messages"][1] == q["messages"][1], "user msg differs"
    a, b = q["messages"][0]["content"], p["messages"][0]["content"]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    ops = [(t, a[i1:i2], b[j1:j2]) for t, i1, i2, j1, j2 in sm.get_opcodes() if t != "equal"]
    kinds.add((p["rung"], p["wording"], str([(o[0], o[1], o[2]) for o in ops]) if p["rung"].startswith("L1") else len(ops)))
    # check swapped clause text equals other paraphrase's clause text
    other = full[p["frame"], 1 - p["wording"], p["rung"], p["v"], p["c"]]["messages"][0]["content"]
    oc = CS.CLAUSES[p["rung"].rstrip("y")][p["clause"]].format(c=p["c"], cn="coin" if p["c"] == 1 else "coins")
    assert oc in other and oc in b
    assert p["target"] == q["target"]
for k in sorted(kinds, key=str): print(k)
# are rows' targets, cells identical sets
print("CS cells per (frame,W):", {(f, w): sorted((p['rung'], p['v'], p['c']) for p in cs if p['frame']==f and p['wording']==w) == sorted((k[2],k[3],k[4]) for k in full if k[0]==f and k[1]==w) for f in ('third','you') for w in (0,1)})
# rows needed in each RL2 cell for scorer
from collections import Counter
print(Counter((r["frame"], r["para"]) for r in rows2), len(rows1))
print("RL rows keys:", sorted(rows1[0].keys()))
print("RL2 rows 'frame' present in RL?", "frame" in rows1[0])
print("cut_off defs:", [ (r['n_new'], r['cut_off']) for r in rows1+rows2 if r['cut_off']][:12])
print("max n_new", max(r['n_new'] for r in rows1+rows2))
# strict: undoing the swap restores the RL2 system message exactly, for all 80 prompts
n = 0
for p in cs:
    q = full[p["frame"], p["wording"], p["rung"], p["v"], p["c"]]
    cn = "coin" if p["c"] == 1 else "coins"
    own = CS.CLAUSES[p["rung"].rstrip("y")][p["wording"]].format(c=p["c"], cn=cn)
    new = CS.CLAUSES[p["rung"].rstrip("y")][p["clause"]].format(c=p["c"], cn=cn)
    assert p["messages"][0]["content"].replace(new, own) == q["messages"][0]["content"] and p["messages"][1] == q["messages"][1]
    n += 1
print("strict round-trip ok:", n)
sb = CS.prompts(True)
ok = all(p["messages"] == full[p["frame"], 0, p["rung"], p["v"], p["c"]]["messages"] for p in sb)
print("part B prompts identical to RL/RL2 W0C0 prompts:", ok, len(sb))
