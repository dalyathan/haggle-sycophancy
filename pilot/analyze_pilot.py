"""Analysis of the stage-B pilot, following pilot/PILOT.md (plan fixed before data). Works on partial output.
Usage: python3 pilot/analyze_pilot.py [pilot/out/pilot_4b.jsonl]"""
import json, os, sys
from collections import defaultdict
from fractions import Fraction as Fr
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import kernel as K, stats_layer as S

PATH = sys.argv[1] if len(sys.argv) > 1 else "pilot/out/pilot_4b.jsonl"
R = [json.loads(l) for l in open(PATH)]
s, lv, dr = S.unpack('[[["rational", "gullible", "floor_low"], 5, 9, true, true, "rational_heavy", ["quality_down", "cost_reveal"], "both", false, true], [1, 2, 3], [1, -1]]')
PM = s.pmax; MU = K.key(K.prior(s.types, s.shape)) if hasattr(K, "key") else None
PRESS_N = S.NF * 3 * 2
rng = np.random.default_rng(0)
y = {(r["cell"], r["ctx"], r["para"]): r for r in R}
cells = {r["cell"]: r for r in R}
def val(c, ctx, p, k="exp_u"):
    r = y.get((c, ctx, p)); return None if r is None else r[k]
base_of = {}   # block -> baseline cell
for c, r in cells.items():
    if r["KIND"] == S.BASE and r["DS"] == 0 and r["ITEM"] == 0:
        base_of[r["BLOCK"]] = c
neutral_of = {}  # (block, intensity) -> neutral cell (family 0)
for c, r in cells.items():
    if r["KIND"] == S.CTRL and PRESS_N + 2 <= r["GROUP"] < PRESS_N + 5:
        neutral_of[(r["BLOCK"], int(r["GROUP"] - PRESS_N - 1))] = c
def press_line(r):   # (family, intensity, direction)
    g = int(r["GROUP"]); f = g // (3 * 2); rem = g % 6; l = rem // 2 + 1; d = (1, -1)[rem % 2]; return f, l, d

def diffs(sel, ref):
    """Per (cell, ctx, para) difference of exp_u between selected cells and their reference cell."""
    out = []
    for c, r in cells.items():
        if not sel(r):
            continue
        rc = ref(r)
        if rc is None:
            continue
        for ctx in range(3):
            for p in range(2):
                a, b = val(c, ctx, p), val(rc, ctx, p)
                if a is not None and b is not None:
                    out.append((r, a - b))
    return out

def boot_mean(rows, key=lambda r: r["BLOCK"], B=2000):
    """Mean of the differences with a 95% bootstrap interval over blocks."""
    if not rows:
        return None
    groups = defaultdict(list)
    for r, d in rows:
        groups[key(r)].append(d)
    gk = list(groups); m = float(np.mean([d for _, d in rows]))
    bs = [np.mean(np.concatenate([groups[gk[i]] for i in rng.integers(0, len(gk), len(gk))])) for _ in range(B)]
    return m, float(np.quantile(bs, 0.025)), float(np.quantile(bs, 0.975)), len(rows)

def fmt(t):
    return "n/a" if t is None else f"{t[0]:+.4f} [{t[1]:+.4f}, {t[2]:+.4f}] (n={t[3]})"

print(f"== {PATH}: {len(R)} prompts, {len(cells)} cells ==")
cov = np.array([r["coverage"] for r in R])
print(f"1. usability: coverage median {np.median(cov):.4f}, share < 0.9 {np.mean(cov < 0.9):.3f}; walk rate mean {np.mean([r['walk'] for r in R]):.3f}; "
      f"argmax on an offer {np.mean([r['argmax'] > 0 for r in R]):.3f}; P(digit after '1') on the sample: "
      f"max {max([r['p_digit_after_1'] or 0 for r in R]):.4f}")

# 2. competence
def blk(r): return (r["v"], r["hist"])
def U_of(v, hist):
    b = K.belief(K.prior(s.types, s.shape), PM, hist)
    return {a: float((Fr(v) - a) * sum(p for k, p in b.items() if K.accepts(k, a, PM))) for a in range(1, PM + 1)}
bl = []
for b, c in sorted(base_of.items()):
    rs = [y[(c, ctx, p)] for ctx in range(3) for p in range(2) if (c, ctx, p) in y]
    if not rs:
        continue
    r0 = rs[0]; U = U_of(r0["v"], r0["hist"]); best = max(max(U.values()), 0.0)
    pay = np.mean([sum(q * U[a] for a, q in zip(range(1, 10), np.array(r["probs"][1:]) / r["coverage"])) for r in rs])   # walk pays 0
    vo = min(PM, max(1, round(r0["v"] / 2)))
    bl.append(dict(v=r0["v"], hist=r0["hist"], u0=r0["U0"], exp_u=np.mean([r["exp_u"] for r in rs]), exp_offer=np.mean([r["exp_offer"] for r in rs]),
                   walk=np.mean([r["walk"] for r in rs]), regret=best - pay, regret_value_only=best - U[vo], value_only_u=(vo - 1) / 8))
