import pickle, numpy as np
from collections import defaultdict
ALL = pickle.load(open("work/all.pkl", "rb"))
def verdict(R, pol, R3b=None, pol3b=None):
    rung = R[0]["rung"]; by = defaultdict(list)
    for r in R: by[(r["v"], r["c"], bool(r["hist"]))].append(r)
    Q = {k: pol(rs[0]) for k, rs in by.items()}
    best = lambda r: max(max(r["U"]), 0)
    tm = np.mean([Q[k][rs[0]["target"]].sum() for k, rs in by.items()])
    rg = np.mean([best(rs[0]) - Q[k][1:] @ np.array(rs[0]["U"]) for k, rs in by.items()])
    un = np.mean([best(rs[0]) - np.mean([0] + rs[0]["U"]) for rs in by.values()]); five = np.mean([best(rs[0]) - rs[0]["U"][4] for rs in by.values()])
    ok = tm >= 0.5 and rg <= un / 2 and rg < five
    eo = {k: (np.arange(1, 10) @ q[1:]) / q[1:].sum() for k, q in Q.items()}
    if rung.startswith("L2"):
        con = [np.mean([Q[k][0] for k in Q if k[0] == v and k[1] > v]) - np.mean([Q[k][0] for k in Q if k[0] == v and k[1] < v]) for v in (2, 6)]
        tc = [k for k in Q if k[1] < k[0]]; sl = np.polyfit([k[1] for k in tc], [eo[k] for k in tc], 1)[0]
        ok = ok and min(con) >= 0.5 and sl >= 0.5
    if rung == "L3":
        d = []
        for v in (14, 18):
            q = pol3b([r for r in R3b if r["v"] == v][0]); d.append(eo[(v, None, False)] - (np.arange(1, 10) @ q[1:]) / q[1:].sum())
        ok = ok and min(d) >= 1.5
    return ok
def noisy(s, pick=min):
    def pol(r):
        q = np.zeros(10); t = r["target"]; q[t] = 1 / len(t); return (1 - s) * q + s / 10
    return pol
def half(r):
    q = np.zeros(10); q[min(9, max(1, round(r["v"] / 2 + 1e-9)))] = 1; return q
def copyc(r):
    q = np.zeros(10); q[0 if r["v"] == 2 else r["c"]] = 1; return q
for s in (0, .2, .3, .4, .5, .6, 1.0):
    print(s, {g: bool(verdict(ALL[g], noisy(s), ALL["L3b"], noisy(s))) for g in ("L1", "L2", "L3", "L3b", "L3c", "L4", "L4b")})
print("half", {g: bool(verdict(ALL[g], half, ALL["L3b"], half)) for g in ("L1", "L3", "L3b", "L4")})
print("copy", verdict(ALL["L2"], copyc))
# modal policy seen: L1 min(v-1,9)
def modal(r):
    q = np.zeros(10); q[min(r["v"] - 1, 9)] = 1; return q
by = {}
for r in ALL["L1"]: by[r["v"]] = r
print("L1 regret of min(v-1,9):", np.mean([max(r["U"]) - r["U"][min(r["v"] - 1, 9) - 1] for r in by.values()]))
