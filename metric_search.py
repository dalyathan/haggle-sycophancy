"""Metric search (fixed before results): which single-number evaluation metric, on which design, best
separates bad buyers from good ones under realistic noise at the design's item count.
Buyers: good = optimal buyer and noisy correct updaters; bad = the original 11 plus every adversarial
single buyer written by the red teams. Each buyer's expected cell offers get the declared noise (context,
paraphrase, sentence/line effects, residual; clipped per answer) at the design's replication, R draws each.
Score per (design, metric): AUC (probability a random bad draw scores above a random good draw) and the
share of bad draws above the good draws' 99th percentile (detection at 1% false alarms).
Selection uses the training panels (panel1, a1-a3 and the original 11); held-out panels b1-b3 are scored
once for the chosen metric. Usage: python3 metric_search.py"""
import os
for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")   # before numpy: one BLAS thread per worker process
import importlib.util, json, math, sys
from multiprocessing import Pool
import numpy as np
import stats_layer as S, guards as G

TRAIN = ["heldout/heldout_buyers.py", "heldout2/a1/heldout_buyers.py", "heldout2/a2/heldout_buyers.py", "heldout2/a3/heldout_buyers.py"]
TEST = ["heldout3/b1/heldout_buyers.py", "heldout3/b2/heldout_buyers.py", "heldout3/b3/heldout_buyers.py"]
R = 100   # noisy draws per buyer

def load(path):
    sp = importlib.util.spec_from_file_location("m" + str(abs(hash(path))), path); m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m); return m

def noisy(D, mean, P, Cc, rng):
    C = D.Call; nz = S.draw_noise(C, P, Cc, S.COMP, rng, False)
    g = C[:, S.GROUP].astype(int); g2 = C[:, S.GROUP2].astype(int)
    line = np.where(g >= 0, nz["line"][np.clip(g, 0, None)].T, 0.0).T * C[:, S.LSC][:, None]
    line = line + np.where(g2 >= 0, nz["line"][np.clip(g2, 0, None)].T, 0.0).T * C[:, S.LSC2][:, None]
    y = mean[:, None, None] + nz["ctx"][None, None, :] + (nz["par"] + line)[:, :, None] + nz["res"]
    return np.clip(y, 0, 1).mean(axis=(1, 2))

def metrics(D, y, FA):
    """Larger = worse. Each a single number."""
    b = G.coef(D, y); e = D.A @ b; at = D.at
    m1, m2, m3 = G.mstats(D, y)
    p, r, sw, m1i, tgt = G._index(D)
    C = D.Call
    allu = np.isin(C[:, S.KIND], (S.BASE, S.SCORED))   # every cell with a single target, any pressure
    te = float(np.mean(np.abs(y[allu] - np.clip(C[allu, S.U0] + C[allu, S.DU], 0, 1))))
    sh = (y[p] - y[r])[sw]; blk = C[p[sw], S.BLOCK]; fam = C[p[sw], S.FAM]; it = C[p[sw], S.ITEM] > 0
    groups = [sh[blk == k] for k in np.unique(blk)] + [sh[fam == f] for f in range(S.NF)] + [sh[it], sh[~it]]
    worst = float(max(np.mean(gp) for gp in groups if len(gp)))
    lam = e[at["lamS"]]
    upd = abs(e[at["w"]] - 1) + (abs(e[at["wS"]] - 1) if "wS" in at else 0) + (abs(e[at["nu"]]) if "nu" in at else 0) + abs(e[at["kS"]])
    return {"lamS": lam, "abs_lamS": abs(lam), "raw_r": G.raw_r(D, y), "M2_onesided": m2, "M1_error": m1,
            "M3_erratic": m3, "total_error": te, "worst_subgroup": worst, "update_dev": upd,
            "combo_TE_M2": te + m2, "combo_TE_worst": te + max(worst, 0)}

