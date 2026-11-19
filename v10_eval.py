"""Score the v1.0 guards (guards.py): adversary files once, the original panel (must still be caught / clean),
and a simulated genuine improvement (how often a really improved steered model still passes everything).
Usage: python3 v10_eval.py [adversary_file ...]   (top 10 v0.9 designs)"""
import importlib.util, json, math, sys
from multiprocessing import Pool
import numpy as np
import stats_layer as S, guards as G

def load(path):
    sp = importlib.util.spec_from_file_location("adv" + str(abs(hash(path))), path); m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m); return m

def work(args):
    i, r2, files, reps = args
    D = S.Design(*S.unpack(i)); P, Cc = r2["best"]["P"], r2["best"]["C"]
    rng = S.seeded("v10eval", i)
    cal = G.Calib(D, P, Cc, r2, rng)
    out = {"single": {}, "pairs": {}, "own": {}, "power": {}}
    good, bad = S.buyers(D.Call, D.s.pmax)
    for n, y in list(bad.items()) + list(good.items()):
        out["own"][n] = G.flags_v10(D, np.clip(y, 0, 1), cal)
    for fpath in files:
        m = load(fpath); tag = fpath.split("/")[-3] if "heldout2" in fpath else "panel1"
        for n, y in m.buyers(D.Call, D.s.pmax).items():
            out["single"][f"{tag}:{n}"] = G.flags_v10(D, np.clip(np.asarray(y, float), 0, 1), cal)
        for n, (yb, ys) in m.steering_pairs(D.Call, D.s.pmax).items():
            res = G.steering_v10(D, cal, np.clip(np.asarray(yb, float), 0, 1), np.clip(np.asarray(ys, float), 0, 1))
            out["pairs"][f"{tag}:{n}"] = [k for k, v in res.items() if not v]
    # genuine improvement: REF base, steered lamS - 0.05, noisy, clipped fits (as the steering test)
    comp = S.COMP; prep = D.prep(P, Cc, comp)
    v, lvar = S.scales(P, Cc, comp, False)
    n_ctrl = max(1, int((D.Call[:, S.KIND] == S.CTRL).sum())); n_blk = len(set(D.Call[:, S.BLOCK]))
    n_sent = max(1, len(set(D.Call[D.Call[:, S.KIND] == S.CTRL, S.GROUP])))
    s_ctrl = math.sqrt(v / n_ctrl + v / n_blk + lvar / n_sent)
    inner = G.slope_mask(D.Call)
    steered = dict(S.REF, lamS=S.REF["lamS"] - S.H1_EFFECT)
    agg = {}
    for _ in range(reps):
        nb = S.draw_noise(D.Call, P, Cc, comp, rng, False)
        ns = S.pair(nb, S.draw_noise(D.Call, P, Cc, comp, rng, False), comp["rho"])
        yb = S.cell_means(D.Call, P, Cc, S.REF, nb); ys = S.cell_means(D.Call, P, Cc, steered, ns)
        bb, cb = D.fit_arm(yb[inner], prep); bs, cs = D.fit_arm(ys[inner], prep)
        res = G.steering_v10(D, cal, yb, ys, bb, bs, cb, cs, s_ctrl, math.sqrt(v))
        res["old_H1to4"] = all(res[k] for k in res if k in ("H1", "H4") or k in S.EQUIV)
        res["ALL"] = all(v_ for k, v_ in res.items() if k not in ("old_H1to4",))
        for k, v_ in res.items():
            agg[k] = agg.get(k, 0) + v_
    out["power"] = {k: v_ / reps for k, v_ in agg.items()}
    return i, out

if __name__ == "__main__":
    files = sys.argv[1:]; reps = 200
    jobs = [(i, r2, files, reps) for i, r2 in G.top_designs(10)]
    with Pool(4) as pool:
        res = pool.map(work, jobs)
    R = dict(res); json.dump(R, open(f"{S.OUT}/v10_eval.json", "w"), indent=1)
    nd = len(R); first = next(iter(R.values()))
    print(f"== own panel (designs where flagged / {nd}) ==")
    for n in first["own"]:
        print(f"  {n:22s} flagged in {sum(bool(R[i]['own'][n]) for i in R)}")
    print("== adversary single buyers: evades (no flag) in N designs ==")
    for n in first["single"]:
        ev = sum(not R[i]["single"][n] for i in R)
        fl = sorted({f for i in R for f in R[i]["single"][n]})
        print(f"  {n:45s} evades {ev}/{nd}  flags: {fl}")
    print("== adversary pairs: passes everything in N designs ==")
    for n in first["pairs"]:
        ps = sum(not R[i]["pairs"][n] for i in R)
        fl = sorted({f for i in R for f in R[i]["pairs"][n]})
        print(f"  {n:45s} passes {ps}/{nd}  failed: {fl}")
    print("== genuine improvement (Δλ = −0.05), pass rate per test, mean over designs ==")
    keys = first["power"].keys()
    print("  " + ", ".join(f"{k} {np.mean([R[i]['power'][k] for i in R]):.2f}" for k in keys))
