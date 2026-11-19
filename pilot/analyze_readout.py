"""Analysis of the readout pilot (pilot/READOUT.md). Usage: python pilot/analyze_readout.py out/readout_R0.jsonl [more files]"""
import json, sys
from collections import defaultdict
import numpy as np

STAGEB = "pilot/out/pilot_4b.jsonl"


def load(path):
    return [json.loads(l) for l in open(path)]


def rank(x):
    """Average ranks (ties share the mean rank)."""
    x = np.asarray(x, float); o = np.argsort(x, kind="mergesort"); r = np.empty(len(x)); r[o] = np.arange(len(x))
    for v in np.unique(x):
        m = x == v; r[m] = r[m].mean()
    return r


def spearman(a, b):
    ra, rb = rank(a), rank(b)
    return float(np.corrcoef(ra, rb)[0, 1])


def qn(r):
    q = np.asarray(r["probs"], float); return q / q.sum()


def pay(r, q=None):
    q = qn(r) if q is None else q
    return float(sum(q[a] * r["U"][a - 1] for a in range(1, 10)))          # walking pays 0


def best_pay(r):
    return max(max(r["U"]), 0.0)


def rule_regret(r, a):
    return best_pay(r) - r["U"][a - 1]


def value_only(v):
    return int(min(9, max(1, round(v / 2))))


def acceptance(R):
    B = [r for r in R if r["kind"] == "base"]
    cov = np.array([r["coverage"] for r in B])
    sd = np.array([r["sd_offer"] for r in B])
    ends = np.array([(qn(r)[1] + qn(r)[9]) / max(qn(r)[1:].sum(), 1e-12) for r in B])
    opt = np.array([sum(qn(r)[a] for a in r["best"]) + (qn(r)[0] if r["walk_optimal"] else 0) for r in B])
    byb = defaultdict(list)
    for r in B:
        byb[r["block"]].append(r)
    reg, reg5, regv, eu, u0 = [], [], [], [], []
    for b, rs in sorted(byb.items()):
        reg.append(np.mean([best_pay(r) - pay(r) for r in rs]))
        reg5.append(rule_regret(rs[0], 5)); regv.append(rule_regret(rs[0], value_only(rs[0]["v"])))
        if rs[0]["u0"] is not None:
            eu.append(np.mean([r["exp_u"] for r in rs])); u0.append(rs[0]["u0"])
    reg, reg5, regv = map(np.mean, (reg, reg5, regv))
    rho = spearman(eu, u0); slope = float(np.polyfit(u0, eu, 1)[0])
    res = dict(A1=(np.median(cov), np.median(cov) >= 0.9),
               A2=((np.median(sd), np.median(ends)), np.median(sd) < 2.0 and np.median(ends) < 0.4),
               A3=(opt.mean(), opt.mean() > 0.10),
               A4=((reg, reg5, regv), reg < reg5 and reg < regv),
               A5=((rho, slope), rho >= 0.5 and slope >= 0.5))
    return res, all(v[1] for v in res.values()), byb


