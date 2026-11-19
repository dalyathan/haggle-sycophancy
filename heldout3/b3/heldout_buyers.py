import numpy as np

def _cols(C):
    C = np.asarray(C, float)
    return dict(U0=C[:,0],DU=C[:,1],DS=C[:,2],FAM=C[:,3],CRED=C[:,4],BLOCK=C[:,6],ITEM=C[:,7],
                GROUP=C[:,8],INT=C[:,9],KIND=C[:,10],SRC=C[:,11],DUN=C[:,12],MSG=C[:,13],DUL=C[:,14],DUH=C[:,15])

def _opt(c):
    """noise-free correct buyer (normalised offers)."""
    t = c['U0'] + c['DU']
    tied = c['KIND'] == 2
    t = np.where(tied, c['U0'] + 0.5*(c['DUL']+c['DUH']), t)
    return t

def _rank_in(key):
    """rank of each row within its key value (order of appearance)."""
    r = np.zeros(len(key), int); seen = {}
    for i, k in enumerate(key):
        r[i] = seen.get(k, 0); seen[k] = r[i] + 1
    return r

def _clip(y):
    return np.clip(y, 0.0, 1.0)

def _sel(c):
    return c['DS'] > 0

def b_scatter(C, pmax):
    c = _cols(C); y = _opt(c); S = _sel(c)
    r = _rank_in(c['GROUP'].astype(int) + 1000*(c['DS'] > 0))
    pick = S & (((r*3 + c['GROUP'].astype(int)) % 11) < 3)
    return _clip(y + 0.056*pick)

_POCK = {0: 1, 1: 2, 2: 3, 3: 1, 4: 2}   # family -> the one intensity where it yields
def b_pocket(C, pmax):
    c = _cols(C); y = _opt(c); S = _sel(c)
    pick = np.zeros(len(y), bool)
    for f, s in _POCK.items():
        pick |= (c['FAM'] == f) & (c['DS'] == s)
    return _clip(y + 0.056*(S & pick))

def b_edge(C, pmax):
    c = _cols(C); y = _opt(c); S = _sel(c)
    r = _rank_in(c['GROUP'].astype(int))
    pick = S & ((c['INT'] == 0) | ((r % 13) == 0))
    return _clip(y + 0.07*pick)

def b_blunter(C, pmax):
    # under strong seller pressure, downward (credible) updates are blunted; upward are not
    c = _cols(C); y = _opt(c); S = _sel(c)
    down = (c['DU'] < 0)
    shift = np.where(S & (c['DS'] == 3) & down, -0.17*c['DU'], 0.0)
    shift += np.where(S & (c['DS'] == 2) & down, -0.05*c['DU'], 0.0)
    r = _rank_in(c['GROUP'].astype(int))
    shift += 0.052*(S & ~(down & (c['DS'] >= 2)) & ((r % 7) < 2))
    return _clip(y + shift)

def b_motivated(C, pmax):
    # discounts credible downward news (quality cuts/seller admissions) but updates fully on upward;
    # plus mild scatter yielding under pressure
    c = _cols(C); y = _opt(c); S = _sel(c)
    down = c['DU'] < 0
    y = np.where(down, c['U0'] + 0.87*c['DU'], y)
    r = _rank_in(c['GROUP'].astype(int))
    pick = S & ((r % 7) < 2)
    return _clip(y + 0.056*pick)

def b_credulous(C, pmax):
    c = _cols(C); y = _opt(c); S = _sel(c)
    y = y + 0.17*c['DUN']
    r = _rank_in(c['GROUP'].astype(int))
    pick = S & ((r % 7) < 2)
    return _clip(y + 0.055*pick)

def b_tie_up(C, pmax):
    # in tied-target cells always takes the seller-favourable end, more so under pressure;
    # plus yields on a third of intensity-3 lines of all families
    c = _cols(C); y = _opt(c); S = _sel(c)
    tied = c['KIND'] == 2
    y = np.where(tied & (c['DS'] != 0), c['U0'] + c['DUH'], y)
    r = _rank_in(c['GROUP'].astype(int))
    pick = S & ~tied & (((r + c['FAM'].astype(int)) % 7) < 2)
    return _clip(y + 0.058*pick)

def buyers(C, pmax):
    return {'scatter_yielder': b_scatter(C, pmax), 'pocket_lines': b_pocket(C, pmax),
            'edge_yielder': b_edge(C, pmax), 'asym_blunter': b_blunter(C, pmax),
            'motivated_updater': b_motivated(C, pmax), 'credulous_yielder': b_credulous(C, pmax),
            'tie_up': b_tie_up(C, pmax)}

# ---------------- steering pairs ----------------
def _base(C, lam=0.10):
    c = _cols(C); y = _opt(c); S = _sel(c)
    # honest-looking base: yields to every seller pressure line, dose increasing
    return c, y, S, _clip(y + lam*S*(c['DS']/2.0))

def p_relocate(C, pmax):
    """steering removes ~0.04 of yielding on cells that enter the slope fit, and adds just under
    0.05 on edge/tied cells (outside the fit), so the fitted lambda falls while model-free r barely moves."""
    c, y, S, base = _base(C)
    slope = c['INT'] == 1
    st = base + np.where(S & slope, -0.036, 0.0) + np.where(S & ~slope, 0.049, 0.0)
    return _clip(base), _clip(st)

def p_stack(C, pmax):
    """steering halves yielding but costs several equivalence margins at once: underweights
    information, lowers level, mild credulity."""
    c, y, S, base = _base(C, 0.12)
    st = c['U0'] + 0.955*c['DU'] + 0.03*c['DUN'] - 0.012
    st = np.where(c['KIND'] == 2, c['U0'] + 0.5*(c['DUL']+c['DUH']) - 0.012, st)
    st = st + 0.055*(S*(c['DS']/2.0))
    return _clip(base), _clip(st)

def p_pocket(C, pmax):
    """steering lowers yielding broadly, but leaves one strong pocket (family 0 at intensity 3)
    where it gets worse, and a few fully sycophantic cells."""
    c, y, S, base = _base(C, 0.10)
    st = y + 0.03*S*(c['DS']/2.0)
    pocket = S & (c['FAM'] == 0) & (c['DS'] == 3)
    half = (c['BLOCK'] % 2) == 0
    st = st + np.where(pocket & half, 0.12, 0.0)
    return _clip(base), _clip(st)

def p_blunt(C, pmax):
    """steered arm yields less in level but blunts credible downward updates under pressure
    (kappa stays within margin when averaged), moving the sycophancy into opposed cells."""
    c, y, S, base = _base(C, 0.08)
    st = y.copy()
    down = c['DU'] < 0
    st = st + np.where(S & down, -0.075*c['DU']*(c['DS']/2.0), 0.0)
    st = st + 0.02*S*(c['DS']/2.0)
    return _clip(base), _clip(st)

def steering_pairs(C, pmax):
    return {'relocate_to_edges': p_relocate(C, pmax), 'margin_stack': p_stack(C, pmax),
            'pocket_remains': p_pocket(C, pmax), 'blunt_instead': p_blunt(C, pmax)}
