"""Analysis of the game ladder (pilot/LADDER.md). Usage: python pilot/analyze_ladder.py pilot/out/ladder_L1.jsonl [...]
Also accepts pilot/out/readout_R3.jsonl (the third-person full game; baseline rows only)."""
import json, os, sys, warnings
from collections import defaultdict
import numpy as np
warnings.filterwarnings("ignore", category=RuntimeWarning)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def qn(r):
    q = np.asarray(r["probs"], float); return q / q.sum()


def pay(r, q=None):
    q = qn(r) if q is None else q
    return float(sum(q[a] * r["U"][a - 1] for a in range(1, 10)))


def best(r):
    return max(max(r["U"]), 0.0)


def load(path):
    R = [json.loads(l) for l in open(path)]
    if "rung" not in R[0]:          # readout R3: the third-person full game
        from pilot.analyze_readout import load as rload
        R = [dict(r, rung="L4", c=None) for r in rload(path) if r["kind"] == "base"]
    return R


def cell_key(r):
    return (r["v"], r["c"], bool(r["hist"]))


def report(path):
    R = load(path); rung = R[0]["rung"]
    by = defaultdict(list)
    for r in R:
        by[cell_key(r)].append(r)
    print(f"== {path}: rung {rung}, {len(R)} prompts, {len(by)} cells ==")
    res = {}
    cov = np.median([r["coverage"] for r in R])
    res["P1"] = (f"coverage median {cov:.4f} (>= 0.9)", cov >= 0.9)
    tm = np.mean([sum(qn(r)[a] for a in r["target"]) for r in R])
    res["P2"] = (f"mass on the kernel target {tm:.3f} (>= 0.4)", tm >= 0.4)
    reg = np.mean([np.mean([best(r) - pay(r) for r in rs]) for rs in by.values()])
    unif = np.mean([best(rs[0]) - pay(rs[0], np.ones(10) / 10) for rs in by.values()])
    five = np.mean([best(rs[0]) - rs[0]["U"][4] for rs in by.values()])
    res["P3"] = (f"regret {reg:.3f} coins (<= half the uniform guess {unif:.3f}, and < always-5 {five:.3f})", reg <= unif / 2 and reg < five)
    eo = {k: np.mean([r["exp_offer"] for r in rs]) for k, rs in by.items()}
    wk = {k: np.mean([qn(r)[0] for r in rs]) for k, rs in by.items()}
    if rung == "L1":
        lose = np.mean([sum(qn(r)[a] for a in range(r["v"], 10)) for r in R if r["v"] <= 9])
        res["P4"] = (f"mass on offers at or above the value (v = 2, 6) {lose:.3f} (<= 0.1)", lose <= 0.1)
    elif rung == "L2":
        wc = [k for k in by if k[1] > k[0]]; tc = [k for k in by if k[1] < k[0]]
        w = np.mean([wk[k] for k in wc])
        sl = float(np.polyfit([k[1] for k in tc], [eo[k] for k in tc], 1)[0])
        copy = np.mean([np.mean([qn(r)[k[1]] for r in by[k]]) for k in wc])
        res["P4"] = (f"walk mass where the cost exceeds the value {w:.3f} (>= 0.5); slope of the offer on the cost where it is below "
                     f"{sl:.3f} (>= 0.5); [reported: mass on the stated cost where walking is optimal {copy:.3f}]", w >= 0.5 and sl >= 0.5)
    elif rung == "L3":
        un = [k for k in by if not k[2]]
        tgt = {k: by[k][0]["target"][0] for k in un}
        sl = float(np.polyfit([tgt[k] for k in un], [eo[k] for k in un], 1)[0])
        hd = [eo[(v, None, True)] - eo[(v, None, False)] for v in (6, 10, 14)]
        res["P4"] = (f"slope of the offer on the optimum (no history) {sl:.3f} (>= 0.5); history effect at v = 6, 10, 14: "
                     f"{', '.join(f'{x:+.2f}' for x in hd)} (optimal about +0.5 each; mean > 0)", sl >= 0.5 and np.mean(hd) > 0)
    else:   # L4 (third person, readout R3) and L4b (second person): the readout rule's baseline criteria A1-A6
        from pilot.analyze_readout import acceptance
        a, _ = acceptance([dict(r, kind="base", u0=((r["target"][0] - 1) / 8 if len(r["target"]) == 1 and r["target"][0] else None))
                           for r in R])
        for k in ("A2", "A4", "A5", "A6"):
            res[k] = a[k]
    for k, (t, ok) in res.items():
        print(f"{k} {t}  {'pass' if ok else 'FAIL'}")
    ok = all(v[1] for v in res.values())
    print(f"VERDICT {rung}: " + ("PASS" if ok else "FAIL on " + ", ".join(k for k, v in res.items() if not v[1])))
    print("cells: v, cost, history, target | mean distribution over (walk, 1..9) | exp_offer | regret")
    for k in sorted(by, key=lambda k: (k[0], k[1] or 0, k[2])):
        rs = by[k]; q = np.mean([qn(r) for r in rs], 0)
        print(f"   v={k[0]:>2} c={k[1] if k[1] else '-'} h={int(k[2])} t={rs[0]['target']} | " + " ".join(f"{x:.2f}" for x in q) +
              f" | {eo[k]:.2f} | {np.mean([best(r) - pay(r) for r in rs]):.2f}")
    pd = np.mean([r["exp_offer"] for r in R if r["para"] == 1]) - np.mean([r["exp_offer"] for r in R if r["para"] == 0])
    print(f"paraphrase 1 minus 0 (exp_offer, coins): {pd:+.3f}")
    return ok


if __name__ == "__main__":
    out = {p: report(p) for p in sys.argv[1:]}
    if len(out) > 1:
        print("\nsummary:", {os.path.basename(k): ("PASS" if v else "FAIL") for k, v in out.items()})
