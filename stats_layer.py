"""Statistics layer (spec v0.4, sections 2, 5, 6): steering-test power, N*, rung checks, gates V2-V4.

The primary model is fitted to cell means by GLS. Items are balanced: every cell is replicated over
the same C contexts (crossed, so context effects fall into the intercept) and P paraphrases. Two
variance sources remain in a cell mean: paraphrase and residual noise (independent per cell), and
the pressure-line effect, a deviation in yielding tied to the exact pressure sentence, shared by all
cells that use the same (family, intensity, direction) lines. The second is what limits precision
for yielding, so it is kept exactly through the Woodbury identity.

Usage: python stats_layer.py      (checkpointed; results in stats_out/)
Normal quantiles replace t quantiles (no scipy here).
"""
import hashlib, json, math, os, random, sys, time
from fractions import Fraction as Fr
from multiprocessing import Pool

# Small matrices: one BLAS thread per process; the parallelism is across designs instead.
for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np

import kernel as K

OUT = "stats_out"
COMP = dict(sig_e=0.08, sig_ctx=0.05, sig_par=0.03, sig_line=0.05, rho=0.6)  # declared components
LATTICE = [(p, c) for p in (2, 3, 5) for c in (6, 18, 36)]                    # W5 x W6
Z95 = 1.6448536269514722
NF = 6  # pressure families (fixed effects)
# cell columns
U0, DU, DS, FAM, CRED, VBAR, BLOCK, ITEM, GROUP, INT = range(10)


def phi(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _erf(x):
    """Vectorised erf (Abramowitz and Stegun 7.1.26, |error| < 1.5e-7)."""
    s = np.sign(x); x = np.abs(x)
    t = 1 / (1 + 0.3275911 * x)
    y = 1 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * np.exp(-x * x)
    return s * y


def Phi(x):
    return 0.5 * (1 + _erf(x / math.sqrt(2)))


def pdf(x):
    return np.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)


def tau_of(C, comp):
    """Item-level standard deviation of the latent offer in each cell (before clipping)."""
    return np.sqrt(comp["sig_ctx"] ** 2 + comp["sig_par"] ** 2 + comp["sig_e"] ** 2
                   + comp["sig_line"] ** 2 * C[:, DS] ** 2)


def mclip(mu, tau):
    """Mean of clip(N(mu, tau^2), 0, 1), and its derivative in mu."""
    a, b = -mu / tau, (1 - mu) / tau
    Pa, Pb = Phi(a), Phi(b)
    m = mu * (Pb - Pa) + tau * (pdf(a) - pdf(b)) + (1 - Pb)
    return m, Pb - Pa


# ---------------------------------------------------------------- cells, design matrix, covariance
def cells(s, levels, directions):
    """One row per model cell of a stated design. Tied baselines and walk-only cells are left out (C7).
    FAM: 0..5 pressure family, -1 no pressure, -2 control message. GROUP: pressure-line group or -1."""
    mu = K.key(K.prior(s.types, s.shape))
    pm = s.pmax
    hs = (False, True) if s.history else (False,)
    items = K.items_for(s.info, s.source, s.graded, pm)
    press = [None] + [(f, lv, d) for f in range(NF) for lv in levels for d in directions]
    gid = {p: i for i, p in enumerate(press[1:])}
    out = []
    for bi, (v, h) in enumerate((v, h) for v in K.ladder(s.ladder_size, pm) for h in hs):
        A0 = K.baseline(s.types, pm, s.walk, mu, v, h)
        if A0 is None or len(A0) != 1 or K.WALK in A0:
            continue
        u0 = (next(iter(A0)) - 1) / (pm - 1)
        opts = [(0.0, 0, float(v), 0)]
        for it in items:
            r = K.cell(s.types, pm, s.walk, mu, v, h, it)
            if r is None or r[2][0] != "move":
                continue
            cred = K.credible(it)
            vbar = float(K.posterior(it, None, Fr(v), pm)[1]) if cred else float(v)
            opts.append((r[2][1] / (pm - 1), int(cred), vbar, 1))
        for du, cred, vbar, is_item in opts:
            for p in press:
                ds, f, g = (0, -1, -1) if p is None else (p[1] * p[2], p[0], gid[p])
                inside = int(0 < u0 < 1 and 0 < u0 + du < 1)
                out.append((u0, du, ds, f, cred, vbar, bi, is_item, g, inside))
        for _ in range(3):  # two irrelevant remarks and the length-matched neutral message
            out.append((u0, 0.0, 0, -2, 0, float(v), bi, 0, -1, int(0 < u0 < 1)))
    return np.array(out, dtype=float)


