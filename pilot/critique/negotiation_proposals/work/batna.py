"""Reviewer scratch: what a verified outside option b does to the optimum of the selected game.
Model A (the proposal's words): walking away pays v-b, a rejected offer pays 0.
Model B (the natural reading): the other stall is still there after a rejection, so rejection also pays max(0, v-b).
No model is run; kernel.py is only imported."""
import sys; sys.path.insert(0, "/home/user/haggle-sycophancy")
from fractions import Fraction as Fr
import kernel as K
PMAX = 9
TYPES = ("rational", "gullible", "floor_low")
mu = {"rational": Fr(7, 10), "gullible": Fr(3, 20), "floor_low": Fr(3, 20)}
def P(b, a): return sum(p for k, p in b.items() if K.accepts(k, a, PMAX))
def argmax(U):
    m = max(U.values()); return sorted(a for a, u in U.items() if u == m), m
def modelA(b, v, o):
    U = {a: (v - a) * P(b, a) for a in range(1, PMAX + 1)}; U[0] = max(Fr(0), Fr(v - o))
    return argmax(U)
def modelB(b, v, o):
    w = max(Fr(0), Fr(v - o))
    U = {a: (v - a) * P(b, a) + (1 - P(b, a)) * w for a in range(1, PMAX + 1)}; U[0] = w
    return argmax(U)
for hist in (False, True):
    b = K.belief(mu, PMAX, hist)
    print("history", hist)
    for v in (2, 4, 7, 9, 11, 13, 16, 18, 6, 10, 14):
        A0 = sorted(K.optimal(b, Fr(v), PMAX, True))
        row = []
        for o in range(1, 10):
            a, _ = modelA(b, v, o); bb, _ = modelB(b, v, o)
            # value-cap equivalence check for model B: optimum at value min(v, o)
            eq = sorted(K.optimal(b, Fr(min(v, o)), PMAX, True))
            row.append(f"b={o}: A{a} B{bb} cap{eq}")
        print(f" v={v:2d} base {A0} | " + " | ".join(row))
