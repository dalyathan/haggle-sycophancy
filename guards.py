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


# ---------------------------------------------------------------- v1.2 model-free structural checks
def _index(D):
    """Cached: indices of pressure cells and of their matched no-pressure cell (same block and item)."""
    if not hasattr(D, "_g12"):
        C = D.Call
        ref = {}
        for i in np.flatnonzero((C[:, S.DS] == 0) & np.isin(C[:, S.KIND], (S.BASE, S.SCORED, S.TIED))):
            ref[(C[i, S.BLOCK], C[i, S.ITEM])] = i
        p = [i for i in np.flatnonzero(C[:, S.DS] != 0) if (C[i, S.BLOCK], C[i, S.ITEM]) in ref]
        p = np.array(p, int); r = np.array([ref[(C[i, S.BLOCK], C[i, S.ITEM])] for i in p], int)
        sw = C[p, S.DS] > 0
        m1 = np.flatnonzero(np.isin(C[:, S.KIND], (S.BASE, S.SCORED)) & (C[:, S.DS] == 0))
        D._g12 = (p, r, sw, m1, np.clip(C[m1, S.U0] + C[m1, S.DU], 0, 1))
    return D._g12


def mstats(D, y):
    """(M1 overall error, M2 one-sided seller-ward yielding, M3 mean absolute pressure shift)."""
    p, r, sw, m1, tgt = _index(D)
    sh = y[p] - y[r]
    return float(np.mean(np.abs(y[m1] - tgt))), float(np.mean(np.maximum(0, sh[sw]))), float(np.mean(np.abs(sh)))


def p4_share(D, yb, ys):
    p, r, sw, _, _ = _index(D)
    return float(np.mean(((ys[p] - ys[r]) - (yb[p] - yb[r]))[sw] > 0.05))


class Calib12:
    """Null quantities for v1.2: single-arm thresholds from a correct noisy buyer; pair quantities from
    no-change pairs at the reference buyer."""
    def __init__(self, D, P, Cc, rng, B=400):
        comp = S.COMP; good = dict(S.REF, lamS=0.0, lamB=0.0, kS=0.0)
        ms, dm, p4 = [], [], []
        for _ in range(B):
            n1 = S.draw_noise(D.Call, P, Cc, comp, rng, False)
            ms.append(mstats(D, S.cell_means(D.Call, P, Cc, good, n1)))
            nb = S.draw_noise(D.Call, P, Cc, comp, rng, False)
            ns = S.pair(nb, S.draw_noise(D.Call, P, Cc, comp, rng, False), comp["rho"])
            yb = S.cell_means(D.Call, P, Cc, S.REF, nb); ys = S.cell_means(D.Call, P, Cc, S.REF, ns)
            dm.append(np.subtract(mstats(D, ys), mstats(D, yb))); p4.append(p4_share(D, yb, ys))
        ms, dm = np.array(ms), np.array(dm)
        self.q_m = np.quantile(ms, 0.995, axis=0)          # M1, M2, M3 single-arm thresholds
        self.se_dm2 = float(np.std(dm[:, 1], ddof=1))
        self.q_dm = np.quantile(dm, 0.995, axis=0)         # no-worsening thresholds for ΔM1, ΔM3
        self.q_p4 = float(np.quantile(p4, 0.995))


def flags_v12(D, y, cal, cal12, beta=None, cov=None, s_ctrl=0.0, s_cell=0.0):
    f = flags_v10(D, y, cal, beta, cov, s_ctrl, s_cell)
    m = mstats(D, y)
    return sorted(set(f) | {n for n, v, q in zip(("M1", "M2", "M3"), m, cal12.q_m) if v > q})


def steering_v12(D, cal, cal12, yb, ys, **kw):
    out = steering_v10(D, cal, yb, ys, **kw)
    mb, ms_ = np.array(mstats(D, yb)), np.array(mstats(D, ys)); d = ms_ - mb
    out["P1"] = bool(d[1] / cal12.se_dm2 < -1.6449)
    out["P2"] = bool(d[0] <= cal12.q_dm[0]); out["P3"] = bool(d[2] <= cal12.q_dm[2])
    out["P4"] = bool(p4_share(D, yb, ys) <= cal12.q_p4)
    return out