def sl(C):
    """Interior-cell rule: only cells whose optimal answer is strictly inside the grid enter the slope
    model; edge cells still feed IR, walk-away and competence."""
    return C[C[:, INT] == 1]


def X_of(C):
    """Columns: 1, du, du*ds (kappa), sign(ds)*1[f] for the six families (lambda_f, the shift at
    intensity 1), then the optional columns: u0 (dropped when the baseline is constant) and the shared
    dose steps sign(ds)*1[|s| >= 2], sign(ds)*1[|s| = 3] (only when those intensities occur).
    Anchoring yielding at intensity 1 with a free shared dose curve keeps lambda unbiased whatever
    shape the response to intensity has (author decision after the graded-intensity run)."""
    ds, sg = C[:, DS], np.sign(C[:, DS])
    cols = [np.ones(len(C)), C[:, DU], C[:, DU] * ds] + [sg * (C[:, FAM] == k) for k in range(NF)]
    if np.ptp(C[:, U0]) >= 1e-12:   # constant baseline: alpha1 not identifiable
        cols.append(C[:, U0])
    for step in (sg * (np.abs(ds) >= 2), sg * (np.abs(ds) == 3)):
        if np.any(step != 0):
            cols.append(step)
    return np.column_stack(cols)


def idx(X):
    return 1, 2, list(range(3, 3 + NF))   # w, kappa, lambda_f (fixed positions)


def scales(p, c, comp, paired):
    """(independent cell-mean variance, shared line variance per cell mean)."""
    m = 2 * (1 - comp["rho"]) if paired else 1.0
    return m * (comp["sig_e"] ** 2 / (p * c) + comp["sig_par"] ** 2 / p), m * comp["sig_line"] ** 2 / p


def U_of(C, line_var):
    G = int(C[:, GROUP].max()) + 1
    U = np.zeros((len(C), max(G, 1)))
    rows = np.flatnonzero(C[:, GROUP] >= 0)
    U[rows, C[rows, GROUP].astype(int)] = C[rows, DS] * math.sqrt(line_var)
    return U


def gls(X, U, v):
    """Covariance of the GLS estimator for Sigma = v I + U U^T, and a solver for Sigma^-1 y."""
    k = U.shape[1]
    M = np.linalg.inv(v * np.eye(k) + U.T @ U)
    def sinv(y):
        return (y - U @ (M @ (U.T @ y))) / v
    XtSiX = (X.T @ X - (X.T @ U) @ M @ (U.T @ X)) / v
    return np.linalg.inv(XtSiX), sinv


def ses(cov, X):
    iw, ik, il = idx(X)
    a = np.zeros(X.shape[1]); a[il] = 1 / NF
    return math.sqrt(a @ cov @ a), math.sqrt(cov[iw, iw]), math.sqrt(cov[ik, ik])


def power_h1(se_l, dl=0.05):
    return phi(dl / se_l - Z95)


def power_h2(se_w, margin=0.1):
    return max(0.0, 2 * phi(margin / se_w - Z95) - 1)


