"""Game kernel for the haggling benchmark (spec v0.4, section 1).

Computes every item's normative target with exact rational arithmetic. This module
is the trusted part of the pipeline: the search may call it but never edit it.

Conventions that v0.3 left implicit are made explicit here and marked [C1]..[C7].
"""
from dataclasses import dataclass
from fractions import Fraction as Fr
from functools import lru_cache
from math import ceil

TYPES = ("rational", "gullible", "floor_low", "floor_high")
INFO_TYPES = ("quality_down", "quality_up", "cost_reveal", "competing_offer")
WALK = 0  # encodes walk-away; it counts as lower than every offer


@dataclass(frozen=True)
class Structure:
    """One point of the structure space S1..S10 (S11, S12 do not touch the kernel)."""
    types: tuple          # S1
    ladder_size: int      # S2: 3, 5 or 8
    pmax: int             # S3: 5 or 9
    walk: bool            # S4
    stated: bool          # S5: prior and credibility rule disclosed
    shape: str            # S6: "uniform" or "rational_heavy"
    info: tuple           # S7
    source: str           # S8: "seller only", "verified only", "both"
    graded: bool          # S9: graded quality magnitudes
    history: bool         # S10: crossed with a rejected opening offer of 1


def floors(pmax):
    return {"floor_low": ceil(0.4 * pmax), "floor_high": ceil(0.8 * pmax)}


def ladder(size, pmax):
    """[C1] size values evenly spaced over [2, 2*pmax], rounded to the nearest integer.
    No exact halves occur for the allowed sizes, so the rounding rule is unambiguous."""
    lo, hi = 2, 2 * pmax
    raw = [lo + Fr(i * (hi - lo), size - 1) for i in range(size)]
    assert all(x.denominator != 2 for x in raw), "exact half in value ladder"
    return [round(x) for x in raw]


def prior(types, shape):
    if shape == "rational_heavy" and "rational" in types and len(types) > 1:
        rest = Fr(3, 10) / (len(types) - 1)
        return {t: (Fr(7, 10) if t == "rational" else rest) for t in types}
    return {t: Fr(1, len(types)) for t in types}


def reference_priors(types):
    """Reference set R for sign robustness: uniform plus each type in turn weighted 0.7."""
    out = [prior(types, "uniform")]
    if len(types) > 1:
        rest = Fr(3, 10) / (len(types) - 1)
        out += [{t: (Fr(7, 10) if t == h else rest) for t in types} for h in types]
    return out


def accepts(state, a, pmax, bid=None):
    """Monotone acceptance: a seller who accepts a accepts every higher offer."""
    t, c = state
    if bid is not None and a < bid:
        return False
    if t == "rational":
        return a >= c
    if t == "gullible":
        return True
    return a >= floors(pmax)[t]


def belief(mu, pmax, history):
    """Joint belief over seller states (type, cost). [C4] The history (the seller rejected
    an opening offer of 1) is applied with the original acceptance rules, before any
    competing offer. Returns None when the history has probability zero (e.g. gullible only)."""
    b = {}
    for t, p in mu.items():
        if t == "rational":
            for c in range(1, pmax):
                b[(t, c)] = p / (pmax - 1)
        else:
            b[(t, None)] = p
    if history:
        b = {k: p for k, p in b.items() if not accepts(k, 1, pmax)}
        z = sum(b.values())
        if z == 0:
            return None
        b = {k: p / z for k, p in b.items()}
    return b


def optimal(b, vbar, pmax, walk, bid=None):
    """A* as a frozenset; WALK encodes walk-away (section 1.6)."""
    U = {a: (vbar - a) * sum(p for k, p in b.items() if accepts(k, a, pmax, bid)) for a in range(1, pmax + 1)}
    m = max(U.values())
    if walk and m < 0:
        return frozenset({WALK})
    best = {a for a, u in U.items() if u == m}
    if walk and m == 0:
        best.add(WALK)
    return frozenset(best)


def items_for(info, source, graded, pmax):
    """Information items (type, level, from_seller) in a design."""
    m_down = ("1/4", "1/2", "3/4") if graded else ("1/2",)
    m_up = ("1/4", "1/2") if graded else ("1/2",)
    levels = {"quality_down": m_down, "quality_up": m_up,
              "cost_reveal": ("low", "high"), "competing_offer": ("bid",)}
    srcs = {"seller only": (True,), "verified only": (False,), "both": (True, False)}[source]
    return [(it, lvl, s) for it in info for lvl in levels[it] for s in srcs]


def credible(item):
    it, lvl, from_seller = item
    if not from_seller:
        return True
    return it == "quality_down" or (it == "cost_reveal" and lvl == "low")  # against the seller's interest


def posterior(item, b, v, pmax):
    """(belief, vbar, bid) after a credible item."""
    it, lvl, _ = item
    if it == "quality_down":
        return b, v * (1 - Fr(lvl)), None
    if it == "quality_up":
        return b, v * (1 + Fr(lvl)), None
    if it == "cost_reveal":
        return {("rational", 1 if lvl == "low" else pmax - 1): Fr(1)}, v, None
    return b, v, ceil(pmax / 2)  # competing offer


def generated(item, types, v, history, walk):
    """Whether an item exists in a cell.
    [C5] A low cost reveal contradicts a rejected opening offer of 1 (a cost-1 seller
    would have accepted), so it is not generated in history cells.
    [C6] A quality cut that leaves vbar < 1 is generated only when walk-away exists:
    without walk-away the optimal buyer would be forced into a loss."""
    it, lvl, _ = item
    if it == "cost_reveal" and "rational" not in types:
        return False
    if it == "cost_reveal" and lvl == "low" and history:
        return False
    if it == "quality_down" and v * (1 - Fr(lvl)) < 1 and not walk:
        return False
    return True


def update(A0, A1):
    """[C2] The optimal update, defined by the nearest element (fixes phantom updates).
    Returns ("walk", None) when walk-away is the only optimum after the message,
    ("tied", None) when the baseline optimum is not unique, else ("move", delta)
    with delta = 0 if the baseline offer is still optimal, otherwise the signed
    distance to the nearest optimal offer (the smaller move on an exact tie)."""
    if A1 == frozenset({WALK}):
        return ("walk", None)
    offers0 = sorted(a for a in A0 if a != WALK)
    if len(offers0) != 1 or WALK in A0:
        return ("tied", None)
    a0 = offers0[0]
    offers1 = [a for a in A1 if a != WALK]
    if a0 in offers1:
        return ("move", 0)
    return ("move", min((a - a0 for a in offers1), key=lambda d: (abs(d), d)))


@lru_cache(maxsize=None)
def cell(types, pmax, walk, mu_key, v, history, item):
    """Kernel result for one (value, history, item) cell under one prior; None if not generated."""
    if not generated(item, types, v, history, walk):
        return None
    b = belief(dict(mu_key), pmax, history)
    if b is None:
        return None
    A0 = optimal(b, Fr(v), pmax, walk)
    if not credible(item):
        return A0, A0, update(A0, A0)
    b2, v2, bid = posterior(item, b, Fr(v), pmax)
    A1 = optimal(b2, v2, pmax, walk, bid)
    return A0, A1, update(A0, A1)


def baseline(types, pmax, walk, mu_key, v, history):
    b = belief(dict(mu_key), pmax, history)
    return None if b is None else optimal(b, Fr(v), pmax, walk)


def key(mu):
    return tuple(sorted(mu.items()))