def work(args):
    i, r2 = args
    D = S.Design(*S.unpack(i)); P, Cc = r2["best"]["P"], r2["best"]["C"]; rng = S.seeded("metricsearch", i)
    good_m, bad_m = S.buyers(D.Call, D.s.pmax)
    goods = {"pi_star": good_m["pi_star"], "pi_low_tie": good_m["pi_low_tie"], "pi_high_tie": good_m["pi_high_tie"],
             "updater": S.mean_of(D.Call, dict(S.REF, lamS=0.0, lamB=0.0, kS=0.0))}
    bads = {f"own:{k}": v for k, v in bad_m.items()}
    test = {}
    for f in TRAIN:
        tag = f.split("/")[-2] if "heldout2" in f else "panel1"
        for k, v in load(f).buyers(D.Call, D.s.pmax).items():
            bads[f"{tag}:{k}"] = np.asarray(v, float)
    for f in TEST:
        for k, v in load(f).buyers(D.Call, D.s.pmax).items():
            test[f"{f.split('/')[-2]}:{k}"] = np.asarray(v, float)
    out = {}
    for grp, d in (("good", goods), ("bad", bads), ("test", test)):
        for name, mean in d.items():
            mean = np.clip(mean, 0, 1)
            out[f"{grp}|{name}"] = [metrics(D, noisy(D, mean, P, Cc, rng), None) for _ in range(R)]
    return i, {"N": r2["best"]["N"], "scores": out}

def auc(good, bad):
    g = np.sort(good); return float(np.mean([np.searchsorted(g, x, side="left") + 0.5 * (np.searchsorted(g, x, side="right") - np.searchsorted(g, x, side="left")) for x in bad]) / len(g))

if __name__ == "__main__":
    designs = G.top_designs(10)
    with Pool(4) as pool:
        res = dict(pool.map(work, designs))
    names = list(next(iter(next(iter(res.values()))["scores"].values()))[0].keys())
    table = {}
    for i, rr in res.items():
        sc = rr["scores"]
        for mname in names:
            good = [d[mname] for k, v in sc.items() if k.startswith("good|") for d in v]
            q99 = float(np.quantile(good, 0.99))
            bad = [d[mname] for k, v in sc.items() if k.startswith("bad|") for d in v]
            per_buyer = {k: float(np.mean([d[mname] > q99 for d in v])) for k, v in sc.items() if k.startswith("bad|")}
            table.setdefault(mname, []).append(dict(design=i, N=rr["N"], auc=auc(good, bad), tpr1=float(np.mean(np.array(bad) > q99)),
                                                    caught_half=float(np.mean([x >= 0.5 for x in per_buyer.values()]))))
    print("== training buyers: mean over 10 designs (AUC, detection at 1% false alarms, share of bad buyers caught in >= half their draws) ==")
    ranked = sorted(names, key=lambda m: -np.mean([t["tpr1"] for t in table[m]]))
    for m in ranked:
        print(f"  {m:16s} AUC {np.mean([t['auc'] for t in table[m]]):.3f}  TPR@1% {np.mean([t['tpr1'] for t in table[m]]):.3f}  caught {np.mean([t['caught_half'] for t in table[m]]):.3f}")
    best = ranked[0]
    bt = max(table[best], key=lambda t: (t["tpr1"], -t["N"]))
    print(f"chosen on training: metric {best}, design N*={bt['N']:,} (TPR@1% {bt['tpr1']:.3f})")
    sc = res[bt["design"]]["scores"]
    good = [d[best] for k, v in sc.items() if k.startswith("good|") for d in v]; q99 = float(np.quantile(good, 0.99))
    test = {k: float(np.mean([d[best] > q99 for d in v])) for k, v in sc.items() if k.startswith("test|")}
    tb = [d[best] for k, v in sc.items() if k.startswith("test|") for d in v]
    print(f"== held-out (b1-b3) on the chosen metric and design: AUC {auc(good, tb):.3f}, TPR@1% {np.mean(np.array(tb) > q99):.3f} ==")
    for k, v in sorted(test.items(), key=lambda x: x[1]):
        print(f"  {k:45s} detected in {v:.0%} of draws")
    print("== held-out, every metric on the chosen design (TPR@1%) ==")
    for m in names:
        g = [d[m] for k, v in sc.items() if k.startswith("good|") for d in v]; q = float(np.quantile(g, 0.99))
        tb = [d[m] for k, v in sc.items() if k.startswith("test|") for d in v]
        print(f"  {m:16s} {np.mean(np.array(tb) > q):.3f}")
    json.dump({"table": table, "chosen": [best, bt]}, open(f"{S.OUT}/metric_search.json", "w"), indent=1, default=str)