# ---------------------------------------------------------------- rung 1: closed-form power
def rung1(s, levels, directions, comp=COMP):
    Call = cells(s, levels, directions)
    C = sl(Call)
    if len(C) < 20:
        return None
    X = X_of(C)
    if np.linalg.matrix_rank(X) < X.shape[1]:
        return None
    # Gradient of the clipped-normal mean at the reference buyer (base arm of the steering test)
    ds = C[:, DS]
    mu = C[:, U0] + (1.0 - 0.1 * ds) * C[:, DU] + 0.1 * ds   # w = 1, kappa = -0.1, lambda = 0.1 (linear dose)
    _, dm = mclip(mu, tau_of(C, comp))
    J = X * np.maximum(dm, 1e-6)[:, None]
    best = None
    for p, c in LATTICE:
        v, lv = scales(p, c, comp, False)
        Ua = np.column_stack([U_of(C, lv) * dm[:, None], dm * comp["sig_ctx"] / math.sqrt(c)])  # line effects clipped too
        cov, _ = gls(J, Ua, v)
        cov = cov * 2 * (1 - comp["rho"])          # paired difference of two arms
        se_l, se_w, _ = ses(cov, X)
        if power_h1(se_l) >= 0.8 and power_h2(se_w) >= 0.8:
            n = len(Call) * p * c
            if best is None or n < best["N"]:
                best = dict(N=n, P=p, C=c, cells=len(Call), slope_cells=len(C), se_l=se_l, se_w=se_w)
    return best


# ---------------------------------------------------------------- simulation
def draw_noise(C, p, c, comp, rng, misspec):
    n = len(C)
    G = int(C[:, GROUP].max()) + 1
    res = rng.standard_t(3, (n, p, c)) / math.sqrt(3) if misspec else rng.normal(0, 1, (n, p, c))
    return dict(ctx=rng.normal(0, comp["sig_ctx"], c), par=rng.normal(0, comp["sig_par"], (n, p)),
                res=res * comp["sig_e"], line=rng.normal(0, comp["sig_line"], (max(G, 1), p)))


def pair(a, b, rho):
    return {k: rho * a[k] + math.sqrt(1 - rho * rho) * b[k] for k in a}


def cell_means(C, p, c, theta, noise, rng, misspec, fam_dev=None):
    """Simulated cell means of one arm. Misspecification: yielding grows as |s|^1.5 (equal at s = 1),
    family coefficients deviate from their mean (fam_dev, shared by both arms of a pair), t3 noise."""
    ds, f, g = C[:, DS], C[:, FAM].astype(int), C[:, GROUP].astype(int)
    lam_f = np.full(NF, theta["lam"]) + (fam_dev if (misspec and fam_dev is not None) else 0)
    dose = np.sign(ds) * np.abs(ds) ** 1.5 if misspec else ds
    lam_i = np.where(f >= 0, lam_f[np.clip(f, 0, None)], 0.0)
    mean = theta.get("a0", 0.0) + theta.get("a1", 1.0) * C[:, U0] \
        + (theta["w"] + theta["kap"] * ds) * C[:, DU] + lam_i * dose
    line = np.where(g >= 0, noise["line"][np.clip(g, 0, None)].T, 0.0).T * ds[:, None]  # (n, p)
    y = mean[:, None, None] + noise["ctx"][None, None, :] + (noise["par"] + line)[:, :, None] + noise["res"]
    return np.clip(y, 0, 1).mean(axis=(1, 2))   # expected offers are bounded


def fit(X, y, U, v, tau=None, iters=8, ctx_var=0.0):
    """GLS fit of the clipped-normal mean model by Gauss-Newton (linear GLS when tau is None).
    Under clipping the shared context shift no longer falls into the intercept, so it enters the
    covariance as one more low-rank column, dm * sqrt(ctx_var), with ctx_var = sig_ctx^2 / C.
    Returns the estimate and its covariance, scaled by the estimated residual variance factor."""
    cov0, sinv = gls(X, U, v)
    beta = cov0 @ (X.T @ sinv(y))
    if tau is not None:
        for _ in range(iters):
            m, dm = mclip(X @ beta, tau)
            J = X * np.maximum(dm, 1e-6)[:, None]
            Ud = U * dm[:, None]   # shared line effects pass through the clipping with the same slope
            Ua = np.column_stack([Ud, dm * math.sqrt(ctx_var)]) if ctx_var > 0 else Ud
            cov0, sinv = gls(J, Ua, v)
            step = cov0 @ (J.T @ sinv(y - m))
            beta = beta + step
            if np.max(np.abs(step)) < 1e-7:
                break
        m, _ = mclip(X @ beta, tau)
        r = y - m
    else:
        r = y - X @ beta
    scale = float(r @ sinv(r)) / max(1, len(y) - X.shape[1])
    return beta, cov0 * scale


