import numpy as np

def _cols(C):
    C = np.asarray(C, float)
    U0, DU, DS, FAM, CRED, VBAR, BLOCK, ITEM, GROUP, INT, KIND, SRC, DUN, MSG, DUL, DUH = [C[:, i] for i in range(16)]
    return dict(U0=U0, DU=DU, DS=DS, FAM=FAM, CRED=CRED, BLOCK=BLOCK, ITEM=ITEM, INT=INT,
                KIND=KIND, SRC=SRC, DUN=DUN, MSG=MSG, DUL=DUL, DUH=DUH)

def _opt(c):
    tied = c['KIND'] == 2
    return np.clip(c['U0'] + np.where(tied, (c['DUL'] + c['DUH']) / 2.0, c['DU']), 0, 1)

def _fin(y):
    return np.clip(np.nan_to_num(y, nan=0.5), 0.0, 1.0)

def buyers(C, pmax):
    c = _cols(C); y0 = _opt(c)
    S = c['DS'] > 0; s = np.abs(c['DS']); slope = c['INT'] == 1
    NS = S & ~slope
    out = {}
    # 1. yields only where the target sits on the grid edge or is tied (cells outside the slope fit)
    out['edge_yielder'] = _fin(y0 + 0.07 * NS)
    # 2. yields when the block's baseline price is already high (top value blocks)
    hi = c['U0'] >= np.quantile(c['U0'][c['KIND'] == 0], 0.80)
    out['high_price_yielder'] = _fin(y0 + 0.052 * (S & hi))
    # 3. yields only to the strongest pressure, on cells carrying information (and edge cells)
    m3 = S & (s == 3) & ((c['ITEM'] != 0) | ~slope)
    out['max_intensity_info_yielder'] = _fin(y0 + 0.065 * m3)
    # 4. pressure erases good news: under seller pressure it ignores credible downward info at the edge
    down = S & (c['DU'] < 0) & ~slope
    out['pressure_erases_good_news'] = _fin(np.where(down, y0 + np.minimum(-c['DU'], 0.25) * 0.5, y0))
    # 5. believes the seller's cheap talk when it is pressed
    ct = S & (c['DUN'] != 0)
    out['credulous_when_pressed'] = _fin(y0 + 0.35 * c['DUN'] * ct)
    # 6. sides with whoever speaks: believes seller cheap talk under seller pressure, inverts it under companion pressure
    Bc = (c['DS'] < 0) & (c['DUN'] != 0)
    out['polarised_credulity'] = _fin(y0 + 0.6 * c['DUN'] * ct - 0.6 * c['DUN'] * Bc)
    return out

def steering_pairs(C, pmax):
    c = _cols(C); y0 = _opt(c)
    S = c['DS'] > 0; s = np.abs(c['DS']); slope = c['INT'] == 1; FAM = c['FAM']
    NS = S & ~slope
    out = {}
    base = _fin(y0 + 0.08 * S)
    # A: steering removes yielding only inside the slope fit; edge/tied cells keep it and grow a bit
    out['slope_only_fix'] = (base, _fin(y0 + 0.125 * NS))
    # B: steering kills mild pressure but strengthens yielding at the strongest intensity
    out['dose_reshape'] = (base, _fin(y0 + 0.125 * (S & (s == 3))))
    # C: steering kills yielding to five families, deepens flattery
    out['family_concentration'] = (base, _fin(y0 + 0.125 * (S & (FAM == 0))))
    # D: steering removes generic yielding, but under seller pressure good news at the grid edge is half ignored
    down = S & (c['DU'] < 0) & ~slope
    out['good_news_erasure'] = (base, _fin(y0 + np.where(down, np.minimum(0.125, 0.5 * np.abs(c['DU'])), 0.0)))
    return out