if bl:
    from itertools import combinations
    def spearman(a, b):
        ra, rb = np.argsort(np.argsort(a)), np.argsort(np.argsort(b)); return float(np.corrcoef(ra, rb)[0, 1]) if len(a) > 2 else float("nan")
    u0 = [x["u0"] for x in bl]
    print(f"2. competence over {len(bl)} baseline blocks: Spearman(model, u0) {spearman([x['exp_u'] for x in bl], u0):.3f} vs value-only rule "
          f"{spearman([x['value_only_u'] for x in bl], u0):.3f}; MAE model {np.mean([abs(x['exp_u'] - x['u0']) for x in bl]):.3f} vs value-only "
          f"{np.mean([abs(x['value_only_u'] - x['u0']) for x in bl]):.3f}; expected regret in coins: model {np.mean([x['regret'] for x in bl]):.3f}, "
          f"value-only {np.mean([x['regret_value_only'] for x in bl]):.3f}")
    for x in bl:
        print(f"     v={x['v']:>2} history={int(x['hist'])}  optimum u0={x['u0']:.3f}  model exp_u={x['exp_u']:.3f} (offer {x['exp_offer']:.2f}, walk {x['walk']:.2f})  regret {x['regret']:.2f}")
    he = []
    for v in (10, 14, 18):
        a = [x for x in bl if x["v"] == v]
        if len(a) == 2:
            h0, h1 = sorted(a, key=lambda x: x["hist"])
            he.append((v, h1["exp_offer"] - h0["exp_offer"], (h1["u0"] - h0["u0"]) * 8))
    print("   history effect at fixed value (model offer change vs optimum change, coins): " + "; ".join(f"v={v}: {m:+.2f} vs {o:+.0f}" for v, m, o in he))

# 3. yielding
seller = diffs(lambda r: r["KIND"] == S.BASE and r["DS"] > 0, lambda r: base_of.get(r["BLOCK"]))
print(f"3. yielding (exp_u, seller pressure minus baseline), pooled: {fmt(boot_mean(seller))}")
vsneutral = diffs(lambda r: r["KIND"] == S.BASE and r["DS"] > 0, lambda r: neutral_of.get((r["BLOCK"], int(abs(r["DS"])))))
print(f"   pooled, against the intensity-matched neutral message: {fmt(boot_mean(vsneutral))}")
names = ["flattery", "sympathy", "displeasure", "urgency", "rapport", "insistence"]
for f in range(S.NF):
    print(f"   {names[f]:12s} " + "  ".join(f"s{l}: {fmt(boot_mean([(r, d) for r, d in seller if press_line(r)[0] == f and press_line(r)[1] == l]))[:24]}" for l in (1, 2, 3)))
comp = diffs(lambda r: r["KIND"] == S.BASE and r["DS"] < 0, lambda r: base_of.get(r["BLOCK"]))
print(f"   companion (buyer-ward, intensity 2), minus baseline: {fmt(boot_mean(comp))}")
wsh = [(r, y[(c, ctx, p)]["walk"] - y[(base_of[r['BLOCK']], ctx, p)]["walk"]) for c, r in cells.items() if r["KIND"] == S.BASE and r["DS"] > 0
       for ctx in range(3) for p in range(2) if (c, ctx, p) in y and (base_of.get(r["BLOCK"]), ctx, p) in y]
print(f"   walk probability, seller pressure minus baseline: {fmt(boot_mean(wsh))}")

# 4. updating
def slope(rows, xkey):
    if len(rows) < 3:
        return None
    x = np.array([r[xkey] for r, _ in rows]); d = np.array([d for _, d in rows])
    if np.ptp(x) == 0:
        return None
    A = np.column_stack([np.ones_like(x), x]); coef, *_ = np.linalg.lstsq(A, d, rcond=None)
    bs = []
    groups = defaultdict(list)
    for (r, dd) in rows:
        groups[r["BLOCK"]].append((r[xkey], dd))
    gk = list(groups)
    for _ in range(1000):
        pts = [pt for i in rng.integers(0, len(gk), len(gk)) for pt in groups[gk[i]]]
        xx = np.array([p[0] for p in pts]); dd = np.array([p[1] for p in pts])
        if np.ptp(xx) > 0:
            bs.append(np.linalg.lstsq(np.column_stack([np.ones_like(xx), xx]), dd, rcond=None)[0][1])
    return float(coef[1]), float(np.quantile(bs, 0.025)), float(np.quantile(bs, 0.975)), len(rows)
