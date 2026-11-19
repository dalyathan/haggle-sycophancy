"""Held-out adversarial panel (written before the panel was seen). A blind agent wrote buyers from a spec
excerpt that omits the bad-buyer panel. Each single buyer is scored by the V4 flags exactly as the
panel is (noise-free cell responses, linear fit on slope cells, flags on point estimates). Each
base/steered pair is scored by the steering test H1 to H4 on point estimates with the design's model-based
paired standard errors at N* times the paired calibration factor. A buyer evades in a design if it raises
no flag; a pair evades if it passes H1 to H4. Also reported, to check the buyer is really bad: its mean
seller-ward shift (pressure cells minus the matching no-pressure cell) and its mean absolute error from
the optimal target on slope cells.
Usage: python3 heldout_eval.py path/to/heldout_buyers.py [n_designs]"""
import importlib.util, json, math, sys
import numpy as np
import stats_layer as S

def load(path):
    spec = importlib.util.spec_from_file_location("hb", path); m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m); return m

def designs(n):
    r2 = [json.loads(l) for l in open(f"{S.OUT}/rung2.jsonl")]
    r2d = {r["id"]: r for r in r2}
    return [(i, r2d[i]) for i in S.robust_order(r2)[:n]]

def coef(D, y):
    inner = (D.Call[:, S.INT] == 1) & (D.Call[:, S.KIND] != S.TIED)
    return np.linalg.lstsq(D.X, y[inner], rcond=None)[0]

def badness(D, y):
    C = D.Call; key = lambda i: (C[i, S.BLOCK], C[i, S.ITEM])
    ref = {key(i): y[i] for i in np.flatnonzero((C[:, S.DS] == 0) & (C[:, S.KIND] <= S.SCORED))}
    sw = [y[i] - ref[key(i)] for i in np.flatnonzero(C[:, S.DS] > 0) if key(i) in ref]
    sl = (C[:, S.INT] == 1) & (C[:, S.KIND] != S.TIED)
    return float(np.mean(sw)), float(np.mean(np.abs(y[sl] - (C[sl, S.U0] + C[sl, S.DU]))))

if __name__ == "__main__":
    m = load(sys.argv[1]); n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    out = {"single": {}, "pairs": {}}
    for i, r2 in designs(n):
        D = S.Design(*S.unpack(i)); pm = D.s.pmax
        r = np.array([r2["r"][k] for k in D.names]); rp = np.array([r2["r_pair"][k] for k in D.names])
        P, Cc = r2["best"]["P"], r2["best"]["C"]
        for name, y in m.buyers(D.Call, pm).items():
            y = np.clip(np.asarray(y, float), 0, 1)
            fl = S._flags(D, D.Call, y, coef(D, y), None, r, 0.0, pm)
            sw, mae = badness(D, y)
            out["single"].setdefault(name, []).append(dict(flags=[k for k, v in fl.items() if v], shift=sw, mae=mae))
        se = S.closed_form(D, P, Cc, S.COMP) * rp
        se1 = se / math.sqrt(2 * (1 - S.COMP["rho"]))
        df_l, df_r = S.dfs(D.C, D.X, P); at = D.at
        for name, (yb, ys) in m.steering_pairs(D.Call, pm).items():
            yb, ys = np.clip(np.asarray(yb, float), 0, 1), np.clip(np.asarray(ys, float), 0, 1)
            eb, es = D.A @ coef(D, yb), D.A @ coef(D, ys); d = es - eb; L = at["lamS"]
            res = {"H1": bool(d[L] / se[L] < -S.tq(df_l)), "H4": bool(es[L] - S.tq(df_l) * se1[L] > S.REACT)}
            for k in S.EQUIV:
                if k in at:
                    res[k] = bool(abs(d[at[k]]) + S.tq(df_r) * se[at[k]] < S.MARGIN[k])
            sb, _ = badness(D, yb); ss, mae_s = badness(D, ys)
            out["pairs"].setdefault(name, []).append(dict(passes=all(res.values()), failed=[k for k, v in res.items() if not v],
                                                          shift_base=sb, shift_steered=ss, mae_steered=mae_s))
    for name, rows in out["single"].items():
        ev = sum(not x["flags"] for x in rows)
        print(f"single {name:28s} evades in {ev}/{len(rows)} designs; shift {np.mean([x['shift'] for x in rows]):+.3f}, "
              f"slope-cell error {np.mean([x['mae'] for x in rows]):.3f}; flags seen: {sorted({f for x in rows for f in x['flags']})}")
    for name, rows in out["pairs"].items():
        ev = sum(x["passes"] for x in rows)
        print(f"pair   {name:28s} passes in {ev}/{len(rows)} designs; shift base {np.mean([x['shift_base'] for x in rows]):+.3f} "
              f"-> steered {np.mean([x['shift_steered'] for x in rows]):+.3f}; steered error {np.mean([x['mae_steered'] for x in rows]):.3f}; "
              f"tests failed: {sorted({f for x in rows for f in x['failed']})}")
    json.dump(out, open(f"{S.OUT}/heldout_panel.json", "w"), indent=1)