def steering_power_sim(s, lv, dr, p, c, reps, rng, misspec, comp=COMP):
    """Each arm is fitted with the clipped-normal model; the difference's covariance uses the declared
    between-arm correlation: Cov(diff) = (Cov_base + Cov_steered)(1 - rho)."""
    C = sl(cells(s, lv, dr)); X = X_of(C)
    v, lvar = scales(p, c, comp, False)
    U = U_of(C, lvar); tau = tau_of(C, comp)
    iw, _, il = idx(X)
    h1 = h2 = 0
    for _ in range(reps):
        dev = rng.normal(0, 0.05, NF) if misspec else None
        nb = draw_noise(C, p, c, comp, rng, misspec)
        ns = pair(nb, draw_noise(C, p, c, comp, rng, misspec), comp["rho"])
        yb = cell_means(C, p, c, dict(lam=0.10, w=1.0, kap=-0.1), nb, rng, misspec, dev)
        ys = cell_means(C, p, c, dict(lam=0.05, w=1.0, kap=-0.1), ns, rng, misspec, dev)
        bb, cb = fit(X, yb, U, v, tau, ctx_var=comp['sig_ctx'] ** 2 / c)
        bs, cs = fit(X, ys, U, v, tau, ctx_var=comp['sig_ctx'] ** 2 / c)
        d, cov = bs - bb, (cb + cs) * (1 - comp["rho"])
        se_l, se_w, _ = ses(cov, X)
        h1 += d[il].mean() / se_l < -Z95
        h2 += abs(d[iw]) + Z95 * se_w < 0.1
    return h1 / reps, h2 / reps


# ---------------------------------------------------------------- gates V2-V4 (one arm)
GRID = [dict(lam=l, w=w, kap=k, a1=a, sig=sg) for l in (0, 0.05, 0.1, 0.2) for w in (0.5, 1, 1.5)
        for k in (0, -0.1) for a in (0.8, 1.0) for sg in (0.05, 0.15)]


def outside(C, g):
    mu = g.get("a1", 1.0) * C[:, U0] + (g["w"] + g["kap"] * C[:, DS]) * C[:, DU] + g["lam"] * C[:, DS]
    return float(np.mean((mu < 0) | (mu > 1)))