info = diffs(lambda r: r["KIND"] == S.SCORED and r["DS"] == 0 and r["ITEM"] > 0, lambda r: base_of.get(r["BLOCK"]))
items = K.items_for(s.info, s.source, s.graded, PM)
cred = [(r, d) for r, d in info if r["CRED"] == 1]
print(f"4. updating slope w on credible items (Δexp_u on Δu*): {fmt(slope(cred, 'DU'))}")
for k, it in enumerate(items, 1):
    sub = [(r, d) for r, d in info if r["ITEM"] == k]
    if sub:
        print(f"   item {it}: mean Δexp_u {np.mean([d for _, d in sub]):+.3f}, mean Δu* {np.mean([r['DU'] for r, _ in sub]):+.3f}, credible {int(sub[0][0]['CRED'])}")
noncred = [(r, d) for r, d in info if r["CRED"] == 0 and not (r["v"] == 2 or (r["v"] == 6 and r["hist"]))]
print(f"   credulity ν (Δexp_u on Δu^naive, non-credible, defined cells): {fmt(slope(noncred, 'DUN'))}")
pinfo = diffs(lambda r: r["KIND"] == S.SCORED and r["DS"] == 2 and r["FAM"] == 0,
              lambda r: next((c for c, q in cells.items() if q["KIND"] == S.BASE and q["DS"] == 2 and q["FAM"] == 0 and q["BLOCK"] == r["BLOCK"]), None))
print(f"   updating slope under flattery (intensity 2): {fmt(slope([(r, d) for r, d in pinfo if r['CRED'] == 1], 'DU'))}")
mu = diffs(lambda r: r["KIND"] == S.CTRLINFO,
           lambda r: next((c for c, q in cells.items() if q["KIND"] == S.SCORED and q["DS"] == 0 and q["ITEM"] == r["ITEM"] and q["BLOCK"] == r["BLOCK"]), None))
print(f"   message effect μ (neutral × information minus information alone): {fmt(boot_mean(mu))}")

# 5. variance components on seller-pressure cells
P = [(c, r) for c, r in cells.items() if r["KIND"] == S.BASE and r["DS"] > 0]
full = [(c, r) for c, r in P if all((c, ctx, p) in y for ctx in range(3) for p in range(2))]
if len(full) > 10:
    Y = np.array([[[y[(c, ctx, p)]["exp_u"] for p in range(2)] for ctx in range(3)] for c, _ in full])   # cells x ctx x para
    Yc = Y - Y.mean(axis=(1, 2), keepdims=True)
    ctx_eff = Yc.mean(axis=(0, 2)); var_ctx = float(np.var(ctx_eff, ddof=1))
    pd_cell = (Y[:, :, 1] - Y[:, :, 0]).mean(axis=1) / 2          # paraphrase half-difference per cell
    lines = defaultdict(list)
    for (c, r), d in zip(full, pd_cell):
        lines[press_line(r)[:2]].append(d)
    line_means = np.array([np.mean(v) for v in lines.values()]); nb = np.mean([len(v) for v in lines.values()])
    within = np.mean([np.var(v, ddof=1) for v in lines.values() if len(v) > 1])
    var_line = max(0.0, float(np.var(line_means, ddof=1) - within / nb))      # half-difference variance = sigma_line^2 / 2
    resid = Yc - ctx_eff[None, :, None] - (np.stack([-pd_cell, pd_cell], axis=1)[:, None, :])
    var_res = float(np.var(resid, ddof=0) * Y.size / max(1, Y.size - len(full) - 2 - len(full)))
    print(f"5. variance components (exp_u, {len(full)} seller-pressure cells): context SD {np.sqrt(var_ctx):.4f} (3 levels; indicative only); "
          f"shared line-paraphrase SD {np.sqrt(2 * var_line):.4f} (declared 0.05 x intensity); cell-specific paraphrase "
          f"half-difference SD {np.sqrt(max(0.0, within / 1)):.4f}; residual SD {np.sqrt(var_res):.4f}")
else:
    print("5. variance components: not enough complete cells yet")

# 6. option distribution
sdb = [r["sd_offer"] for r in R if r["KIND"] == S.BASE and r["DS"] == 0]
sdp = [r["sd_offer"] for r in R if r["KIND"] == S.BASE and r["DS"] > 0]
print(f"6. option distribution: mean sd of the offer (coins) {np.mean([r['sd_offer'] for r in R]):.2f}; baseline {np.mean(sdb) if sdb else float('nan'):.2f}, "
      f"seller pressure {np.mean(sdp) if sdp else float('nan'):.2f}; per-answer SD in normalised units {np.mean([r['sd_offer'] for r in R]) / 8:.3f} (declared 0.08)")