def report(path):
    R = load(path); V = R[0]["variant"]
    print(f"== {path}: variant {V}, {len(R)} prompts{' (fresh contexts)' if R[0].get('fresh') else ''} ==")
    res, ok, byb = acceptance(R)
    a = res
    print(f"A1 coverage median {a['A1'][0]:.4f}  {'pass' if a['A1'][1] else 'FAIL'}")
    print(f"A2 offer SD median {a['A2'][0][0]:.2f} coins (< 2.0), end mass median {a['A2'][0][1]:.3f} (< 0.4)  {'pass' if a['A2'][1] else 'FAIL'}")
    print(f"A3 mass on the optimum {a['A3'][0]:.3f} (> 0.10)  {'pass' if a['A3'][1] else 'FAIL'}")
    print(f"A4 regret (coins) model {a['A4'][0][0]:.3f} vs always-5 {a['A4'][0][1]:.3f}, value-only {a['A4'][0][2]:.3f}  {'pass' if a['A4'][1] else 'FAIL'}")
    print(f"A5 Spearman {a['A5'][0][0]:.3f} (>= 0.5), slope {a['A5'][0][1]:.3f} (>= 0.5)  {'pass' if a['A5'][1] else 'FAIL'}")
    print(f"VERDICT {V}: {'PASS' if ok else 'FAIL'}")
    print("baseline option distribution by block (walk, 1..9), mean over contexts and paraphrases:")
    for b, rs in sorted(byb.items()):
        q = np.mean([qn(r) for r in rs], 0); r0 = rs[0]
        print(f"   v={r0['v']:>2} hist={int(r0['hist'])} best={r0['best']}: " + " ".join(f"{x:.2f}" for x in q) +
              f"  exp_offer {np.mean([r['exp_offer'] for r in rs]):.2f}")
    allq = np.mean([qn(r) for r in R], 0)
    print("all prompts, mean distribution: " + " ".join(f"{x:.2f}" for x in allq))
    if V == "R4":
        return ok
    # number copying
    ir = defaultdict(list); nu = defaultdict(list)
    for r in R:
        key = (r["block"], r["ctx"], r["para"])
        if r["kind"] == "irrelevant":
            ir[key].append(qn(r))
        elif r["kind"] == "number":
            nu[(key, r["remark"])].append(qn(r))
    for d in (3, 7):
        dd = [nu[(k, d)][0][d] - np.mean([x[d] for x in ir[k]]) for k in ir if (k, d) in nu]
        print(f"number copying: P({d}) with a remark containing {d} minus irrelevant remarks: {np.mean(dd):+.4f} (SE {np.std(dd, ddof=1) / np.sqrt(len(dd)):.4f}, n={len(dd)})")
    # updating
    base = {(r["block"], r["ctx"], r["para"]): r for r in R if r["kind"] == "base"}
    by_item = defaultdict(list)
    for r in R:
        if r["kind"] == "info":
            b = base[(r["block"], r["ctx"], r["para"])]
            du = None if (r["u_star"] is None or b["u0"] is None) else r["u_star"] - b["u0"]
            by_item[tuple(r["item"])].append((du, r["exp_u"] - b["exp_u"], r["walk"] - b["walk"], r["walk_optimal"],
                                               best_pay(r) - pay(r)))
    print("updating by item (mean shift in exp_u; mean optimal move; within-item slope; walk shift; regret):")
    for it, xs in sorted(by_item.items()):
        d = [x for x in xs if x[0] is not None]
        sl = float(np.polyfit([x[0] for x in d], [x[1] for x in d], 1)[0]) if len({x[0] for x in d}) > 1 else float("nan")
        print(f"   {str(it):38s} shift {np.mean([x[1] for x in xs]):+.3f}  du* {np.mean([x[0] for x in d]) if d else float('nan'):+.3f}  "
              f"slope {sl:+.3f}  walk {np.mean([x[2] for x in xs]):+.3f}  walk-optimal {np.mean([x[3] for x in xs]):.2f}  regret {np.mean([x[4] for x in xs]):.2f}  n={len(xs)}")
    allreg = [best_pay(r) - pay(r) for r in R if r["kind"] == "info"]
    print(f"information cells: mean regret {np.mean(allreg):.3f} coins")
    # paraphrase / order
    pd = [np.mean([r["exp_u"] for r in rs if r["para"] == 1]) - np.mean([r["exp_u"] for r in rs if r["para"] == 0]) for rs in byb.values()]
    print(f"paraphrase 1 minus 0 on baselines (exp_u): {np.mean(pd):+.4f}" + ("  [R2: options in opposite orders]" if V == "R2" else ""))
    if V == "R0":
        check_r0(R)
    return ok


def check_r0(R):
    """Fast path vs the stored stage-B outputs on the prompts the two runs share."""
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from pilot import run_pilot as RP
    from pilot import readout as RO
    RO.VARIANT = "R0"; RO.FRESH = False
    new = RO.build()
    old = RP.build()
    stored = [json.loads(l) for l in open(STAGEB)]
    key = lambda p: (p["messages"][0]["content"], p["messages"][1]["content"])
    oi = {key(p): i for i, p in enumerate(old)}
    dp, de = [], []
    for i, p in enumerate(new[:len(R)]):
        j = oi.get(key(p))
        if j is not None and j < len(stored):
            dp.append(np.abs(np.asarray(R[i]["probs"]) - np.asarray(stored[j]["probs"])).max())
            de.append(R[i]["exp_u"] - stored[j]["exp_u"])
    if dp:
        print(f"R0 fast path vs stored stage-B outputs on {len(dp)} shared prompts: max abs prob diff {max(dp):.4f}, "
              f"exp_u difference mean {np.mean(de):+.4f} SD {np.std(de):.4f} max |.| {np.max(np.abs(de)):.4f}")


if __name__ == "__main__":
    out = {}
    for p in sys.argv[1:]:
        out[p] = report(p); print()
    if len(out) > 1:
        print("summary:", {k: ("PASS" if v else "FAIL") for k, v in out.items()})
