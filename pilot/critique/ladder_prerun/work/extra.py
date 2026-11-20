import sys, io, contextlib, json, numpy as np
sys.path.insert(0, '.'); sys.path.insert(0, 'work')
from fractions import Fraction as Fr
import kernel as K
import sim
from sim import run, pt
opt = lambda p: pt(*p["target"])
# max uniform-noise share with which the optimal policy still passes each rung
for rung in ("L1", "L2", "L3", "L4b"):
    last = None
    for nz in np.arange(0, 0.8, 0.01):
        with contextlib.redirect_stdout(io.StringIO()):
            ok = run(rung, "o", opt, float(nz))
        if ok: last = nz
    print(rung, "optimal + uniform noise passes up to noise share", last)
# the same for 'noise = mass spread on neighbours' (target +-1) at L3/L4b
def blur(w):
    def f(p):
        q = np.zeros(10)
        for a in p["target"]:
            q[a] += (1 - w) / len(p["target"])
            for d in (-1, 1):
                b = min(9, max(1, a + d)) if a else 1
                q[b] += w / 2 / len(p["target"])
        return q
    return f
for rung in ("L3", "L4b"):
    for w in (0.3, 0.5, 0.6):
        run(rung, f"optimal blurred to +-1 with weight {w}", blur(w))
# L3 alternatives
def tgt(b, v):
    A = K.optimal(b, Fr(v), 9, True); return sorted(A)
for name, costs in [("uniform 1..8", range(1, 9)), ("uniform 1..8 | 1 rejected", range(2, 9)), ("uniform 1..8 | 2 rejected", range(3, 9)),
                    ("uniform 1..4", range(1, 5)), ("uniform 5..8", range(5, 9))]:
    b = {("rational", c): Fr(1, len(costs)) for c in costs}
    print(name, {v: tgt(b, v) for v in (2, 6, 10, 14, 18)})
# reference regrets on L4
L, P = sim.build("L4b")
cells = {(p["v"], p["hist"]): p for p in P}
best = lambda p: max(max(p["U"]), 0)
print("L4 uniform over 9 offers", np.mean([best(p) - np.mean(p["U"]) for p in cells.values()]),
      "over ten", np.mean([best(p) - 0.9 * np.mean(p["U"]) for p in cells.values()]))
# R3 rows vs L4b annotations
R = [json.loads(l) for l in open("pilot/out/readout_R3.jsonl")]
B = [r for r in R if r["kind"] == "base"]
print(len(B), "R3 base rows; U/target equal to L4b:", all(np.allclose(r["U"], cells[(r["v"], r["hist"])]["U"]) and r["target"] == cells[(r["v"], r["hist"])]["target"] for r in B))
print("R3 base (ctx,para,v,hist) set == L4b:", sorted((r["ctx"], r["para"], r["v"], r["hist"]) for r in B) == sorted((p["ctx"], p["para"], p["v"], p["hist"]) for p in P))
# L4 third-person prompt vs L4b: same after substitution?
import pilot.readout as RO
RO.VARIANT = "R3"; Q = [q for q in RO.build() if q["kind"] == "base"]
import re
def norm(s): return re.sub(r"\s+", " ", s)
q = [x for x in Q if x["ctx"] == 0 and x["para"] == 0 and x["v"] == 6 and x["hist"]][0]
p = [x for x in P if x["ctx"] == 0 and x["para"] == 0 and x["v"] == 6 and x["hist"]][0]
print(len(q["messages"][0]["content"].split()), len(p["messages"][0]["content"].split()), "words L4 / L4b system")
for rung in ("L1", "L2", "L3"):
    _, PP = sim.build(rung)
    print(rung, "system words", len(PP[0]["messages"][0]["content"].split()), "unique prefixes", len({x["messages"][0]["content"] for x in PP}), "of", len(PP),
          "hash unique", len({x["hash"] for x in PP}))
