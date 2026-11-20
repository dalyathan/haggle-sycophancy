"""Independent recomputation of the ladder: own kernel (no import of kernel.py / analyze_ladder.py)."""
import json, sys
from fractions import Fraction as Fr
from collections import defaultdict
import numpy as np
D = "pilot/out/"
def rows(name):
    return [json.loads(l) for l in open(D + name)]
def belief(rung, c, hist):
    base = rung.rstrip("y") if rung != "L4b" else "L4"
    if base == "L1": b = [(lambda a: True, Fr(1))]
    elif base == "L2": b = [(lambda a, c=c: a >= c, Fr(1))]
    elif base in ("L3", "L3b", "L3c"):
        top = 4 if base == "L3b" else 8
        b = [((lambda a, k=k: a >= k), Fr(1, top)) for k in range(1, top + 1)]
    else:
        b = [((lambda a, k=k: a >= k), Fr(7, 80)) for k in range(1, 9)] + [(lambda a: True, Fr(15, 100)), (lambda a: a >= 4, Fr(15, 100))]
    if hist:
        b = [(f, p) for f, p in b if not f(1)]; z = sum(p for _, p in b); b = [(f, p / z) for f, p in b]
    return b
def kern(rung, v, c, hist):
    b = belief(rung, c, hist)
    acc = {a: sum(p for f, p in b if f(a)) for a in range(1, 10)}
    U = {a: (v - a) * acc[a] for a in range(1, 10)}
    m = max(U.values())
    if m < 0: T = [0]
    else:
        T = sorted(a for a in U if U[a] == m)
        if m == 0: T = [0] + T
        offers = [a for a in T if a]
        if offers and all(acc[a] == 0 for a in offers): T = [0]
    return [float(U[a]) for a in range(1, 10)], T
def qn(r):
    q = np.array(r["probs"], float); return q / q.sum()
def reg(r, q=None):
    q = qn(r) if q is None else q
    return max(max(r["U"]), 0) - float(q[1:] @ np.array(r["U"]))
def load(name):
    R = rows(name)
    if name.startswith("readout"):
        R = [dict(r, rung="L4", c=None) for r in R if r["kind"] == "base"]
    return R
FILES = ["ladder_L1.jsonl", "ladder_L1y.jsonl", "ladder_L2.jsonl", "ladder_L2y.jsonl", "ladder_L3.jsonl", "ladder_L3b.jsonl",
         "ladder_L3c.jsonl", "readout_R3.jsonl", "ladder_L4b.jsonl"]
ALL = {}
for f in FILES:
    R = load(f); rung = R[0]["rung"]; ALL[rung] = R
    bad = 0; badq = 0
    for r in R:
        U, T = kern(rung, r["v"], r["c"], bool(r["hist"]))
        if not np.allclose(U, r["U"], atol=1e-9) or T != r["target"]:
            bad += 1
            if bad <= 3: print("  MISMATCH", rung, r["v"], r["c"], r["hist"], T, r["target"], U, r["U"])
        q = qn(r); off = q[1:] / q[1:].sum(); eo = float(np.arange(1, 10) @ off)
        if abs(eo - r["exp_offer"]) > 1e-6 or abs(sum(r["probs"]) - r["coverage"]) > 1e-9: badq += 1
    by = defaultdict(list)
    for r in R: by[(r["v"], r["c"], bool(r["hist"]))].append(r)
    n_cp = defaultdict(int)
    for r in R: n_cp[(r["ctx"], r["para"])] += 1
    cov = np.median([r["coverage"] for r in R]); covmin = min(r["coverage"] for r in R)
    tm = np.mean([qn(r)[r["target"]].sum() for r in R])
    rg = np.mean([np.mean([reg(r) for r in rs]) for rs in by.values()])
    un = np.mean([reg(rs[0], np.ones(10) / 10) for rs in by.values()])
    five = np.mean([max(max(rs[0]["U"]), 0) - rs[0]["U"][4] for rs in by.values()])
    # payoff-equivalent target mass (all answers with the max payoff, walking = 0)
    def pe(r):
        pay = np.array([0.0] + r["U"]); return qn(r)[pay >= pay.max() - 1e-12].sum()
    pem = np.mean([pe(r) for r in R])
    am = np.mean([int(np.argmax(qn(r))) in r["target"] for r in R])
    # bootstrap over prompts within cells
    rng = np.random.default_rng(0); bs = []
    for _ in range(2000):
        bs.append(np.mean([np.mean(rng.choice([reg(r) for r in rs], len(rs))) for rs in by.values()]))
    sets = defaultdict(list)
    for r in R: sets[(r["ctx"], r["para"])].append(r)
    sreg = {k: np.mean([reg(r) for r in rs]) for k, rs in sorted(sets.items())}
    stm = {k: np.mean([qn(r)[r["target"]].sum() for r in rs]) for k, rs in sorted(sets.items())}
    print(f"{rung:4} n={len(R)} cells={len(by)} sets={dict(n_cp) and len(n_cp)} kernel-mismatch={bad} summary-mismatch={badq} | P1 cov med {cov:.4f} min {covmin:.3f} | "
          f"P2 target {tm:.3f} (payoff-equivalent {pem:.3f}; argmax on target {am:.2f}) | P3 regret {rg:.3f} [boot {np.percentile(bs,2.5):.2f},{np.percentile(bs,97.5):.2f}] "
          f"thr {un/2:.3f} always5 {five:.3f} uniform {un:.3f} ratio {rg/un:.2f}")
    print("      per set regret:", " ".join(f"{x:.2f}" for x in sreg.values()), "| target mass:", " ".join(f"{x:.2f}" for x in stm.values()))
    if rung in ("L2", "L2y"):
        wk = {k: np.mean([qn(r)[0] for r in rs]) for k, rs in by.items()}
        eo = {k: np.mean([r["exp_offer"] for r in rs]) for k, rs in by.items()}
        for v in (2, 6):
            print(f"      walk contrast v={v}: {np.mean([wk[k] for k in by if k[0]==v and k[1]>v]) - np.mean([wk[k] for k in by if k[0]==v and k[1]<v]):+.3f}")
        tc = [k for k in by if k[1] < k[0]]
        print(f"      slope {np.polyfit([k[1] for k in tc], [eo[k] for k in tc], 1)[0]:.3f}")
        for s, rs in sorted(sets.items()):
            b2 = defaultdict(list)
            for r in rs: b2[(r['v'], r['c'])].append(qn(r)[0])
            con = [np.mean([np.mean(b2[k]) for k in b2 if k[0]==v and k[1]>v]) - np.mean([np.mean(b2[k]) for k in b2 if k[0]==v and k[1]<v]) for v in (2,6)]
            print(f"        set {s}: walk contrast {con[0]:+.2f} {con[1]:+.2f}")
