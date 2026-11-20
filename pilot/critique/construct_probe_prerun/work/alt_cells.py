"""Pre-run review scratch: (1) can the fixed cells be passed by a rule that never compares v with c? (2) an example alternative
cell / v' set where neither the effective value alone nor the size of the change separates the targets. Kernel targets. No model."""
import sys
sys.argv = [sys.argv[0], "L2"]
from pilot import ladder as L
def tgt(v, c): return L.target(L.belief("L2", c), v)
def table(INFO):
    trade_t, walk_t, rows = set(), set(), []
    for (v, c), (rel, irr) in INFO.items():
        for arm, ve in (("base", v), ("rel", rel), ("irr", irr)):
            t = tgt(ve, c); (walk_t if t == [0] else trade_t).add(ve); rows.append((v, c, arm, ve, ve - v, t))
    for r in rows: print("  ", r)
    print("  effective values with target c:", sorted(trade_t), " with target walk:", sorted(walk_t),
          " overlap:", sorted(trade_t & walk_t))
    rel = [abs(r[4]) for r in rows if r[2] == "rel"]; irr = [abs(r[4]) for r in rows if r[2] == "irr"]
    print("  |change| relevant:", sorted(rel), " irrelevant:", sorted(irr), " separable by size:", max(irr) < min(rel))
print("fixed CP cells"); table({(10, 4): (2, 7), (10, 6): (3, 8), (14, 8): (4, 11), (18, 4): (2, 9), (18, 8): (4, 12),
                                (2, 4): (7, 3), (4, 6): (9, 5), (6, 8): (12, 7)})
print("example alternative"); table({(6, 4): (3, 5), (8, 6): (5, 7), (10, 4): (2, 5), (14, 8): (7, 9), (18, 4): (3, 5),
                                     (2, 4): (5, 3), (4, 6): (7, 5), (2, 8): (10, 7)})
print("example alternative 2 (adds a within-value baseline contrast at v = 6)")
table({(6, 4): (3, 5), (8, 6): (5, 7), (10, 4): (2, 5), (14, 8): (7, 9), (18, 4): (3, 5),
       (4, 6): (7, 5), (6, 8): (9, 7), (2, 8): (10, 7)})
