import sys, time
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from functools import lru_cache
from itertools import combinations, product
from fractions import Fraction as Fr
import kernel_proto as K

t0 = time.time()
SETS = [c for r in range(1, 5) for c in combinations(K.TYPES, r)]
INFO_SUBSETS = [c for r in range(1, 5) for c in combinations(K.INFO_TYPES, r)]

def priors_for(types):
    """Reference prior set for sign robustness: uniform plus each type made heavy (0.7)."""
    out = [K.prior(types, "uniform")]
    if len(types) > 1:
        for h in types:
            rest = Fr(3, 10) / (len(types) - 1)
            out.append({t: (Fr(7, 10) if t == h else rest) for t in types})
    return out

def belief_from(mu, types, pmax, h):
    fl = K.floors(pmax); b = {}
    for t in types:
        if t == "rational":
            for c in range(1, pmax): b[(t, c)] = mu[t] / (pmax - 1)
        else: b[(t, None)] = mu[t]
    if h is not None:
        b = {k: p for k, p in b.items() if not K.accepts(k, h, fl, None)}
        z = sum(b.values()); b = {k: p / z for k, p in b.items()} if z else {}
    return b

@lru_cache(maxsize=None)
def delta(types, pmax, walk, mu_key, v, h, item):
    mu = dict(mu_key)
    b = belief_from(mu, types, pmax, h)
    if not b: return None
    a0 = K.lo(K.optimal(b, Fr(v), pmax, walk))
    if not K.credible(item): return (a0, 0)
    if item[0] == "cost_reveal" and "rational" not in types: return None
    b2, v2, bid = K.apply(item, b, Fr(v), pmax)
    a1 = K.lo(K.optimal(b2, v2, pmax, walk, bid))
    return (a0, a1 - a0 if a0 and a1 else None)

count = dict(raw=0, canonical=0, forbidden_cost=0, headroom=0, graded=0, k3=0, feasible=0)
for types, size, pmax, walk, shape, stated, info, source, mags, hist in product(
        SETS, (3, 5, 8), (5, 9), (False, True), ("uniform", "rational_heavy"), (False, True),
        INFO_SUBSETS, ("seller only", "verified only", "both"), ("single", "graded"), ("none", "crossed")):
    count["raw"] += 1
    # canonical form: inactive parameters take one value
    if shape == "rational_heavy" and not ("rational" in types and len(types) > 1): continue
    if mags == "graded" and not ({"quality_down", "quality_up"} & set(info)): continue
    count["canonical"] += 1
    if "cost_reveal" in info and "rational" not in types:
        count["forbidden_cost"] += 1; continue
    magnitudes = ("0.5",) if mags == "single" else ("0.25", "0.5")
    items = K.info_items(info, source, magnitudes, pmax)
    hs = (None, 1) if hist == "crossed" else (None,)
    vs = K.ladder(size, pmax)
    mu_ref = tuple(sorted(K.prior(types, shape).items()))
    base = [delta(types, pmax, walk, mu_ref, v, h, items[0]) for v in vs for h in hs]
    a0s = [d[0] for d in base if d]
    interior = sum(1 for a in a0s if 1 < a < pmax) / max(1, len(a0s))
    if interior < 0.5: continue
    count["headroom"] += 1
    # graded: >= 3 distinct non-zero |delta| over credible items (reference prior)
    mags_seen, ok_types = set(), set()
    for it in items:
        for v in vs:
            for h in hs:
                d = delta(types, pmax, walk, mu_ref, v, h, it)
                if not d or d[1] in (None, 0) or not K.credible(it): continue
                if stated:
                    mags_seen.add(abs(d[1])); ok_types.add(it[0])
                else:  # hidden prior: sign must agree under every prior in the reference set
                    signs = set()
                    for mu in priors_for(types):
                        dd = delta(types, pmax, walk, tuple(sorted(mu.items())), v, h, it)
                        signs.add(None if not dd or dd[1] is None else (dd[1] > 0) - (dd[1] < 0))
                    if len(signs) == 1 and 0 not in signs and None not in signs:
                        mags_seen.add(abs(d[1])); ok_types.add(it[0])
    if len(mags_seen) < 3: continue
    count["graded"] += 1
    if not set(info) <= ok_types: continue
    count["k3"] += 1
    count["feasible"] += 1
pressure = 4  # pressure intensity (2) x pressure direction (2) do not touch the kernel
print({k: v * (pressure if k != "raw" else pressure) for k, v in count.items()})
print("seconds:", round(time.time() - t0, 1), "cache:", delta.cache_info().currsize)
