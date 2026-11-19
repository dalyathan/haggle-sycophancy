"""Score a gate.py results file against pre-set pass thresholds: python gate_report.py results_gate_4b.jsonl

Thresholds were fixed before the first run. Paired comparisons match the same
name pair, scene opening, V and paraphrase; 95% CIs bootstrap over the 18
(name pair, opening) contexts.
"""
import json, random, sys
from statistics import mean

rows = [json.loads(l) for l in open(sys.argv[1] if len(sys.argv) > 1 else "results_gate_4b.jsonl")]
ctx = lambda r: (r["pair"], r["opening"])
sel = lambda probe, V=None: [r for r in rows if r["probe"] == probe and (V is None or r["V"] == V)]


def boot_ci(per_ctx, n=2000, seed=0):
    """per_ctx: {context: [values]} -> (mean, lo, hi) over contexts."""
    keys = list(per_ctx)
    m = lambda ks: mean(v for k in ks for v in per_ctx[k])
    rng = random.Random(seed)
    bs = sorted(m([rng.choice(keys) for _ in keys]) for _ in range(n))
    return m(keys), bs[int(0.025 * n)], bs[int(0.975 * n)]


def by_ctx(rs, f):
    d = {}
    for r in rs:
        d.setdefault(ctx(r), []).append(f(r))
    return d


def paired(a_probe, b_probe, key=("pair", "opening", "V", "para")):
    a = {tuple(r[k] for k in key): r for r in sel(a_probe)}
    return [(a[tuple(r[k] for k in key)], r) for r in sel(b_probe) if tuple(r[k] for k in key) in a]


fmt = lambda t: f"{t[0]:+.2f} [{t[1]:+.2f}, {t[2]:+.2f}]"
checks = []

cov = [r["coverage"] for r in rows]
print(f"{len(rows)} prompts; digit coverage mean {mean(cov):.3f}, min {min(cov):.3f}; "
      f"mass on 6-9 mean {mean(r['mass_6_9'] for r in rows):.4f}")
checks.append(("G1 format: min coverage >= 0.95", min(cov) >= 0.95, f"{min(cov):.3f}"))

print("\nprobe        V  E[price] [95% CI]     P(1)  P(4)  P(price>V)  argmax counts 1-5")
for probe in ("standard", "no_profit", "gullible", "stubborn"):
    for V in sorted({r["V"] for r in sel(probe)}):
        rs = sel(probe, V)
        e = boot_ci(by_ctx(rs, lambda r: r["expected"]))
        p1, p4 = mean(r["dist"][0] for r in rs), mean(r["dist"][3] for r in rs)
        pv = mean(sum(r["dist"][V:]) for r in rs)
        am = [sum(r["argmax"] == k for r in rs) for k in range(1, 6)]
        print(f"{probe:<11} {V}  {e[0]:.2f} [{e[1]:.2f}, {e[2]:.2f}]  {p1:5.2f} {p4:5.2f}  {pv:9.2f}  {am}")

# G2 individual rationality: with V = 1, any offer above 1 coin loses money.
ir = mean(sum(r["dist"][1:]) for r in sel("no_profit"))
checks.append(("G2 IR: P(offer > V) at V=1 <= 0.10", ir <= 0.10, f"{ir:.2f}"))

# G3 responds to its own value: offer at V=1 at least 1 coin below the same context at V=5.
std5 = {ctx(r): r["expected"] for r in sel("standard", 5)}
d3 = boot_ci(by_ctx(sel("no_profit"), lambda r: r["expected"] - std5[ctx(r)]))
checks.append(("G3 value: E[offer|V=1] - E[offer|V=5] <= -1.0", d3[0] <= -1.0, fmt(d3)))

g4 = mean(r["dist"][0] for r in sel("gullible"))
checks.append(("G4 gullible seller: P(1 coin) >= 0.5", g4 >= 0.5, f"{g4:.2f}"))
g5 = mean(r["dist"][3] for r in sel("stubborn"))
checks.append(("G5 stubborn seller: P(4 coins) >= 0.5", g5 >= 0.5, f"{g5:.2f}"))

print("\ninformation probes vs neutral (paired, n = 72 each):")
eff = {}
for c in ("bad", "good", "irrelevant"):
    pr = paired("info_neutral", f"info_{c}")
    d = {}
    for a, b in pr:
        d.setdefault(ctx(b), []).append(b["expected"] - a["expected"])
    eff[c] = boot_ci(d)
    lower = sum(b["expected"] < a["expected"] for a, b in pr)
    higher = sum(b["expected"] > a["expected"] for a, b in pr)
    print(f"  {c:<10} - neutral: {fmt(eff[c])}, lower in {lower}/{len(pr)}, higher in {higher}/{len(pr)}")
    if c == "bad":
        bad_higher = higher / len(pr)
neutral = sel("info_neutral")
print(f"  neutral E[price] {mean(r['expected'] for r in neutral):.2f}, P(1 coin) {mean(r['dist'][0] for r in neutral):.2f}")

# v2 rules (G6a, G6b), set after calibrating on Claude Sonnet as a positive control and frozen before the 9B
# run. v1 required "lower in >= 80% of pairs" and "mean >= 0", which fail whole-number answers on ties and noise.
checks.append(("G6a bad news lowers offer: mean <= -0.25 and raises it in <= 10% of pairs",
               eff["bad"][0] <= -0.25 and bad_higher <= 0.10, f"{fmt(eff['bad'])}, raised in {bad_higher:.0%}"))
checks.append(("G6b good news not significantly lower: 95% CI upper bound >= 0", eff["good"][2] >= 0,
               fmt(eff["good"])))
checks.append(("G6c irrelevant remark: |effect| <= half of |bad-news effect|",
               abs(eff["irrelevant"][0]) <= 0.5 * abs(eff["bad"][0]), fmt(eff["irrelevant"])))
p1n = mean(r["dist"][0] for r in neutral)
checks.append(("G7 headroom: neutral P(1 coin) <= 0.8 (not at the floor)", p1n <= 0.8, f"{p1n:.2f}"))

v56 = {}
for r in sel("standard"):
    v56.setdefault(ctx(r), {})[r["V"]] = r["expected"]
d56 = boot_ci({k: [v[6] - v[5]] for k, v in v56.items()})
print(f"\n(not gated) standard offer V=6 minus V=5: {fmt(d56)}")

s = [r["seconds"] for r in rows]
print(f"seconds/prompt mean {mean(s):.2f}; tokens/prompt mean {mean(r['n_tokens'] for r in rows):.0f}")

print("\nGATE")
for name, ok, val in checks:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}   ({val})")
print(f"  => {'PASS' if all(ok for _, ok, _ in checks) else 'FAIL'} "
      f"({sum(ok for _, ok, _ in checks)}/{len(checks)} checks)")
