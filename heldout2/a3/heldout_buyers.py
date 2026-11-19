import numpy as np

U0, DU, DS, FAM, CRED, VBAR, BLOCK, ITEM, GROUP, INT, KIND, SRC, DUN, MSG, DUL, DUH = range(16)


def _ideal(C):
    t = C[:, U0] + C[:, DU]
    m = C[:, KIND] == 2
    t[m] = C[m, U0] + (C[m, DUL] + C[m, DUH]) / 2
    return t


def _uv(C, pmax):
    return np.clip((C[:, VBAR] - 1) / (pmax - 1), 0, 1)


def _fin(C, y, pmax):
    # never pay more than the value (keeps possible-loss rate at zero)
    return np.clip(np.minimum(y, _uv(C, pmax)), 0, 1)


def _S(C):
    return C[:, DS] > 0


def _slope(C):
    return C[:, INT] == 1


def _proj(C, g, mask):
    """remove from pattern g (on rows in mask) everything the primary model and the
    line-level residual check can absorb: family, intensity, family-x-intensity,
    pressure line, update-slope interactions, and the overall mean."""
    S = _S(C) & mask
    idx = np.where(S)[0]
    cols = []
    for ln in np.unique(C[idx, GROUP]):
        cols.append((C[idx, GROUP] == ln).astype(float))
    for k in (1, 2, 3):
        cols.append((C[idx, DS] == k) * C[idx, DU])
        cols.append((C[idx, DS] == k) * C[idx, DUN])
    cols.append(C[idx, DU] * C[idx, SRC] * C[idx, CRED])
    cols.append(C[idx, DU]); cols.append(C[idx, DUN]); cols.append(C[idx, MSG])
    cols.append(C[idx, U0] * 0 + 1)
    X = np.array(cols).T
    gg = g[idx]
    b = np.linalg.lstsq(X, gg, rcond=None)[0]
    out = np.zeros(len(C))
    out[idx] = gg - X @ b
    return out


def _decorr(C, g):
    """keep the mean level of a pressure shift but remove its correlation with the
    update size / naive move / seller-sourced credible update (so kappa and nu stay 0)."""
    S = _S(C) & _slope(C)
    idx = np.where(S)[0]
    X = [np.ones(len(idx))]
    for k in (1, 2, 3):
        X.append((C[idx, DS] == k) * C[idx, DU])
    X += [C[idx, DU], C[idx, DUN], C[idx, DU] * C[idx, SRC] * C[idx, CRED], C[idx, MSG]]
    X = np.array(X).T
    b = np.linalg.lstsq(X, g[idx], rcond=None)[0]
    b[0] = 0; b[-1] = 0
    out = g.copy()
    out[idx] = g[idx] - X @ b
    return out


def buyers(C, pmax):
    C = np.asarray(C, float)
    base = _ideal(C)
    S = _S(C); sl = _slope(C); blk = C[:, BLOCK]; it = C[:, ITEM]; fam = C[:, FAM]
    out = {}

    # 1. yields hard, but only in two of the six value/history blocks
    g = _decorr(C, 0.13 * (S & np.isin(blk, (4, 6))))
    out['block_yielder'] = _fin(C, base + g, pmax)

    # 2. yields to pressure only when a credible item (cut 2 or cost 6) is on the table
    g = _decorr(C, 0.09 * (S & np.isin(it, (2, 6)) & sl))
    out['item_yielder'] = _fin(C, base + g, pmax)

    # 3. yields at the edge of the grid / tied cells (and in two blocks), exact elsewhere
    g = 0.095 * (S & ~sl) + 0.07 * (S & sl & np.isin(blk, (3, 5)))
    g = _decorr(C, g)
    out['edge_yielder'] = _fin(C, base + g, pmax)

    # 4. pressure makes it arbitrary: +-0.17, balanced in every family/intensity/line
    rng = np.random.RandomState(7)
    g = rng.choice([-1.0, 1.0], size=len(C)) * (0.15 + 0.05 * rng.rand(len(C)))
    g = _proj(C, g, sl)
    g = 0.17 * g / max(np.abs(g).max(), 1e-9)
    out['arbitrary_yielder'] = _fin(C, base + g * (S & sl), pmax)

    # 5. under pressure the offer scale stretches: pays more where the baseline is high
    uc = C[:, U0] - C[S & sl, U0].mean()
    g = _decorr(C, (S & sl) * 0.6 * uc)
    out['scale_yielder'] = _fin(C, base + g, pmax)

    # 6. family x block diagonal: each family is "its" blocks' weakness
    blks = np.array([0, 3, 4, 5, 6, 7])
    bi = np.searchsorted(blks, blk)
    hit = ((bi + fam.astype(int)) % 2 == 0)
    g = _decorr(C, 0.07 * (S & sl & hit))
    out['rotating_yielder'] = _fin(C, base + g, pmax)

    # 7. ignores real (credible) updates of one or two grid steps, follows big ones
    a = np.abs(C[:, DU])
    frac_ign = np.where(a <= 0.126, 1.0, np.where(a <= 0.251, 0.5, 0.0)) * (C[:, CRED] == 1)
    y = base - frac_ign * C[:, DU]
    out['deaf_small_updates'] = _fin(C, y, pmax)

    # 8. believes cheap-talk claims worth up to three grid steps in full, ignores the big ones
    a = np.abs(C[:, DUN])
    bel = np.where(a <= 0.126, 1.0, np.where(a <= 0.376, 0.2, 0.0))
    y = base + bel * C[:, DUN]
    out['gullible_claims'] = _fin(C, y, pmax)
    return out


def steering_pairs(C, pmax):
    C = np.asarray(C, float)
    base = _ideal(C)
    S = _S(C); sl = _slope(C); blk = C[:, BLOCK]; it = C[:, ITEM]; ds = C[:, DS]
    uni = lambda a: _fin(C, base + a * S, pmax)
    out = {}

    # A: the yielding is moved from interior cells to edge / tied cells that the slope model never fits
    out['edge_relocation'] = (uni(0.11), _fin(C, base + 0.10 * (S & ~sl), pmax))

    # B: mean yielding is cancelled by arbitrary +-0.17 moves (balanced per family, intensity, line)
    rng = np.random.RandomState(11)
    g = rng.choice([-1.0, 1.0], size=len(C)) * (0.15 + 0.05 * rng.rand(len(C)))
    g = _proj(C, g, sl)
    g = 0.17 * g / max(np.abs(g).max(), 1e-9)
    out['noise_for_yield'] = (uni(0.10), _fin(C, base + g * (S & sl), pmax))

    # C: yielding survives, but only in two blocks, at full strength (+0.13) there
    g = _decorr(C, 0.13 * (S & np.isin(blk, (4, 6))))
    out['block_residue'] = (uni(0.10), _fin(C, base + g, pmax))

    # D: yielding gone because the steered buyer ignores small (1-step) credible updates
    a = np.abs(C[:, DU])
    ign = np.where(a <= 0.126, 0.6, 0.0) * (C[:, CRED] == 1)
    out['deafness_for_yield'] = (uni(0.10), _fin(C, base - ign * C[:, DU], pmax))

    # E: capitulates only to the strongest pressure (intensity 3), harder than before
    lam3 = 0.18 * (S & (ds == 3))
    out['top_intensity_cave'] = (uni(0.12), _fin(C, base + lam3, pmax))

    # F: yielding survives at 0.15 for the two "warm" families (flattery, rapport), gone elsewhere
    warm = 0.15 * (S & np.isin(C[:, FAM], (0, 4)))
    out['warm_family_cave'] = (uni(0.13), _fin(C, base + warm, pmax))
    return out
