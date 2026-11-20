import sys, json, io, contextlib, numpy as np
sys.path.insert(0, '.'); sys.path.insert(0, 'work')
from dump import build
import pilot.analyze_ladder as A

def rows(rung, policy, noise=0.0, P=None):
    L, P = build(rung)
    out = []
    for p in P:
        q = np.asarray(policy(p), float); q = q / q.sum()
        q = (1 - noise) * q + noise * np.ones(10) / 10
        offer = q[1:] / max(q[1:].sum(), 1e-12); eo = float((np.arange(1, 10) * offer).sum())
        r = {k: v for k, v in p.items() if k != "messages"}
        r.update(probs=q.tolist(), coverage=1.0, walk=float(q[0]), exp_offer=eo, exp_u=(eo - 1) / 8,
                 sd_offer=float(np.sqrt((((np.arange(1, 10) - eo) ** 2) * offer).sum())))
        out.append(r)
    return out

def pt(*answers):
    q = np.zeros(10)
    for a in answers: q[a] += 1
    return q

def run(rung, name, policy, noise=0.0, verbose=False):
    R = rows(rung, policy, noise)
    path = f"work/_tmp_{rung}.jsonl"
    with open(path, "w") as f:
        for r in R: f.write(json.dumps(r) + "\n")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ok = A.report(path)
    lines = buf.getvalue().splitlines()
    v = [l for l in lines if l.startswith("VERDICT")][0]
    print(f"[{rung}] {name} (noise {noise}): {v}")
    if verbose:
        for l in lines[1:]:
            if l[:2] in ("P1","P2","P3","P4","A2","A4","A5","A6"): print("     ", l)
    return ok

half = lambda v: int(min(9, max(1, round(v / 2))))
if __name__ == "__main__":
    V = "-v" in sys.argv
    print("---- L1")
    for name, pol in [("optimal", lambda p: pt(*p["target"])), ("uniform", lambda p: np.ones(10)), ("always 1", lambda p: pt(1)),
                      ("always 2", lambda p: pt(2)), ("always 3", lambda p: pt(3)), ("always 5", lambda p: pt(5)),
                      ("first digit of v", lambda p: pt(int(str(p["v"])[0]))), ("half value", lambda p: pt(half(p["v"]))),
                      ("1 w.p. .4 else 2/3 ", lambda p: .4*pt(1)+.3*pt(2)+.3*pt(3)),
                      ("1 at .4, rest uniform over 2..5", lambda p: .4*pt(1)+.15*pt(2)+.15*pt(3)+.15*pt(4)+.15*pt(5)),
                      ("always 2 except v=2 -> 1", lambda p: pt(1 if p["v"]==2 else 2))]:
        run("L1", name, pol, verbose=V)
    print("---- L2")
    opt = lambda p: pt(*p["target"])
    for name, pol in [("optimal", opt), ("uniform", lambda p: np.ones(10)), ("copy cost", lambda p: pt(p["c"])),
                      ("copy cost, walk iff v==2", lambda p: pt(0 if p["v"] == 2 else p["c"])),
                      ("copy cost, walk iff v<=6", lambda p: pt(0 if p["v"] <= 6 else p["c"])),
                      ("copy cost, walk iff c>=7", lambda p: pt(0 if p["c"] >= 7 else p["c"])),
                      ("copy cost w.p. .5, walk w.p. .5 everywhere", lambda p: .5*pt(0)+.5*pt(p["c"])),
                      ("copy cost w.p. .6, walk w.p. .4 everywhere", lambda p: .6*pt(0)+.4*pt(p["c"])),
                      ("always walk", lambda p: pt(0)), ("always 5", lambda p: pt(5)), ("always 9", lambda p: pt(9)),
                      ("cost+1 capped 9, walk iff c>v", lambda p: pt(0 if p["c"] > p["v"] else min(9, p["c"]+1))),
                      ("cost+2 capped 9, walk iff c>v", lambda p: pt(0 if p["c"] > p["v"] else min(9, p["c"]+2))),
                      ("half value, walk iff v==2", lambda p: pt(0 if p["v"]==2 else half(p["v"]))),
                      ("max(c, half v) walk iff v==2", lambda p: pt(0 if p["v"]==2 else max(p["c"], half(p["v"])))),
                      ("walk iff c>v else .5 on c, .5 on 9", lambda p: pt(0) if p["c"]>p["v"] else .5*pt(p["c"])+.5*pt(9)),
                      ]:
        run("L2", name, pol, verbose=V)
    print("---- L3")
    lo = lambda p: pt(min(a for a in p["target"] if a) if any(p["target"]) else 0)
    hi = lambda p: pt(max(p["target"]))
    L3nohist = {2: 1, 6: 3, 10: 5, 14: 7, 18: 8}
    for name, pol in [("optimal (uniform over tie set)", opt), ("optimal, lower tie", lo), ("optimal, upper tie", hi),
                      ("uniform", lambda p: np.ones(10)), ("half value (history ignored)", lambda p: pt(half(p["v"]))),
                      ("no-history optimum, history ignored", lambda p: pt(L3nohist[p["v"]])),
                      ("always 5", lambda p: pt(5)), ("always 4", lambda p: pt(4)),
                      ("v-1 capped 8", lambda p: pt(min(8, p["v"]-1))), ("v-1 capped 8, +1 capped after history", lambda p: pt(min(9 if p["hist"] else 8, p["v"]-1+ (1 if p["hist"] else 0)))),
                      ("v-1 capped 8; with history 9 at v>=10", lambda p: pt(9 if (p["hist"] and p["v"] >= 10) else min(8, p["v"]-1))),
                      ("always 5, history -> 6", lambda p: pt(6 if p["hist"] else 5)),
                      ("1 if v=2 else 5; history +1", lambda p: pt((1 if p["v"]==2 else 5) + (1 if p["hist"] else 0))),
                      ("v<10: 2, else 7; hist +1", lambda p: pt((2 if p["v"]<10 else 7) + (1 if p["hist"] else 0))),
                      ]:
        run("L3", name, pol, verbose=V)
    print("---- L4b")
    for name, pol in [("optimal (uniform over tie set)", opt), ("optimal, lower tie", lo), ("optimal, upper tie", hi), ("uniform", lambda p: np.ones(10)),
                      ("half value", lambda p: pt(half(p["v"]))), ("always 5", lambda p: pt(5)), ("always 4", lambda p: pt(4)),
                      ("L3-optimal policy (ignores mixture)", lambda p: pt(L3nohist[p["v"]] + (1 if p["hist"] and p["v"] in (6,10,14) else 0))),
                      ]:
        run("L4b", name, pol, verbose=V)
    print("---- noisy optimal (share of uniform noise)")
    for rung in ("L1", "L2", "L3", "L4b"):
        for nz in (0.2, 0.4, 0.5, 0.6):
            run(rung, "optimal", opt, nz)
