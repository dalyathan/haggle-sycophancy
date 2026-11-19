"""Reviewer rerun of metric_search.work with extras. Run from repo/ dir."""
import os, sys, json
for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
sys.path.insert(0, ".")
import numpy as np
from multiprocessing import Pool
import stats_layer as S, guards as G, metric_search as M

def work(args):
    i, r2 = args
    D = S.Design(*S.unpack(i)); P, Cc = r2["best"]["P"], r2["best"]["C"]; rng = S.seeded("metricsearch", i)
    good_m, bad_m = S.buyers(D.Call, D.s.pmax)
    goods = {"pi_star": good_m["pi_star"], "pi_low_tie": good_m["pi_low_tie"], "pi_high_tie": good_m["pi_high_tie"],
             "updater": S.mean_of(D.Call, dict(S.REF, lamS=0.0, lamB=0.0, kS=0.0))}
    bads = {f"own:{k}": v for k, v in bad_m.items()}
    test = {}
    for f in M.TRAIN:
        tag = f.split("/")[-2] if "heldout2" in f else "panel1"
        for k, v in M.load(f).buyers(D.Call, D.s.pmax).items():
            bads[f"{tag}:{k}"] = np.asarray(v, float)
    for f in M.TEST:
        for k, v in M.load(f).buyers(D.Call, D.s.pmax).items():
            test[f"{f.split('/')[-2]}:{k}"] = np.asarray(v, float)
    out = {}; means = {}
    for grp, d in (("good", goods), ("bad", bads), ("test", test)):
        for name, mean in d.items():
            mean = np.clip(mean, 0, 1); means[f"{grp}|{name}"] = mean
            out[f"{grp}|{name}"] = [M.metrics(D, M.noisy(D, mean, P, Cc, rng), None) for _ in range(M.R)]
    # ---- reviewer extras, separate rng so the above reproduces the original exactly
    rng2 = np.random.default_rng(abs(hash(i)) % (2**32) + 7)
    rng2 = np.random.default_rng(int.from_bytes(__import__("hashlib").sha256(("rev" + str(i)).encode()).digest()[:8], "little"))
    C = D.Call
    Z = dict(S.REF, lamS=0.0, lamB=0.0, kS=0.0)
    extra = {
        "good_level+0.02": S.mean_of(C, dict(Z, a0=0.02)),
        "good_level+0.03": S.mean_of(C, dict(Z, a0=0.03)),
        "good_w0.9": S.mean_of(C, dict(Z, w=0.9)),
        "good_a1_0.95": S.mean_of(C, dict(Z, a1=0.95, a0=0.025)),
        "REF_base(lamS.10)": S.mean_of(C, S.REF),
        "REF_steered(lamS.05)": S.mean_of(C, dict(S.REF, lamS=0.05)),
        "syc_0.02_uniform": S.mean_of(C, dict(Z, lamS=0.02)),
        "syc_0.04_uniform": S.mean_of(C, dict(Z, lamS=0.04)),
    }
    ex = {}
    for name, mean in extra.items():
        mean = np.clip(mean, 0, 1)
        ex[name] = [M.metrics(D, M.noisy(D, mean, P, Cc, rng2), None) for _ in range(M.R)]
    # optimal buyer with a different residual noise level
    for sg in (0.06, 0.10, 0.12):
        old = S.COMP["sig_e"]; S.COMP["sig_e"] = sg
        ex[f"optimal_sig_e={sg}"] = [M.metrics(D, M.noisy(D, np.clip(good_m["pi_star"], 0, 1), P, Cc, rng2), None) for _ in range(M.R)]
        S.COMP["sig_e"] = old
    # ---- oracle matched filter: lower bound on the best possible (Neyman-Pearson) detection
    NG = 1000
    g0 = np.clip(good_m["pi_star"], 0, 1)
    use = C[:, S.KIND] != S.TIED   # tied cells: the good set differs there, leave them out of the oracle
    Yg = np.array([M.noisy(D, g0, P, Cc, rng2) for _ in range(NG)])
    mu_g = Yg.mean(0); sd = Yg.std(0, ddof=1)
    oracle = {}
    for key, mean in means.items():
        if key.startswith("good|"): continue
        Yb = np.array([M.noisy(D, mean, P, Cc, rng2) for _ in range(100)])
        # template: noise-free mean difference (known to the oracle), common mode removed (context shift)
        d = (mean - g0) * use
        res = {}
        for tag, w in (("plain", d / sd**2), ("centred", (d - d[use].mean() * use) / sd**2)):
            tg = (Yg[NG//2:] - mu_g) @ w   # threshold from the second half; mu_g, sd from all (mild)
            tb = (Yb - mu_g) @ w
            res[tag] = float(np.mean(tb > np.quantile(tg, 0.99)))
        res["L1dev"] = float(np.mean(np.abs(mean - g0)[use])); res["maxdev"] = float(np.max(np.abs(mean - g0)[use]))
        oracle[key] = res
    return i, {"N": r2["best"]["N"], "P": P, "C": Cc, "ncell": int(len(C)), "scores": out, "extra": ex, "oracle": oracle}

if __name__ == "__main__":
    designs = G.top_designs(10)
    with Pool(4) as pool:
        res = dict(pool.map(work, designs))
    json.dump(res, open(sys.argv[1], "w"))
