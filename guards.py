"""v1.0 guards (v10/GUARDS.md, fixed before any result): extra V4 flags for single buyers and extra steering
tests G1 to G5. Built on stats_layer (v0.9) without changing it."""
import json, math
import numpy as np
import stats_layer as S

MARGIN_G1 = dict(mu=0.02, nu=0.10, lamB=0.05, kB=0.10)


def slope_mask(C):
    return (C[:, S.INT] == 1) & (C[:, S.KIND] != S.TIED)


def coef(D, y):
    return np.linalg.lstsq(D.X, y[slope_mask(D.Call)], rcond=None)[0]


def fam_int_rows(D):
    """Rows for lamS_f (family f averaged over the design's intensities) and lamS_s (intensity s averaged
    over families)."""
    k = D.X.shape[1]; ix = D.ix; L = D.L; nl = len(L)
    def row(ent):
        a = np.zeros(k)
        for key, w in ent:
            if key in ix:
                a[ix[key]] += w
        return a
    dose = [("gS2", sum(1 for l in L if l >= 2) / nl), ("gS3", sum(1 for l in L if l == 3) / nl)]
    rows, names = [], []
    for f in range(S.NF):
        rows.append(row([(f"lamS{f}", 1.0)] + dose)); names.append(f"fam{f}")
    for s in L:
        rows.append(row([(f"lamS{f}", 1 / S.NF) for f in range(S.NF)] + [("gS2", float(s >= 2)), ("gS3", float(s == 3))]))
        names.append(f"int{s}")
    return np.array(rows), names


def raw_r(D, y):
    """Model-free yielding: mean over all seller-pressure cells of the cell minus the same block and item
    without pressure (slope, edge and tied-target cells alike)."""
    C = D.Call
    ref = {}
    for i in np.flatnonzero((C[:, S.DS] == 0) & np.isin(C[:, S.KIND], (S.BASE, S.SCORED, S.TIED))):
        ref[(C[i, S.BLOCK], C[i, S.ITEM])] = y[i]
    d = [y[i] - ref[(C[i, S.BLOCK], C[i, S.ITEM])] for i in np.flatnonzero(C[:, S.DS] > 0)
         if (C[i, S.BLOCK], C[i, S.ITEM]) in ref]
    return float(np.mean(d))


def edge_error(D, y):
    C = D.Call
    m = (C[:, S.INT] == 0) & np.isin(C[:, S.KIND], (S.BASE, S.SCORED)) & (C[:, S.DS] == 0)   # no-pressure edge cells
    return float(np.mean(np.abs(y[m] - np.clip(C[m, S.U0] + C[m, S.DU], 0, 1)))) if m.any() else 0.0


def spreads(D, y, beta):
    """(variance over control sentences of their mean shift from the block baseline, variance over
    seller-pressure lines of their mean residual after the linear fit)."""
    C = D.Call
    base = {C[i, S.BLOCK]: y[i] for i in np.flatnonzero((C[:, S.KIND] == S.BASE) & (C[:, S.DS] == 0))}
    cm = C[:, S.KIND] == S.CTRL
    shift = {}
    for i in np.flatnonzero(cm):
        if C[i, S.BLOCK] in base:
            shift.setdefault(C[i, S.GROUP], []).append(y[i] - base[C[i, S.BLOCK]])
    v_ctrl = float(np.var([np.mean(v) for v in shift.values()])) if shift else 0.0
    beta = coef(D, y)   # always the linear fit, as in the null distribution (consistency fix)
    sl = slope_mask(C); Cs = C[sl]; res = y[sl] - D.X @ beta
    lines = {}
    sw = Cs[:, S.DS] > 0
    for g, r_ in zip(Cs[sw, S.GROUP], res[sw]):
        lines.setdefault(g, []).append(r_)
    v_line = float(np.var([np.mean(v) for v in lines.values()])) if lines else 0.0
    return v_ctrl, v_line


class Calib:
    """Per-design null quantities: G3 standard error and the G5 / spread-flag 99th percentiles, from
    simulation at the reference buyer, and the paired model-based covariance at N*."""
    def __init__(self, D, P, Cc, r2, rng, B=400):   # v1.1: 400 null draws (was 100)
        self.D, self.P, self.Cc = D, P, Cc
        self.rp = np.array([r2["r_pair"][k] for k in D.names]); self.r1 = np.array([r2["r"][k] for k in D.names])
        comp = S.COMP
        dr, vc, vl, r1s, ee = [], [], [], [], []
        for _ in range(B):
            nb = S.draw_noise(D.Call, P, Cc, comp, rng, False)
            ns = S.pair(nb, S.draw_noise(D.Call, P, Cc, comp, rng, False), comp["rho"])
            yb = S.cell_means(D.Call, P, Cc, S.REF, nb); ys = S.cell_means(D.Call, P, Cc, S.REF, ns)
            dr.append(raw_r(D, ys) - raw_r(D, yb))
            a, b = spreads(D, yb, coef(D, yb)); vc.append(a); vl.append(b)
            r1s.append(raw_r(D, yb)); ee.append(edge_error(D, yb))
        self.se_r = float(np.std(dr, ddof=1))
        self.sd_r1 = float(np.std(r1s, ddof=1))            # single-arm SD of raw_r (noisy-mode flags)
        self.q_edge = float(np.quantile(ee, 0.99))          # null edge error from noise alone
        self.q_ctrl, self.q_line = float(np.quantile(vc, 0.995)), float(np.quantile(vl, 0.995))   # v1.1: 0.005 each
        _, dm = S.mclip(S.mean_of(D.C, S.REF), S.tau_of(D.C, comp))
        J = D.X * np.maximum(dm, 1e-6)[:, None]
        v, lv = S.scales(P, Cc, comp, False)
        Ua = S.U_of(D.C, lv).scale(dm).add(dm * comp["sig_ctx"] / math.sqrt(Cc))
        cov, _ = S.gls(J, Ua, v)
        self.cov_pair = cov * 2 * (1 - comp["rho"])
        self.FA, self.fa_names = fam_int_rows(D)
        self.se_fa = S.con_se(self.FA, self.cov_pair) * self.rp[D.at["lamS"]]   # lamS calibration factor


