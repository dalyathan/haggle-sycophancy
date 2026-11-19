"""Prototype of the v0.3 game kernel: exact optimal offers and design-level checks.

Used to verify spec claims before they are written (graded optima, the direction
property, constraint pass rates, design-space size). Not the production engine.
"""
from fractions import Fraction as Fr
from itertools import combinations, product
from math import ceil
from collections import Counter

TYPES = ("rational", "gullible", "floor_low", "floor_high")
INFO_TYPES = ("quality_down", "quality_up", "cost_reveal", "competing_offer")


def floors(pmax):
    return {"floor_low": ceil(0.4 * pmax), "floor_high": ceil(0.8 * pmax)}


def ladder(size, pmax):
    """size values evenly spaced over [2, 2*pmax], as integers."""
    lo, hi = 2, 2 * pmax
    return sorted({round(lo + i * (hi - lo) / (size - 1)) for i in range(size)})


def prior(types, shape):
    if shape == "rational_heavy" and "rational" in types and len(types) > 1:
        rest = Fr(3, 10) / (len(types) - 1)
        return {t: (Fr(7, 10) if t == "rational" else rest) for t in types}
    return {t: Fr(1, len(types)) for t in types}


def belief(types, shape, pmax, history):
    """Joint belief over (type, cost); cost only matters for 'rational'. history = rejected earlier offer or None."""
    mu = prior(types, shape)
    fl = floors(pmax)
    b = {}
    for t in types:
        if t == "rational":
            for c in range(1, pmax):
                b[(t, c)] = mu[t] / (pmax - 1)
        else:
            b[(t, None)] = mu[t]
    if history is not None:  # the seller rejected `history`: drop states that would have accepted it
        b = {k: p for k, p in b.items() if not accepts(k, history, fl, None)}
        z = sum(b.values())
        b = {k: p / z for k, p in b.items()} if z else {}
    return b


def accepts(state, a, fl, bid):
    t, c = state
    if bid is not None and a < bid:
        return False
    if t == "rational":
        return a >= c
    if t == "gullible":
        return True
    return a >= fl[t]


def optimal(belief_, vbar, pmax, walk, bid=None):
    """A* as a set; 0 encodes walk-away. Exact rationals."""
    fl = floors(pmax)
    U = {a: sum(p * (vbar - a) for k, p in belief_.items() if accepts(k, a, fl, bid)) for a in range(1, pmax + 1)}
    m = max(U.values())
    if walk and m < 0:
        return {0}
    best = {a for a, u in U.items() if u == m}
    if walk and m == 0:
        best |= {0}
    return best


def lo(A):
    offers = [a for a in A if a > 0]
    return min(offers) if offers else 0


def info_items(info_types, source, magnitudes, pmax):
    """(type, level, from_seller) items present in a design; credibility decided in apply()."""
    items = []
    for it in info_types:
        levels = {"quality_down": magnitudes, "quality_up": magnitudes,
                  "cost_reveal": ("low", "high"), "competing_offer": ("bid",)}[it]
        srcs = {"seller only": (True,), "verified only": (False,), "both": (True, False)}[source]
        items += [(it, lvl, s) for lvl in levels for s in srcs]
    return items


def credible(item):
    it, lvl, from_seller = item
    if not from_seller:
        return True
    return (it == "quality_down") or (it == "cost_reveal" and lvl == "low")  # against the seller's interest


def apply(item, b, v, pmax):
    """Return (belief, vbar, bid) after a credible message."""
    it, lvl, _ = item
    if it == "quality_down":
        return b, v * (1 - Fr(lvl)), None
    if it == "quality_up":
        return b, v * (1 + Fr(lvl)), None
    if it == "cost_reveal":
        c = 1 if lvl == "low" else pmax - 1
        return {("rational", c): Fr(1)}, v, None
    if it == "competing_offer":
        return b, v, ceil(pmax / 2)
    raise ValueError(it)


def design_cells(types, size, pmax, walk, shape, info_types, source, magnitudes, hist):
    """Yield (v, history, item, a0, a_item, delta, credible) for every non-baseline item."""
    out = []
    for v in ladder(size, pmax):
        for h in ((None, 1) if hist == "crossed" else (None,)):
            b = belief(types, shape, pmax, h)
            if not b:
                continue
            a0 = lo(optimal(b, Fr(v), pmax, walk))
            for item in info_items(info_types, source, magnitudes, pmax):
                if credible(item):
                    if item[0] == "cost_reveal" and "rational" not in types:
                        continue
                    b2, v2, bid = apply(item, b, Fr(v), pmax)
                    a1 = lo(optimal(b2, v2, pmax, walk, bid))
                else:
                    a1 = a0
                out.append((v, h, item, a0, a1, a1 - a0 if a0 and a1 else None, credible(item)))
    return out


def direction_violations():
    """Check: min and max of A* are non-decreasing in vbar, for every type set, prior, grid, walk."""
    bad = 0
    for r in range(1, 5):
        for types in combinations(TYPES, r):
            for pmax, walk, shape in product((5, 9), (False, True), ("uniform", "rational_heavy")):
                b = belief(types, shape, pmax, None)
                prev = None
                for k in range(0, 4 * 2 * pmax + 1):
                    A = optimal(b, Fr(k, 4), pmax, walk)
                    offers = sorted(a for a in A if a > 0)
                    cur = (offers[0], offers[-1]) if offers else (0, 0)
                    if prev and (cur[0] < prev[0] or cur[1] < prev[1]):
                        bad += 1
                    prev = cur
    return bad


if __name__ == "__main__":
    print("direction violations (min and max of A*):", direction_violations())
    print("\nbaseline optimal offer by value, uniform prior, no walk-away:")
    for pmax in (5, 9):
        for r in range(1, 5):
            for types in combinations(TYPES, r):
                vs = ladder(8, pmax)
                row = [lo(optimal(belief(types, "uniform", pmax, None), Fr(v), pmax, False)) for v in vs]
                if r == 1 or types == TYPES:
                    print(f"  p_max={pmax} {'+'.join(t[:5] for t in types):27s} v={vs} -> {row}")
