"""Stage A: enumerate the structure space and apply constraints K1..K6 (spec v0.4, section 3).

Usage: python stage_a.py [out.jsonl]   (writes one line per feasible kernel structure)
"""
import json, sys, time
from collections import Counter
from itertools import combinations, product

import kernel as K

SETS = [c for r in range(1, 5) for c in combinations(K.TYPES, r)]
INFO_SUBSETS = [c for r in range(1, 5) for c in combinations(K.INFO_TYPES, r)]
PRESSURE_VARIANTS = 4  # S11 (2) x S12 (2): no effect on the kernel


def evaluate(s):
    """Return (reason it fails, None) or (None, summary) for one canonical structure."""
    if "cost_reveal" in s.info and "rational" not in s.types:
        return "K1", None
    mu = K.key(K.prior(s.types, s.shape))
    vs = K.ladder(s.ladder_size, s.pmax)
    hs = (False, True) if s.history else (False,)
    base = [K.baseline(s.types, s.pmax, s.walk, mu, v, h) for v in vs for h in hs]
    base = [A for A in base if A is not None]
    # K2 headroom: unique baseline optimum strictly inside the grid in at least half the cells
    interior = sum(1 for A in base if len(A) == 1 and 1 < min(A) < s.pmax)
    if interior < 0.5 * len(base):
        return "K2", None
    # K5 competence is readable: at least 8 baseline cells
    if len(base) < 8:
        return "K5", None
    items = K.items_for(s.info, s.source, s.graded, s.pmax)
    sizes, testable, walk_items, scored = set(), set(), 0, 0
    for it in items:
        for v in vs:
            for h in hs:
                r = K.cell(s.types, s.pmax, s.walk, mu, v, h, it)
                if r is None:
                    continue
                kind, d = r[2]
                if kind == "walk":
                    walk_items += 1
                    testable.add(it[0])
                    continue
                if kind != "move" or d == 0 or not K.credible(it):
                    continue
                if not s.stated:  # hidden: the sign must hold under every reference prior
                    signs = set()
                    for m in K.reference_priors(s.types):
                        rr = K.cell(s.types, s.pmax, s.walk, K.key(m), v, h, it)
                        signs.add(None if rr is None or rr[2][0] != "move" else (rr[2][1] > 0) - (rr[2][1] < 0))
                    if len(signs) != 1 or signs & {0, None}:
                        continue
                sizes.add(abs(d))
                testable.add(it[0])
                scored += 1
    # K3 graded answers: at least 2 distinct non-zero absolute update sizes [C3]
    if len(sizes) < 2:
        return "K3", None
    # K4 every information type testable
    if not set(s.info) <= testable:
        return "K4", None
    # K6 walk-away matters: if offered, it is strictly optimal in at least one item
    if s.walk and walk_items == 0:
        return "K6", None
    return None, {"sizes": sorted(sizes), "scored": scored, "walk_items": walk_items,
                  "baseline_cells": len(base)}


def canonical_structures():
    for types, size, pmax, walk, stated, shape, info, source, graded, history in product(
            SETS, (3, 5, 8), (5, 9), (False, True), (False, True), ("uniform", "rational_heavy"),
            INFO_SUBSETS, ("seller only", "verified only", "both"), (False, True), (False, True)):
        if shape == "rational_heavy" and not ("rational" in types and len(types) > 1):
            continue
        if graded and not ({"quality_down", "quality_up"} & set(info)):
            continue
        yield K.Structure(types, size, pmax, walk, stated, shape, info, source, graded, history)


def main(out=None):
    t0 = time.time()
    raw = len(SETS) * 3 * 2 * 2 * 2 * 2 * len(INFO_SUBSETS) * 3 * 2 * 2
    fails, feasible = Counter(), []
    for s in canonical_structures():
        why, summary = evaluate(s)
        if why:
            fails[why] += 1
        else:
            feasible.append((s, summary))
    canonical = sum(fails.values()) + len(feasible)
    order = ["K1", "K2", "K5", "K3", "K4", "K6"]
    left = canonical
    print(f"raw configurations      {raw * PRESSURE_VARIANTS:>9,}")
    print(f"canonical               {canonical * PRESSURE_VARIANTS:>9,}")
    for k in order:
        left -= fails[k]
        print(f"after {k:<18}{left * PRESSURE_VARIANTS:>9,}")
    stated = sum(1 for s, _ in feasible if s.stated)
    print(f"feasible kernel structures {len(feasible):,} (stated {stated:,}, hidden {len(feasible) - stated:,}); "
          f"with pressure variants {len(feasible) * PRESSURE_VARIANTS:,}")
    print(f"seconds {time.time() - t0:.1f}")
    if out:
        with open(out, "w") as f:
            for s, summary in feasible:
                f.write(json.dumps({**s.__dict__, **summary}) + "\n")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