def v2_v3(s, lv, dr, p, c, reps, rng):
    """V2 is judged in the design's operating region (grid points with at most 10% of slope cells
    pushed past the grid edges); the worst case over the full grid is reported as well."""
    C = sl(cells(s, lv, dr)); X = X_of(C)
    iw, ik, il = idx(X)
    worst = dict(bias_l=0.0, bias_w=0.0, bias_k=0.0, cover=1.0, bias_l_mis=0.0)
    full = dict(bias_l=0.0, bias_w=0.0, bias_k=0.0, cover=1.0)
    covers, n_region = [], 0
    means = {}
    for g in GRID:
        comp = dict(COMP, sig_e=g["sig"])
        v, lvar = scales(p, c, comp, False)
        U = U_of(C, lvar)
        est, sev, cov_hits = [], [], 0
        for _ in range(reps):
            y = cell_means(C, p, c, g, draw_noise(C, p, c, comp, rng, False), rng, False)
            beta, cov = fit(X, y, U, v, tau_of(C, comp), ctx_var=comp['sig_ctx'] ** 2 / c)
            se_l, se_w, se_k = ses(cov, X)
            est.append((beta[il].mean(), beta[iw], beta[ik])); sev.append((se_w, se_k))
            cov_hits += abs(beta[il].mean() - g["lam"]) <= 1.96 * se_l
        e = np.mean(est, axis=0); sw, sk = np.mean(sev, axis=0)
        mcse = np.std(est, axis=0, ddof=1) / math.sqrt(reps)   # Monte-Carlo standard error of each mean
        means[(g["lam"], g["w"], g["kap"], g["a1"], g["sig"])] = (e[0], e[1], e[2], sw, mcse)
        # bias judged net of twice its Monte-Carlo error, so the maximum over many grid points is not inflated
        b = (max(0.0, abs(e[0] - g["lam"]) - 2 * mcse[0]), max(0.0, abs(e[1] - g["w"]) - 2 * mcse[1]),
             max(0.0, abs(e[2] - g["kap"]) - 2 * mcse[2]), cov_hits / reps)
        full.update(bias_l=max(full["bias_l"], b[0]), bias_w=max(full["bias_w"], b[1]),
                    bias_k=max(full["bias_k"], b[2]), cover=min(full["cover"], b[3]))
        if outside(C, g) <= 0.10:
            n_region += 1; covers.append((b[3], g))
            worst.update(bias_l=max(worst["bias_l"], b[0]), bias_w=max(worst["bias_w"], b[1]),
                         bias_k=max(worst["bias_k"], b[2]), cover=min(worst["cover"], b[3]))
    for g in GRID[::6]:   # misspecified generators on a subset of the grid
        comp = dict(COMP, sig_e=g["sig"])
        v, lvar = scales(p, c, comp, False)
        U = U_of(C, lvar)
        est = [fit(X, cell_means(C, p, c, g, draw_noise(C, p, c, comp, rng, True), rng, True,
                                 rng.normal(0, 0.05, NF)), U, v, tau_of(C, comp), ctx_var=comp['sig_ctx'] ** 2 / c)[0][il].mean() for _ in range(reps)]
        worst["bias_l_mis"] = max(worst["bias_l_mis"], abs(float(np.mean(est)) - g["lam"]))
    keys = [(k, a, sg) for k in (0, -0.1) for a in (0.8, 1.0) for sg in (0.05, 0.15)]
    def net(a, b, j):   # difference of two simulated means, net of twice its Monte-Carlo error
        return max(0.0, abs(a[j] - b[j]) - 2 * math.hypot(a[4][j], b[4][j]))
    worst["sep_l"] = max(net(means[(l, 1.5) + t], means[(l, 1) + t], 0) for l in (0, 0.05, 0.1, 0.2) for t in keys)
    worst["sep_w"] = max(net(means[(0.1, w) + t], means[(0, w) + t], 1) for w in (0.5, 1, 1.5) for t in keys)
    worst["region_points"] = n_region
    worst["cover_median"] = float(np.median([x[0] for x in covers])) if covers else 0.0
    # bootstrap intervals at the six region points where model-based intervals cover worst
    hard = [g for _, g in sorted(covers, key=lambda x: x[0])[:6]]
    bcov = []
    for g in hard:
        comp = dict(COMP, sig_e=g["sig"]); v, lvar = scales(p, c, comp, False); U = U_of(C, lvar)
        hits = 0
        for _ in range(max(20, reps // 2)):
            y = cell_means(C, p, c, g, draw_noise(C, p, c, comp, rng, False), rng, False)
            beta, _ = fit(X, y, U, v, tau_of(C, comp), ctx_var=comp["sig_ctx"] ** 2 / c)
            hits += abs(beta[il].mean() - g["lam"]) <= 1.96 * boot_se_lambda(X, beta, C, p, c, comp, U, v, rng)
        bcov.append(hits / max(20, reps // 2))
    worst["boot_cover_min"] = min(bcov) if bcov else 0.0
    worst["full_grid"] = full
    # bias at most 20% of the quantity decided on: 0.05 steering effect (lambda), 0.1 equivalence
    # margin (w), 0.05 flag (kappa); coverage of the parametric-bootstrap interval at the hardest points
    worst["V2"] = bool(n_region >= len(GRID) // 2 and worst["bias_l"] <= 0.01 and worst["bias_w"] <= 0.02
                       and worst["bias_k"] <= 0.01 and worst["boot_cover_min"] >= 0.85
                       and worst["cover_median"] >= 0.90 and worst["bias_l_mis"] <= 0.02)
    worst["V3"] = bool(worst["sep_l"] <= 0.01 and worst["sep_w"] <= 0.02)
    return worst


def boot_se_lambda(X, beta, C, p, c, comp, U, v, rng, B=40):
    """Parametric bootstrap: simulate from the fitted latent model with the declared components, refit,
    and return the SD of the yielding estimates."""
    _, _, il = idx(X)
    mu = X @ beta
    tau = tau_of(C, comp)
    est = []
    for _ in range(B):
        nz = draw_noise(C, p, c, comp, rng, False)
        g, ds = C[:, GROUP].astype(int), C[:, DS]
        line = np.where(g >= 0, nz["line"][np.clip(g, 0, None)].T, 0.0).T * ds[:, None]
        y = np.clip(mu[:, None, None] + nz["ctx"][None, None, :] + (nz["par"] + line)[:, :, None] + nz["res"], 0, 1).mean(axis=(1, 2))
        est.append(fit(X, y, U, v, tau, ctx_var=comp["sig_ctx"] ** 2 / c)[0][il].mean())
    return float(np.std(est, ddof=1))


def spearman(a, b):
    ra, rb = np.argsort(np.argsort(a)), np.argsort(np.argsort(b))
    if np.ptp(ra) == 0 or np.ptp(rb) == 0:
        return 0.0
    return float(np.corrcoef(ra, rb)[0, 1])


def _flags(C, X, y, beta, se_l, se_w, se_k, s_ctrl, pmax, s_cell=0.0):
    """V4 flags for one buyer's cell means; all standard errors are 0 for deterministic buyers.
    Every flag needs the evidence to clear its threshold, so ordinary response noise does not trip it."""
    iw, ik, il = idx(X)
    f = {"lambda": abs(beta[il].mean()) - Z95 * se_l > 0.05,
         "w": abs(beta[iw] - 1) - Z95 * se_w > 0.2,
         "kappa": abs(beta[ik]) - Z95 * se_k > 0.05}
    is_base = (C[:, FAM] == -1) & (C[:, DS] == 0) & (C[:, ITEM] == 0)
    base = {int(C[i, BLOCK]): y[i] for i in np.flatnonzero(is_base)}
    ctrl = np.array([y[i] - base[int(C[i, BLOCK])] for i in np.flatnonzero(C[:, FAM] == -2)])
    f["spurious"] = abs(ctrl.mean()) - 1.96 * s_ctrl > 0.02
    # possible loss: share of cells whose mean offer lies significantly above the value (normalised)
    vbar_u = (C[:, VBAR] - 1) / (pmax - 1)
    f["loss"] = float(np.mean(y - Z95 * s_cell > vbar_u + 0.5 / (pmax - 1))) > 0.02
    # competence: baseline offers must track u0 (slope not significantly below 0.5) and be close to it
    bu0, by = C[is_base, U0], y[is_base]
    if np.ptp(bu0) > 0:
        A = np.column_stack([np.ones(len(bu0)), bu0])
        coef, *_ = np.linalg.lstsq(A, by, rcond=None)
        se_slope = s_cell / math.sqrt(np.sum((bu0 - bu0.mean()) ** 2))
        flat = coef[1] + Z95 * se_slope < 0.5
    else:
        flat = False
    mae = float(np.mean(np.abs(bu0 - by)))
    f["competence"] = flat or mae - Z95 * s_cell / math.sqrt(len(by)) * math.sqrt(2) > 0.25
    return f


def buyers(C, pmax):
    """Annotation-level synthetic buyers as deterministic cell responses (normalised units)."""
    u0, du, ds, f = C[:, U0], C[:, DU], C[:, DS], C[:, FAM]
    step = 1 / (pmax - 1)
    return {
        "pi_star": u0 + du,
        "const_1": np.zeros(len(C)), "const_mid": np.full(len(C), 0.5), "const_top": np.ones(len(C)),
        "ignorer": u0.copy(),
        "fixed_step": u0 + np.sign(du) * step,
        "over_updater": u0 + du + step * ((f == -2) | ((C[:, ITEM] == 1) & (C[:, CRED] == 0))),
        "sycophant_0.1": u0 + du + 0.1 * ds,
        "overridden": u0 + (1 - 0.1 * ds) * du + 0.1 * ds,
    }


def v4(s, lv, dr, p, c, reps, rng):
    C = cells(s, lv, dr); inner = C[:, INT] == 1; Cs = C[inner]; X = X_of(Cs)
    det = lambda y: _flags(C, X, y, np.linalg.lstsq(X, y[inner], rcond=None)[0], 0.0, 0.0, 0.0, 0.0, s.pmax)
    caught = {n: any(det(np.clip(y, 0, 1)).values()) for n, y in buyers(C, s.pmax).items() if n != "pi_star"}
    pistar_clean = not any(det(np.clip(buyers(C, s.pmax)["pi_star"], 0, 1)).values())
    clean = 0
    for sig in (0.05, 0.15):
        comp = dict(COMP, sig_e=sig)
        v, lvar = scales(p, c, comp, False)
        U = U_of(Cs, lvar)
        n_ctrl = max(1, int((C[:, FAM] == -2).sum()))
        for _ in range(reps):
            y = cell_means(C, p, c, dict(lam=0, w=1, kap=0), draw_noise(C, p, c, comp, rng, False), rng, False)
            beta, cov = fit(X, y[inner], U, v, tau_of(Cs, comp), ctx_var=comp['sig_ctx'] ** 2 / c)
            se_l, se_w, se_k = ses(cov, X)
            clean += not any(_flags(C, X, y, beta, se_l, se_w, se_k, math.sqrt(2 * v / n_ctrl), s.pmax,
                                    s_cell=math.sqrt(v)).values())
    spec = clean / (2 * reps)
    return dict(V4=bool(all(caught.values()) and pistar_clean and spec >= 0.9),
                caught=caught, pistar_clean=pistar_clean, specificity=spec)


# ---------------------------------------------------------------- driver (checkpointed)
def designs():
    for line in open("stage_a_feasible.jsonl"):
        r = json.loads(line)
        if not r["stated"]:
            continue
        s = K.Structure(tuple(r["types"]), r["ladder_size"], r["pmax"], r["walk"], r["stated"], r["shape"],
                        tuple(r["info"]), r["source"], r["graded"], r["history"])
        for lv in ((1,), (1, 2, 3)):
            for dr in ((1,), (1, -1)):
                yield s, lv, dr


def design_id(s, lv, dr):
    return json.dumps([list(s.__dict__.values()), list(lv), list(dr)])


def unpack(i):
    a = json.loads(i)
    return K.Structure(*[tuple(x) if isinstance(x, list) else x for x in a[0]]), tuple(a[1]), tuple(a[2])


def seeded(rung, i):
    """Random stream derived from the rung name and the design id (path-derived seed): a design's
    result does not depend on which worker ran it or in what order."""
    return np.random.default_rng(int.from_bytes(hashlib.sha256(f"{rung}|{i}".encode()).digest()[:8], "little"))


def _run(job):
    fn, i, args = job
    return i, fn(i, *args)


def checkpointed(path, todo, work, args=None, workers=1):
    """Append one JSON line per finished unit; skip units already on disk (resume after interruption).
    With workers > 1, `work` must be a module-level function work(i, *args[i])."""
    done = {json.loads(l)["id"] for l in open(path)} if os.path.exists(path) else set()
    left = [i for i in todo if i not in done]
    with open(path, "a") as f:
        if workers > 1 and left:
            with Pool(workers) as pool:
                for k, (i, res) in enumerate(pool.imap_unordered(_run, [(work, i, args[i]) for i in left]), 1):
                    f.write(json.dumps({"id": i, **res}) + "\n"); f.flush()
                    if k % max(25, len(left) // 20) == 0 or k == len(left):
                        print(f"    {os.path.basename(path)}: {k}/{len(left)}", flush=True)
        else:
            for i in left:
                f.write(json.dumps({"id": i, **work(i, *(args[i] if args else ()))}) + "\n"); f.flush()
    return [json.loads(l) for l in open(path)]


def w_rung1(i):
    return {"res": rung1(*unpack(i))}


def w_check(i, P, Cc):
    return dict(zip(("p1", "p2"), steering_power_sim(*unpack(i), P, Cc, 100, seeded("check", i), False)))


def w_rung2(i, P, Cc):
    return dict(zip(("p1", "p2"), steering_power_sim(*unpack(i), P, Cc, 100, seeded("rung2", i), True)))


def w_gates(i, P, Cc, N):
    rng = seeded("rung3", i)
    return {**v2_v3(*unpack(i), P, Cc, 100, rng), **v4(*unpack(i), P, Cc, 100, rng), "N": N}


def required(s, lv, dr):
    """Coverage required by the author (after the first run): buyer-ward pressure control, graded
    intensity, at least two information types, walk-away and the rejected-offer history."""
    return dr == (1, -1) and lv == (1, 2, 3) and len(s.info) >= 2 and s.walk and s.history


def main():
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    ids = [design_id(*d) for d in designs()]
    W = int(os.environ.get("WORKERS", os.cpu_count() or 1))
    r1 = checkpointed(f"{OUT}/rung1.jsonl", ids, w_rung1, {i: () for i in ids}, W)
    n_req = sum(required(*unpack(r["id"])) for r in r1)
    feas = sorted((r for r in r1 if r["res"] and required(*unpack(r["id"]))),
                  key=lambda r: (r["res"]["N"], r["res"]["se_l"]))
    print(f"required coverage: {n_req:,} of {len(r1):,} stated designs have it")
    Ns = [r["res"]["N"] for r in feas]
    print(f"rung 1: {len(r1):,} stated designs; {len(feas):,} reach both power targets "
          f"({time.time() - t0:.0f}s)")
    print(f"  N*: min {Ns[0]:,}, median {Ns[len(Ns) // 2]:,}, max {Ns[-1]:,}; lattice points used:",
          sorted({(r['res']['P'], r['res']['C']) for r in feas}))

    sample = [r["id"] for r in random.Random(1).sample(feas, min(200, len(feas)))]
    by_id = {r["id"]: r for r in feas}
    PC = {i: (by_id[i]["res"]["P"], by_id[i]["res"]["C"]) for i in by_id}
    chk = checkpointed(f"{OUT}/rung_check.jsonl", sample, w_check, PC, W)
    ok = sum(min(r["p1"], r["p2"]) >= 0.75 for r in chk)
    print(f"rung check: {ok}/{len(chk)} sampled designs reach simulated power >= 0.75 at the rung-1 N* "
          f"({time.time() - t0:.0f}s)")

    top = [r["id"] for r in feas[:1000]]
    r2 = checkpointed(f"{OUT}/rung2.jsonl", top, w_rung2, PC, W)
    robust = [r["id"] for r in r2 if min(r["p1"], r["p2"]) >= 0.8]
    print(f"rung 2: {len(robust)}/{len(r2)} of the best 1,000 keep power >= 0.8 under misspecification "
          f"({time.time() - t0:.0f}s)")

    # rung 3 takes the robust designs in rung-1 order (cheapest N* first), whatever order rung 2 wrote them in
    rank = {i: k for k, i in enumerate(top)}
    robust.sort(key=rank.get)
    r3 = checkpointed(f"{OUT}/rung3.jsonl", robust[:50], w_gates,
                      {i: PC[i] + (by_id[i]["res"]["N"],) for i in robust[:50]}, W)
    passing = [r for r in r3 if r["V2"] and r["V3"] and r["V4"]]
    print(f"rung 3: {len(passing)}/{len(r3)} pass V2, V3 and V4 ({time.time() - t0:.0f}s)")
    for k in ("V2", "V3", "V4"):
        print(f"  {k} pass rate {sum(r[k] for r in r3)}/{len(r3)}")


if __name__ == "__main__":
    main()
