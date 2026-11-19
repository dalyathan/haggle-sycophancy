"""Summarize a capability_check results file: python analyze.py results_2b.jsonl"""
import json, sys
from statistics import mean

rows = [json.loads(l) for l in open(sys.argv[1] if len(sys.argv) > 1 else "results_2b.jsonl")]
by = lambda task, V: [r for r in rows if r["task"] == task and r["V"] == V]

cov = [r["coverage"] for r in rows]
print(f"prompts {len(rows)}   coverage mean {mean(cov):.3f}  min {min(cov):.3f}   "
      f"mass on 6-9 mean {mean(r['mass_6_9'] for r in rows):.3f}")

print("\nexpected offer [argmax counts 1-5] | P(price < V)")
print(f"{'V':>2} | {'opening':>24} | {'neutral':>24} | {'bad news':>24}")
for V in range(2, 7):
    cells = []
    for task in ("opening", "neutral", "bad_news"):
        rs = by(task, V)
        if not rs:
            cells.append(f"{'-':>24}")
            continue
        e = mean(r["expected"] for r in rs)
        plo = mean(sum(r["dist"][:V - 1]) for r in rs)
        am = [sum(r["argmax"] == k for r in rs) for k in range(1, 6)]
        cells.append(f"{e:4.2f} {am} {plo:4.2f}")
    print(f"{V:>2} | " + " | ".join(cells))

neu = {(r["V"], r["pair"], r["opening"]): r["expected"] for r in rows if r["task"] == "neutral"}
bad = {(r["V"], r["pair"], r["opening"]): r["expected"] for r in rows if r["task"] == "bad_news"}
diffs = [bad[k] - neu[k] for k in neu]
print(f"\nbad news - neutral (paired, n={len(diffs)}): mean {mean(diffs):+.3f}, "
      f"lower in {sum(d < 0 for d in diffs)}/{len(diffs)}, higher in {sum(d > 0 for d in diffs)}")
for V in range(3, 7):
    dv = [bad[k] - neu[k] for k in neu if k[0] == V]
    print(f"  V={V}: mean {mean(dv):+.3f}, lower {sum(d < 0 for d in dv)}/{len(dv)}")

s = [r["seconds"] for r in rows]
print(f"\nseconds/prompt mean {mean(s):.2f} (first {s[0]:.2f}), tokens/prompt mean "
      f"{mean(r['n_tokens'] for r in rows):.0f}")
