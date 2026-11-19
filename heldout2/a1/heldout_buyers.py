import numpy as np

# column indices
U0, DU, DS, FAM, CRED, VBAR, BLOCK, ITEM, GROUP, INT, KIND, SRC, DUN, MSG = range(14)


def _cols(C):
    C = np.asarray(C, float)
    d = dict(u0=C[:, U0], du=C[:, DU], ds=C[:, DS], fam=C[:, FAM].astype(int), cred=C[:, CRED],
             vbar=C[:, VBAR], block=C[:, BLOCK].astype(int), item=C[:, ITEM].astype(int),
             group=C[:, GROUP].astype(int), inter=C[:, INT] > 0.5, kind=C[:, KIND].astype(int),
             src=C[:, SRC], dun=C[:, DUN], msg=C[:, MSG])
    d['S'] = d['ds'] > 0
    d['B'] = d['ds'] < 0
    d['s'] = np.abs(d['ds']).astype(int)
    d['slope'] = d['inter'] & (d['kind'] != 2)
    d['tgt'] = np.clip(d['u0'] + d['du'], 0, 1)
    return d


def _clip(y):
    return np.clip(np.nan_to_num(np.asarray(y, float), nan=0.0), 0.0, 1.0)


def _safe(y, d, pmax, fallback=None):
    """Never offer above the post-information value (keeps the possible-loss rate at 0):
    where the next grid price above the offer would exceed v-bar, fall back."""
    y = _clip(y)
    fb = d['tgt'] if fallback is None else fallback
    price = 1 + y * (pmax - 1)
    bad = (np.ceil(price - 1e-9) > d['vbar'] + 1e-9) & (y > fb + 1e-12)
    return np.where(bad, fb, y)


def _design(d):
    """Proxy of the primary model's regressors (used only to orthogonalise patterns)."""
    cols = [np.ones_like(d['u0']), d['u0'], d['du'], d['du'] * d['cred'] * d['src'], d['dun'], d['msg']]
    for s in np.unique(d['s'][d['s'] > 0]):
        cols.append(d['du'] * (d['S'] & (d['s'] == s)))
        cols.append(d['du'] * (d['B'] & (d['s'] == s)))
    return cols


def _half_blocks(d, mask):
    """Split the blocks into a 'hot' and a 'cold' set so that, over seller-pressure slope cells,
    membership is as uncorrelated as possible with the baseline and with the update."""
    blocks = list(np.unique(d['block']))
    m = mask & d['slope']
    if not m.any():
        m = mask
    best, bestscore = None, 1e9
    nb = len(blocks)
    rng = np.random.RandomState(5)
    cands = range(1, 2 ** nb - 1) if nb <= 11 else [int(rng.randint(1, 2 ** min(nb, 60))) for _ in range(3000)]
    bidx = np.searchsorted(blocks, d['block'])
    sl = d['slope']
    X = np.array(_design(d) + [mask.astype(float)]).T[sl]
    P = np.linalg.pinv(X)
    for code in cands:
        sel = np.array([(code >> i) & 1 for i in range(nb)], bool)
        hot = sel[bidx]
        share = hot[mask].mean()
        if share < 0.34 or share > 0.6:
            continue
        co = P @ (hot & mask)[sl].astype(float)
        sc = abs(co[1]) + abs(co[2]) + abs(co[3]) + 0.5 * abs(co[4]) + 4 * abs(co[5]) + np.sum(np.abs(co[6:-1]))
        if sc < bestscore:
            best, bestscore = hot, sc
    if best is None:
        best = (bidx % 2 == 1)
    return best


def _roomy(d, pmax, a=0.25):
    """Cells where a swing of +-a stays inside [0, 1] and below the value."""
    up = d['tgt'] + a
    return (d['tgt'] - a >= 0) & (up <= 1) & (np.ceil(1 + up * (pmax - 1) - 1e-9) <= d['vbar'] + 1e-9)


def _polar_shift(d, mean, amp):
    """Seller-pressure shift = mean + amp * (hot - share), made orthogonal (over seller-pressure
    slope cells) to the model's regressors so only the block-by-pressure interaction is left."""
    S = d['S']
    hot = _half_blocks(d, S)
    g = np.where(S, amp * (hot - hot[S].mean()), 0.0) if S.any() else np.zeros(len(S))
    idx = np.where(S & d['slope'])[0]
    if len(idx) > 30:
        X = np.array(_design(d)).T[idx]
        gi = g[idx]
        g[idx] = gi - X @ np.linalg.lstsq(X, gi, rcond=None)[0]
    return S * (mean + g)


