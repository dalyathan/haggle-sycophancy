"""Scratch sizing for the next-step recommendation. No model is run."""
import sys, os, itertools, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
from fractions import Fraction as Fr
import kernel as K
PMAX = 9
def tgt(v, c):
    b = {("rational", c): Fr(1)}
    A = K.optimal(b, Fr(v), PMAX, True)
    return [0] if K.no_trade(b, A, PMAX) else sorted(A)
print("cell (v, c): baseline target -> target after the information item")
trade = [(6,2),(6,4),(8,2),(8,6),(12,4),(12,8),(16,6),(16,9)]
walk = [(2,3),(2,7),(3,5),(3,8),(4,6),(4,9)]
for v, c in trade:
    print("  half  ", (v, c), tgt(v, c), "->", tgt(Fr(v, 2), c))
for v, c in walk:
    print("  double", (v, c), tgt(v, c), "->", tgt(2 * v, c))
# power of a one-sided Fisher exact test, control arm n0 against pressure arm n1
from math import comb
def fisher_p(a, n0, b, n1):   # P(pressure count >= b | margins)
    N, Kk = n0 + n1, a + b
    return sum(comb(n1, x) * comb(n0, Kk - x) for x in range(b, min(n1, Kk) + 1)) / comb(N, Kk)
def binom(n, p, k): return comb(n, k) * p**k * (1 - p)**(n - k)
def power(n0, p0, n1, p1):
    tot = 0.0
    for a in range(0, n0 + 1):
        pa = binom(n0, p0, a)
        if pa < 1e-9: continue
        for b in range(0, n1 + 1):
            pb = binom(n1, p1, b)
            if pb < 1e-9: continue
            if fisher_p(a, n0, b, n1) < 0.05: tot += pa * pb
    return tot
for n0, n1 in ((84, 84), (168, 168)):
    for p0, p1 in ((0.03, 0.08), (0.03, 0.13), (0.03, 0.18), (0.05, 0.15), (0.05, 0.20)):
        print(f"n control {n0}, n pressure {n1}: error rate {p0} against {p1}: power {power(n0, p0, n1, p1):.2f}")
# compute
print("v0.9 selected design, both arms, tokens per item -> CPU-years at 0.3 s/token; GPU-days at 1,000 and 3,000 tokens/s")
for tok in (300, 2200, 2800, 5000):
    T = 106488 * 2 * tok
    print(f"  {tok} tokens/item: {T/1e6:.0f} M tokens; CPU {T*0.3/3600/24/365:.1f} years; GPU {T/1000/86400:.1f} / {T/3000/86400:.1f} days")
print("100 CPU-hours =", round(100*3600/0.3/1e6, 2), "M tokens =", round(100*3600/0.3/300), "trivial-rung items or", round(100*3600/0.3/2200), "full-game no-history items")
