import pickle, numpy as np
from collections import defaultdict, Counter
ALL = pickle.load(open("work/all.pkl", "rb"))
def qn(r):
    q = np.array(r["probs"], float); return q / q.sum()
print("== L1/L1y: per v: two-digit prob after '1', argmax counts, mass on 1 / v-1 / v(capped 9) / 9 / walk")
for g in ("L1", "L1y"):
    for v in (2, 6, 10, 14, 18):
        rs = [r for r in ALL[g] if r["v"] == v]; q = np.mean([qn(r) for r in rs], 0)
        print(g, v, "two-digit", round(np.mean([r["p_two_digit_after_1"] for r in rs]), 3), "argmax", dict(Counter(int(np.argmax(qn(r))) for r in rs)),
              "by para mass on 1:", [round(np.mean([qn(r)[1] for r in rs if r["para"] == p]), 2) for p in (0, 1)],
              "mass>=v:", round(q[min(v, 10):].sum(), 2) if v < 10 else "-", "P9", round(q[9], 2))
print("== L2/L2y by cell class")
for g in ("L2", "L2y"):
    R = ALL[g]
    def agg(sel, name):
        rs = [r for r in R if sel(r)]
        cost = np.mean([qn(r)[r["c"]] for r in rs]); walk = np.mean([qn(r)[0] for r in rs])
        vecho = np.mean([qn(r)[r["v"]] if r["v"] <= 9 and r["v"] != r["c"] else np.nan for r in rs])
        one = np.mean([qn(r)[1] for r in rs if r["c"] != 1] or [np.nan]); nine = np.mean([qn(r)[9] for r in rs if r["c"] != 9] or [np.nan])
        below = np.mean([qn(r)[1:r["c"]].sum() for r in rs]); above = np.mean([qn(r)[r["c"] + 1:].sum() for r in rs])
        am = Counter()
        for r in rs:
            a = int(np.argmax(qn(r))); am["cost" if a == r["c"] else "walk" if a == 0 else "value" if a == r["v"] else "other"] += 1
        print(f"  {g} {name:28} n={len(rs):3} cost {cost:.2f} walk {walk:.2f} value-digit {vecho:.2f} P1(c!=1) {one:.2f} P9(c!=9) {nine:.2f} below-cost {below:.2f} above-cost {above:.2f} argmax {dict(am)}")
    agg(lambda r: r["c"] < r["v"], "trade cells (c<v)")
    agg(lambda r: r["c"] < r["v"] and r["c"] == 1, " trade, c=1")
    agg(lambda r: r["c"] < r["v"] and r["c"] > 1, " trade, c>1")
    agg(lambda r: r["c"] > r["v"], "walk cells (c>v)")
    agg(lambda r: r["c"] > r["v"] and r["v"] == 2, " walk, v=2")
    agg(lambda r: r["c"] > r["v"] and r["v"] == 6, " walk, v=6")
    for p in (0, 1):
        agg(lambda r: r["c"] > r["v"] and r["para"] == p, f" walk cells para {p}")
        agg(lambda r: r["c"] < r["v"] and r["para"] == p, f" trade cells para {p}")
    # regret decomposition in trade cells: where does regret come from
    tr = [r for r in R if r["c"] < r["v"]]
    tot = np.mean([max(r["U"]) - qn(r)[1:] @ np.array(r["U"]) for r in tr])
    parts = dict(walk=np.mean([qn(r)[0] * max(r["U"]) for r in tr]), below=np.mean([qn(r)[1:r["c"]].sum() * max(r["U"]) for r in tr]),
                 above=np.mean([sum(qn(r)[a] * (max(r["U"]) - r["U"][a - 1]) for a in range(r["c"] + 1, 10)) for r in tr]))
    wk = [r for r in R if r["c"] > r["v"]]
    print(f"  {g} regret trade cells {tot:.2f}: " + ", ".join(f"{k} {x:.2f}" for k, x in parts.items()) + f"; walk cells regret {np.mean([-(qn(r)[1:] @ np.array(r['U'])) for r in wk]):.2f}"
          f"; share of total regret from v>=10: {sum(max(max(r['U']),0) - qn(r)[1:] @ np.array(r['U']) for r in R if r['v']>=10)/sum(max(max(r['U']),0) - qn(r)[1:] @ np.array(r['U']) for r in R):.2f}")
    # normalised regret per cell (regret / best payoff) in trade cells
    print(f"  {g} mean regret/best in trade cells: {np.mean([(max(r['U']) - qn(r)[1:] @ np.array(r['U']))/max(r['U']) for r in tr]):.2f}; "
          f"L2 c=1 mass on 1 by v: {[round(np.mean([qn(r)[1] for r in R if r['c']==1 and r['v']==v]),2) for v in (2,6,10,14,18)]}")
print("== L1 vs L2(c=1): mass on 1 by v")
for a, b in (("L1", "L2"), ("L1y", "L2y")):
    print(a, [round(np.mean([qn(r)[1] for r in ALL[a] if r["v"] == v]), 2) for v in (2, 6, 10, 14, 18)], b, "c=1",
          [round(np.mean([qn(r)[1] for r in ALL[b] if r["v"] == v and r["c"] == 1]), 2) for v in (2, 6, 10, 14, 18)])
print("== mean distributions pooled over v>=10, no history")
for g in ("L1", "L1y", "L3", "L3b", "L3c", "L4", "L4b"):
    print(g, np.round(np.mean([qn(r) for r in ALL[g] if r["v"] >= 10 and not r["hist"]], 0), 2), "hist:", np.round(np.mean([qn(r) for r in ALL[g] if r["v"] >= 10 and r["hist"]] or [np.zeros(10)], 0), 2))
print("== slope of exp_offer on v (coins per coin), no history; optimal slope")
for g in ("L1", "L1y", "L3", "L3b", "L3c", "L4", "L4b"):
    rs = [r for r in ALL[g] if not r["hist"]]
    print(g, round(np.polyfit([r["v"] for r in rs], [r["exp_offer"] for r in rs], 1)[0], 3), "target slope", round(np.polyfit([r["v"] for r in rs], [np.mean([a for a in r["target"]]) for r in rs], 1)[0], 3))
print("== history effects by paraphrase (exp_offer hist - nohist), v=6,10,14")
for g in ("L3", "L3c", "L4", "L4b"):
    for p in (0, 1):
        print(g, p, [round(np.mean([r["exp_offer"] for r in ALL[g] if r["v"] == v and r["hist"] and r["para"] == p]) - np.mean([r["exp_offer"] for r in ALL[g] if r["v"] == v and not r["hist"] and r["para"] == p]), 2) for v in (6, 10, 14, 18)],
              "P(1) nohist->hist", round(np.mean([qn(r)[1] for r in ALL[g] if not r["hist"] and r["para"] == p]), 2), round(np.mean([qn(r)[1] for r in ALL[g] if r["hist"] and r["para"] == p]), 2),
              "P(2)", round(np.mean([qn(r)[2] for r in ALL[g] if not r["hist"] and r["para"] == p]), 2), round(np.mean([qn(r)[2] for r in ALL[g] if r["hist"] and r["para"] == p]), 2))