# L3 P4
for a, b in (("L3", "L3b"),):
    for v in (14, 18):
        x = np.mean([r["exp_offer"] for r in ALL[a] if r["v"] == v and not r["hist"]]); y = np.mean([r["exp_offer"] for r in ALL[b] if r["v"] == v])
        print(f"L3 P4 v={v}: {x - y:+.2f}")
    for v in (14, 18):
        for p in (0, 1):
            x = np.mean([r["exp_offer"] for r in ALL[a] if r["v"] == v and not r["hist"] and r["para"] == p]); y = np.mean([r["exp_offer"] for r in ALL[b] if r["v"] == v and r["para"] == p])
            print(f"   para {p} v={v}: {x - y:+.2f}")
    print("  L3 no-hist mass on 8:", np.round([np.mean([qn(r)[8] for r in ALL['L3'] if r['v']==v and not r['hist']]) for v in (2,6,10,14,18)],2), " on 4:", np.round([np.mean([qn(r)[4] for r in ALL['L3'] if r['v']==v and not r['hist']]) for v in (2,6,10,14,18)],2))
    print("  L3b mass on 8:", np.round([np.mean([qn(r)[8] for r in ALL['L3b'] if r['v']==v]) for v in (2,6,10,14,18)],2), " on 4:", np.round([np.mean([qn(r)[4] for r in ALL['L3b'] if r['v']==v]) for v in (2,6,10,14,18)],2))
# paired framing differences
def paired(a, b):
    A = {(r["v"], r["c"], bool(r["hist"]), r["ctx"], r["para"]): r for r in ALL[a]}
    d = defaultdict(list); dt = []; dw = []
    for r in ALL[b]:
        o = A[(r["v"], r["c"], bool(r["hist"]), r["ctx"], r["para"])]
        d[(r["ctx"], r["para"])].append(reg(r) - reg(o)); dt.append(qn(r)[r["target"]].sum() - qn(o)[o["target"]].sum()); dw.append(qn(r)[0] - qn(o)[0])
    m = [np.mean(x) for k, x in sorted(d.items())]
    allv = np.concatenate([x for x in d.values()])
    rng = np.random.default_rng(1)
    bs = [np.mean(rng.choice(allv, len(allv))) for _ in range(4000)]
    print(f"{b} minus {a}: regret {np.mean(m):+.3f} (sets {' '.join(f'{x:+.3f}' for x in m)}); prompt-bootstrap 95% [{np.percentile(bs,2.5):+.3f},{np.percentile(bs,97.5):+.3f}]; "
          f"share of prompts improved {np.mean(allv<0):.2f}; target mass {np.mean(dt):+.3f}; walk mass {np.mean(dw):+.3f}")
paired("L4", "L4b"); paired("L1", "L1y"); paired("L2", "L2y"); paired("L3", "L3c")
import pickle; pickle.dump(ALL, open("work/all.pkl", "wb"))
