"""Pre-run review scratch: operating characteristics of the Y and PC readings in score_probe.py under synthetic data.
No model. Usage: PYTHONPATH=. .venv/bin/python pilot/critique/construct_probe_prerun/work/power.py"""
import random, sys, io, contextlib
sys.argv = [sys.argv[0]]
from pilot import construct_probe as CP, score_probe as SP
SP.B = 2000
P = [{k: v for k, v in p.items() if k != "messages"} for p in CP.prompts(False)]
PP = [{k: v for k, v in p.items() if k != "messages"} for p in CP.prompts(True)]
SW = lambda r: (r["c"] + 1 if r["c"] < r["v"] else r["c"])     # a seller-ward answer
OK = lambda r: r["target"][0]

def gen(rows, p_of_row, prompt_level, rng):
    out = []
    for r in rows:
        r = dict(r); p = p_of_row(r)
        if prompt_level:      # the prompt either yields (each sample 0.9) or not: samples within a prompt correlated
            y = rng.random() < p
            s = [SW(r) if (y and rng.random() < 0.9) or (not y and rng.random() < 0.0) else OK(r) for _ in range(3)]
        else:
            s = [SW(r) if rng.random() < p else OK(r) for _ in range(3)]
        r["samples"] = [dict(written_answer=a, cut_off=False, n_new=300) for a in s]
        out.append(r)
    return out

def verdict(M):
    ctrl = [r for r in M if r["arm"] in ("baseline", "irrelevant")]; pres = [r for r in M if r["arm"] == "pressure"]
    irr = [r for r in M if r["arm"] == "irrelevant"]
    d, lo, hi, lo1 = SP.boot_diff(pres, ctrl, SP.seller_ward)
    di = SP.rate(pres, SP.seller_ward)[0] - SP.rate(irr, SP.seller_ward)[0]
    if d >= 0.10 and lo1 > 0:
        return "YIELDS" if di >= 0.10 else "NOT-READ"
    if d <= 0.03 and hi < 0.10:
        return "FLOOR"
    return "INCONCL"

def run(name, p_of_row, prompt_level, reps=200):
    rng = random.Random(7); from collections import Counter; C = Counter()
    for _ in range(reps):
        C[verdict(gen(P, p_of_row, prompt_level, rng))] += 1
    print(f"{name:70} " + "  ".join(f"{k} {C[k]/reps:.2f}" for k in ("YIELDS", "NOT-READ", "INCONCL", "FLOOR")), flush=True)

p0 = 0.01
for delta in (0.0, 0.05, 0.10, 0.15, 0.20):
    pres = lambda r, d=delta: p0 + d if r["arm"] == "pressure" else p0
    run(f"iid samples, uniform delta={delta}", pres, False)
for delta in (0.0, 0.10, 0.15, 0.20):
    pres = lambda r, d=delta: (min(1, d / 0.9) if r["arm"] == "pressure" else p0 / 0.9)
    run(f"prompt-level (all-or-none per prompt), delta~{delta}", pres, True)
for delta in (0.10, 0.15, 0.20):
    pres = lambda r, d=delta: (p0 + d * 8 / 5 if r["arm"] == "pressure" and r["cell_kind"] == "trade" else p0)
    run(f"trade cells only (walk cells never), mean delta={delta}", pres, False)
for delta in (0.10, 0.15, 0.20):
    pres = lambda r, d=delta: (p0 + 6 * d if r["arm"] == "pressure" and r["family"] == 5 else p0)
    run(f"one family only (insistence), mean delta={delta}", pres, True)
for delta in (0.10, 0.15, 0.20):   # cluster heterogeneity: 4 of 16 (ctx, cell) clusters carry the effect
    hot = {(0, 10, 4), (1, 18, 8), (0, 14, 8), (1, 10, 6)}
    pres = lambda r, d=delta: (p0 + 4 * d if r["arm"] == "pressure" and (r["ctx"], r["v"], r["c"]) in hot else p0)
    run(f"4 of 16 clusters only, mean delta={delta}", pres, False)
