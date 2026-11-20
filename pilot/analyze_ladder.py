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
    res = {}; rep = []
    cov = np.median([r["coverage"] for r in R])
    res["P1"] = (f"coverage median {cov:.4f} (>= 0.9)", cov >= 0.9)
    tm = np.mean([sum(qn(r)[a] for a in r["target"]) for r in R])
    res["P2"] = (f"mass on the kernel target {tm:.3f} (>= 0.5)", tm >= 0.5)
    reg = np.mean([np.mean([best(r) - pay(r) for r in rs]) for rs in by.values()])
    unif = np.mean([best(rs[0]) - pay(rs[0], np.ones(10) / 10) for rs in by.values()])
    five = np.mean([best(rs[0]) - rs[0]["U"][4] for rs in by.values()])
    res["P3"] = (f"regret {reg:.3f} coins (<= {unif / 2:.3f}, half a uniform guess over the ten answers; and < always-5 {five:.3f})",
                 reg <= unif / 2 and reg < five)
    eo = {k: np.mean([r["exp_offer"] for r in rs]) for k, rs in by.items()}
    wk = {k: np.mean([qn(r)[0] for r in rs]) for k, rs in by.items()}
    base = rung.rstrip("y") if rung != "L4b" else "L4b"
    if base == "L1":
        rep.append(f"mass on offers at or above the value (v = 2, 6): {np.mean([sum(qn(r)[a] for a in range(r['v'], 10)) for r in R if r['v'] <= 6]):.3f}")
    elif base == "L2":
        con = {}
        for v in (2, 6):
            above = [wk[k] for k in by if k[0] == v and k[1] > v]; below = [wk[k] for k in by if k[0] == v and k[1] < v]
            con[v] = np.mean(above) - np.mean(below)
        tc = [k for k in by if k[1] < k[0]]
        sl = float(np.polyfit([k[1] for k in tc], [eo[k] for k in tc], 1)[0])
        res["P4"] = (f"walk contrast (cost above minus below the value) at v = 2: {con[2]:+.3f}, v = 6: {con[6]:+.3f} (each >= 0.5); "
                     f"slope of the offer on the cost where it is below the value {sl:.3f} (>= 0.5)", min(con.values()) >= 0.5 and sl >= 0.5)
        wc = [k for k in by if k[1] > k[0]]
        rep.append(f"mass on the stated cost where walking is optimal {np.mean([np.mean([qn(r)[k[1]] for r in by[k]]) for k in wc]):.3f}; "
                   f"rejected low offers (pay 0) there {np.mean([np.mean([qn(r)[1:k[1]].sum() for r in by[k]]) for k in wc]):.3f}")
    elif base in ("L3", "L3c"):
        hd = [eo[(v, None, True)] - eo[(v, None, False)] for v in (6, 10, 14)]
        rep.append(f"history effect at v = 6, 10, 14: {', '.join(f'{x:+.2f}' for x in hd)} coins (optimal 0 or +1: ties)")
        if base == "L3":
            other = os.path.join(os.path.dirname(path), os.path.basename(path).replace("ladder_L3", "ladder_L3b"))
            if os.path.exists(other):
                eb = defaultdict(list)
                for r in load(other):
                    eb[r["v"]].append(r["exp_offer"])
                d = {v: eo[(v, None, False)] - np.mean(eb[v]) for v in (14, 18)}
                res["P4"] = (f"offer with cost uniform on 1..8 minus on 1..4 (L3b) at v = 14: {d[14]:+.2f}, v = 18: {d[18]:+.2f} coins "
                             f"(optimal +3, +4; each >= 1.5)", min(d.values()) >= 1.5)
            else:
                res["P4"] = ("L3b output missing: cannot test", False)
    elif base in ("L4", "L4b"):
        from pilot.analyze_readout import acceptance
        a, _ = acceptance([dict(r, kind="base", u0=((r["target"][0] - 1) / 8 if len(r["target"]) == 1 and r["target"][0] else None))
                           for r in R])
        for k in ("A2", "A4", "A5", "A6"):
            rep.append(f"{k} {a[k][0]}  {'pass' if a[k][1] else 'fail'}")
        if base == "L4b":
            r3 = os.path.join(os.path.dirname(path), "readout_R3.jsonl")
            if os.path.exists(r3):
                L4 = {(r["v"], bool(r["hist"]), r["ctx"], r["para"]): best(r) - pay(r) for r in load(r3)}
                dd = defaultdict(list)
                for r in R:
                    dd[(r["ctx"], r["para"])].append((best(r) - pay(r)) - L4[(r["v"], bool(r["hist"]), r["ctx"], r["para"])])
                m = [np.mean(x) for x in dd.values()]
                rep.append(f"regret, second minus third person (paired by cell): {np.mean(m):+.3f} coins, range over the six "
                           f"context x paraphrase sets {min(m):+.3f} to {max(m):+.3f}")
    nt = [sum(qn(r)[a] for a in (0, 1, 9) if a not in r["target"]) for r in R]
    rep.append(f"mass on 0, 1, 9 where they are not targets: {np.mean(nt):.3f}")
    for pp in (0, 1):
        Rp = [r for r in R if r["para"] == pp]
        rp = np.mean([best(r) - pay(r) for r in Rp]); tp = np.mean([sum(qn(r)[a] for a in r["target"]) for r in Rp])
        rep.append(f"paraphrase {pp}: regret {rp:.3f}, target mass {tp:.3f}")
    for k, (t, ok) in res.items():
        print(f"{k} {t}  {'pass' if ok else 'FAIL'}")
    ok = all(v[1] for v in res.values())
    print(f"VERDICT {rung}: " + ("PASS" if ok else "FAIL on " + ", ".join(k for k, v in res.items() if not v[1])))
    for x in rep:
        print("  reported: " + x)
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