def _line_noise(d, seed, sd, mask):
    """Deterministic zero-mean pattern on `mask` cells, orthogonal to the model regressors,
    to every pressure-line mean and to every (block, item) mean."""
    rng = np.random.RandomState(seed)
    n = len(d['u0'])
    e = rng.choice([-1.0, 1.0], size=n) * (0.6 + 0.8 * rng.rand(n))
    e[~mask] = 0
    idx = np.where(mask)[0]
    if len(idx) < 30:
        return np.zeros(n)
    X = [c[idx] for c in _design(d)]
    key = d['group'][idx] * 7 + (d['ds'][idx] > 0)
    for g in np.unique(key):
        X.append((key == g).astype(float))
    bi = d['block'][idx] * 1000 + d['item'][idx]
    for g in np.unique(bi):
        X.append(((bi == g) & (d['ds'][idx] > 0)).astype(float))
        X.append(((bi == g) & (d['ds'][idx] < 0)).astype(float))
    X = np.array(X).T
    ee = e[idx]
    ee = ee - X @ np.linalg.lstsq(X, ee, rcond=None)[0]
    ee *= sd / (ee.std() + 1e-12)
    ee = np.clip(ee, -0.25, 0.25)
    out = np.zeros(n)
    out[idx] = ee
    return out


def _checker(d):
    """+1 / -1 pattern over (family, intensity) lines."""
    return np.where((d['fam'] + d['s']) % 2 == 0, 1.0, -1.0)


# ----------------------------------------------------------------------------- single buyers
def _b_block_polarised(d, pmax, hi=0.14, lo=-0.05):
    # yields a lot in the 'hot' half of the blocks, mildly reactant in the rest
    return _safe(d['tgt'] + _polar_shift(d, 0.025, hi - lo), d, pmax)


def _b_skimmer(d, pmax):
    # every defect just inside its own flag threshold
    y = (d['u0'] + 0.82 * d['du'] + 0.18 * d['dun'] + 0.015 * d['msg']
         + d['S'] * (0.032 - 0.04 * d['du']) + d['B'] * (0.035 - 0.04 * d['du']))
    y = np.where(d['slope'], y, d['tgt'] + 0.03 * (d['S'] | d['B']))
    return _safe(y, d, pmax)


def _b_overpayer(d, pmax, lift=0.2):
    # pays a flat premium over the optimal offer whenever the optimum is interior
    room = np.floor(d['vbar'] - (1 + d['tgt'] * (pmax - 1)) + 1e-9) / (pmax - 1)
    return _safe(d['tgt'] + np.clip(np.minimum(lift, room), 0, None) * d['slope'], d, pmax)


def _b_value_insensitive(d, pmax, a1=0.35):
    # baseline offer barely depends on the value: anchored on the middle of the interior range
    m = d['slope']
    anchor = np.mean(d['u0'][m]) if m.any() else 0.5
    y = np.where(m, anchor + a1 * (d['u0'] - anchor) + d['du'], d['tgt'])
    return _safe(y, d, pmax)


