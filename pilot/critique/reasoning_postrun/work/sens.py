"""Sensitivity: regret by condition with cut-offs read three ways; Wilson intervals; paraphrase/framing contrasts."""
import json, math
from collections import defaultdict
D = "/home/user/haggle-sycophancy/pilot/out/"
rows = [json.loads(l) | {"frame": "third"} for l in open(D + "reason_ladder.jsonl")] + [json.loads(l) for l in open(D + "reason_ladder2.jsonl")]
def pay(r, a):
    if a == 0 or a > 9: return 0.0
    return r["U"][a - 1]
def best(r): return max(0.0, max(r["U"]))
def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (c - h) / d, (c + h) / d
by = defaultdict(list)
for r in rows: by[(r["frame"], r["para"])].append(r)
print("condition | correct | Wilson 95% | answered | correct|answered | regret cut=walk | regret cut=forced argmax | regret cut=worst")
for k in sorted(by):
    rs = by[k]
    ok = sum(1 for r in rs if r["written_answer"] is not None and r["written_answer"] in r["target"])
    ans = [r for r in rs if r["written_answer"] is not None]
    oka = sum(1 for r in ans if r["written_answer"] in r["target"])
    am = lambda r: max(range(10), key=lambda i: r["probs"][i])
    reg_w = sum(best(r) - (pay(r, r["written_answer"]) if r["written_answer"] is not None else 0) for r in rs) / len(rs)
    reg_f = sum(best(r) - pay(r, r["written_answer"] if r["written_answer"] is not None else am(r)) for r in rs) / len(rs)
    reg_x = sum(best(r) - (pay(r, r["written_answer"]) if r["written_answer"] is not None else min(0, min(r["U"]))) for r in rs) / len(rs)
    lo, hi = wilson(ok, len(rs))
    okf = sum(1 for r in rs if (r["written_answer"] if r["written_answer"] is not None else am(r)) in r["target"])
    print(k, ok, f"[{lo:.2f}, {hi:.2f}]", len(ans), f"{oka}/{len(ans)}", f"{reg_w:.2f}", f"{reg_f:.2f}", f"{reg_x:.2f}", "| correct if cut read by forced argmax:", okf)
# reference policies on the same 20 cells
cells = by[("third", 0)]
for name, pol in [("always 1", lambda r: 1), ("copy cost (1 in L1), never walk", lambda r: r["c"] or 1),
                  ("uniform over walk,1..9", None)]:
    if pol:
        print(name, "correct", sum(pol(r) in r["target"] for r in cells), "regret %.2f" % (sum(best(r) - pay(r, pol(r)) for r in cells) / 20))
    else:
        print(name, "regret %.2f" % (sum(best(r) - sum(pay(r, a) for a in range(10)) / 10 for r in cells) / 20))
# Fisher exact, paraphrase 0 vs 1 pooled over framing
from math import comb
def fisher(a, b, c, d):
    n = a + b + c + d; r1 = a + b; c1 = a + c
    p0 = comb(r1, a) * comb(n - r1, c1 - a) / comb(n, c1)
    return sum(comb(r1, x) * comb(n - r1, c1 - x) / comb(n, c1) for x in range(max(0, c1 - (n - r1)), min(r1, c1) + 1)
               if comb(r1, x) * comb(n - r1, c1 - x) / comb(n, c1) <= p0 + 1e-12)
print("paraphrase 0 vs 1 (pooled): 36/40 vs 21/40, Fisher two-sided p = %.4f" % fisher(36, 4, 21, 19))
print("third vs second person (pooled): %d/40 vs %d/40" % (19 + 10, 17 + 11), "p = %.3f" % fisher(29, 11, 28, 12))