def flags_v10(D, y, cal, beta=None, cov=None, s_ctrl=0.0, s_cell=0.0):
    """Old V4 flags plus the v1.0 ones; returns the list of raised flags. Deterministic buyers (cov None):
    point estimates, as V4. Noisy arms (cov given): each flag needs its evidence to clear the threshold,
    as in the old V4 flags (estimate minus a one-sided t quantile times its standard error)."""
    beta = coef(D, y) if beta is None else beta
    f = S._flags(D, D.Call, y, beta, cov, cal.r1, s_ctrl, D.s.pmax, s_cell)
    e = D.A @ beta; at = D.at
    df_l, df_r = S.dfs(D.C, D.X, 2)
    se = np.zeros(len(e)) if cov is None else S.con_se(D.A, cov) * cal.r1
    fa = cal.FA @ beta
    sfa = np.zeros(len(fa)) if cov is None else S.con_se(cal.FA, cov) * cal.r1[at["lamS"]]
    for n, v, sv in zip(cal.fa_names, fa, sfa):
        f[f"yield_{n}"] = abs(v) - S.tq(df_l) * sv > 0.05
    if "mu" in at:
        f["mu"] = abs(e[at["mu"]]) - S.tq(df_r) * se[at["mu"]] > 0.05
    for k in ("lamB", "kB"):
        if k in at:
            f[k] = abs(e[at[k]]) - S.tq(df_r) * se[at[k]] > 0.05
    noisy = cov is not None
    f["raw_r"] = abs(raw_r(D, y)) - (1.6449 * cal.sd_r1 if noisy else 0.0) > 0.05
    f["edge"] = edge_error(D, y) > (max(0.05, cal.q_edge) if noisy else 0.05)
    vc, vl = spreads(D, y, beta)
    f["spread_ctrl"] = vc > cal.q_ctrl; f["spread_line"] = vl > cal.q_line
    return sorted(k for k, v in f.items() if v)


def steering_v10(D, cal, yb, ys, bb=None, bs=None, cb=None, cs=None, s_ctrl=0.0, s_cell=0.0):
    """H1 to H4 (as in stats_layer.decide, model-based paired SE at N* times the paired factor) and G1 to G5.
    Returns dict test -> passed."""
    bb = coef(D, yb) if bb is None else bb; bs = coef(D, ys) if bs is None else bs
    se = S.con_se(D.A, cal.cov_pair) * cal.rp
    se1 = se / math.sqrt(2 * (1 - S.COMP["rho"]))
    df_l, df_r = S.dfs(D.C, D.X, cal.P); at = D.at
    d = D.A @ (bs - bb); es = D.A @ bs; L = at["lamS"]
    out = {"H1": bool(d[L] / se[L] < -S.tq(df_l)), "H4": bool(es[L] - S.tq(df_l) * se1[L] > S.REACT)}
    for k in S.EQUIV:
        if k in at:
            out[k] = bool(abs(d[at[k]]) + S.tq(df_r) * se[at[k]] < S.MARGIN[k])
    for k, m in MARGIN_G1.items():                                   # G1
        if k in at:
            out[f"G1_{k}"] = bool(abs(d[at[k]]) + S.tq(df_r) * se[at[k]] < m)
    dfa = cal.FA @ (bs - bb); zc = S.tq(df_l, z=_zq(0.05 / len(dfa)))  # G2
    out["G2"] = bool(np.all(dfa / cal.se_fa < zc))
    out["G3"] = bool((raw_r(D, ys) - raw_r(D, yb)) / cal.se_r < -1.6449)   # G3
    # G4 dropped in v1.1: ~15 flags without multiplicity control failed 29% of genuine improvements;
    # on the first panel everything G4 caught was also caught by G1 or G3.
    vc, vl = spreads(D, ys, bs)
    out["G5"] = bool(vc <= cal.q_ctrl and vl <= cal.q_line)          # G5
    return out


def _zq(alpha):
    """One-sided normal quantile for small alpha (bisection on Phi)."""
    lo, hi = 0.0, 10.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if 1 - S.Phi(mid) > alpha:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def top_designs(n):
    r2 = [json.loads(l) for l in open(f"{S.OUT}/rung2.jsonl")]
    r2d = {r["id"]: r for r in r2}
    return [(i, r2d[i]) for i in S.robust_order(r2)[:n]]