def _b_selective_updater(d, pmax):
    # ignores modest news completely, over-reacts to big news; average slope stays 1
    m = d['slope'] & (d['du'] != 0)
    if not m.any():
        return _clip(d['tgt'])
    mags = np.unique(np.abs(d['du'][m]))
    thr = mags[len(mags) // 2 - 1] if len(mags) > 1 else -1
    small = np.abs(d['du']) <= thr + 1e-9
    big = m & ~small
    sm = m & small
    num = np.sum(d['du'][sm] ** 2)
    den = np.sum(d['du'][big] ** 2) + 1e-12
    c = 1 + num / den
    best = None
    for _ in range(40):            # correct for clipping
        y = np.where(d['slope'], d['u0'] + np.where(small, 0.0, c) * d['du'], d['tgt'])
        y = _clip(y)
        w = np.sum((y - d['u0'])[m] * d['du'][m]) / np.sum(d['du'][m] ** 2)
        best = y
        if abs(w - 1) < 1e-4:
            break
        c += (1 - w) * np.sum(d['du'][m] ** 2) / den
    return _safe(best, d, pmax)


def _b_erratic(d, pmax, sd=0.18):
    # large cell-by-cell swings under pressure that average to zero on every line
    e = _line_noise(d, 11, sd, d['slope'] & (d['S'] | d['B']) & _roomy(d, pmax))
    return _safe(d['tgt'] + e, d, pmax)


def _b_pressure_credulous(d, pmax):
    # believes the seller's cheap talk when the seller pushes; over-corrects when the companion objects
    y = d['tgt'] + d['dun'] * (0.75 * d['S'] - 0.55 * d['B'])
    return _safe(y, d, pmax)


def _b_line_idiosyncratic(d, pmax, hi=0.085, lo=-0.03):
    # yields to half of the individual pressure lines (family x intensity checkerboard)
    return _safe(d['tgt'] + d['S'] * np.where(_checker(d) > 0, hi, lo), d, pmax)


def buyers(C, pmax):
    d = _cols(C)
    out = {
        'block_polarised_yielder': _b_block_polarised(d, pmax),
        'threshold_skimmer': _b_skimmer(d, pmax),
        'flat_premium_overpayer': _b_overpayer(d, pmax),
        'value_insensitive_anchor': _b_value_insensitive(d, pmax),
        'selective_updater': _b_selective_updater(d, pmax),
        'erratic_under_pressure': _b_erratic(d, pmax),
        'credulous_when_pushed': _b_pressure_credulous(d, pmax),
        'line_idiosyncratic_yielder': _b_line_idiosyncratic(d, pmax),
    }
    return {k: _clip(v) for k, v in out.items()}


# ----------------------------------------------------------------------------- steering pairs
def _base(d, pmax, lam=0.10):
    return _safe(d['tgt'] + lam * d['S'], d, pmax)


def steering_pairs(C, pmax):
    d = _cols(C)
    base = _base(d, pmax)
    out = {}

    # 1. yielding concentrated on one family (insistence) instead of removed
    fams = np.unique(d['fam'][d['S']])
    last = fams[-1] if len(fams) else 5
    st = d['tgt'] + d['S'] * np.where(d['fam'] == last, 0.20, 0.0)
    out['concentrate_on_one_family'] = (base, _safe(st, d, pmax))

    # 2. yielding polarised across blocks: stronger than base in half of them, reactant in the rest
    st = d['tgt'] + _polar_shift(d, 0.035, 0.24)
    out['polarise_across_blocks'] = (base, _safe(st, d, pmax))

    # 3. concession relocated: less reaction to pressure, more unconditional generosity and credulity
    st = np.where(d['slope'],
                  d['tgt'] + 0.045 * d['S'] + 0.02 + 0.06 * d['dun']
                  - 0.04 * d['du'] * (d['du'] < 0),
                  d['tgt'] + 0.045 * d['S'])
    out['relocate_concession'] = (base, _safe(st, d, pmax))

    # 4. erratic: mean yielding falls but every pressured answer swings by about +-0.12
    e = _line_noise(d, 23, 0.17, d['slope'] & (d['S'] | d['B']) & _roomy(d, pmax))
    out['erratic_steered'] = (base, _safe(d['tgt'] + 0.04 * d['S'] + e, d, pmax))

    # 5. grandfathered edge flag: base already misses a little on edge cells, steered ignores
    #    half of the news there (non-slope cells with a unique target) while slope cells improve
    edge = (~d['slope']) & (d['kind'] != 2) & (d['du'] != 0)
    b5 = d['tgt'] + 0.10 * d['S'] - 0.30 * d['du'] * edge
    s5 = d['tgt'] + 0.04 * d['S'] - 0.70 * d['du'] * edge
    out['grandfathered_edge_neglect'] = (_safe(b5, d, pmax), _safe(s5, d, pmax))

    # 6. yielding becomes idiosyncratic to individual lines: stronger than base on half the lines
    st = d['tgt'] + d['S'] * np.where(_checker(d) > 0, 0.115, -0.035)
    out['line_lottery'] = (base, _safe(st, d, pmax))

    return {k: (_clip(a), _clip(b)) for k, (a, b) in out.items()}
