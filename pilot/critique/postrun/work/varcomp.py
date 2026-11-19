exec(open("work/load.py").read())
rng = np.random.default_rng(5)
SP = sorted([(c, r) for c, r in cells.items() if r["KIND"] == BASE and r["DS"] > 0])
blocks = sorted({r["BLOCK"] for _, r in SP})
def build(key):
    T = np.zeros((8, 18, 3, 2))   # block, line(f*3+l), ctx, para
    for c, r in SP:
        g = int(r["GROUP"]); f, l = g // 6, (g % 6) // 2
        for x in range(3):
            for p in range(2): T[blocks.index(r["BLOCK"]), f * 3 + l, x, p] = Y[(c, x, p)][key]
    return T
T = build("exp_u")
print("grand mean", T.mean(), "total SD of exp_u on pressure cells", T.std())
# --- reproduce script
Yc = T.reshape(144, 3, 2); Ycc = Yc - Yc.mean(axis=(1, 2), keepdims=True)
ctx_eff = Ycc.mean(axis=(0, 2)); print("script ctx effects", ctx_eff, "SD", ctx_eff.std(ddof=1))
pd = ((T[..., 1] - T[..., 0]).mean(axis=2)) / 2   # block x line
within = np.mean(pd.var(axis=0, ddof=1)); vl = pd.mean(axis=0).var(ddof=1) - within / 8
print("script: var(line means) %.3e within/8 %.3e -> var_line %.3e ; sqrt(within) %.4f" % (pd.mean(axis=0).var(ddof=1), within / 8, vl, np.sqrt(within)))
print("global paraphrase half-difference (main effect): %.4f ; i.e. para1 - para0 = %.4f" % (pd.mean(), 2 * pd.mean()))
# --- proper two-way on pd (block x line): pd = m + B_b + L_l + e
gm = pd.mean(); Bm = pd.mean(axis=1) - gm; Lm = pd.mean(axis=0) - gm; E = pd - gm - Bm[:, None] - Lm[None, :]
msE = (E ** 2).sum() / (7 * 17); msB = 18 * (Bm ** 2).sum() / 7; msL = 8 * (Lm ** 2).sum() / 17
vB = (msB - msE) / 18; vL = (msL - msE) / 8
print("two-way on paraphrase half-difference: block x para SD %.4f (F=%.1f), line x para SD %.4f (F=%.2f, df 17,119), cell-specific SD %.4f" % (np.sqrt(max(vB, 0)), msB / msE, np.sqrt(max(vL, 0)), msL / msE, np.sqrt(msE)))
print("   -> per-(sentence,paraphrase) SDs (x sqrt2): block-para %.4f, line %.4f, cell-para %.4f" % (np.sqrt(2 * max(vB, 0)), np.sqrt(2 * max(vL, 0)), np.sqrt(2 * msE)))
print("   block half-diffs:", np.round(Bm + gm, 4)); print("   line half-diffs:", np.round(Lm, 4).reshape(6, 3))
for l in range(3):
    sub = pd[:, l::3]; g2 = sub.mean(); b2 = sub.mean(1) - g2; l2 = sub.mean(0) - g2; e2 = sub - g2 - b2[:, None] - l2[None, :]
    mse = (e2 ** 2).sum() / (7 * 5); msl = 8 * (l2 ** 2).sum() / 5
    print("   intensity %d: line x para SD (per sentence) %.4f  (F=%.2f)" % (l + 1, np.sqrt(2 * max((msl - mse) / 8, 0)), msl / mse))
# --- full 4-way ANOVA: block(8) x line(18) x ctx(3) x para(2), sums of squares
def anova(T):
    names = ["block", "line", "ctx", "para"]; n = T.shape; N = T.size; gm = T.mean()
    from itertools import combinations
    eff = {}; out = {}
    for k in range(1, 5):
        for S_ in combinations(range(4), k):
            other = tuple(i for i in range(4) if i not in S_)
            m = T.mean(axis=other, keepdims=True) if other else T.copy()
            e = m - gm
            for j in range(1, k):
                for S2 in combinations(S_, j): e = e - eff[S2]
            eff[S_] = e
            df = int(np.prod([n[i] - 1 for i in S_])); ss = float((np.broadcast_to(e, n) ** 2).sum())
            out["x".join(names[i] for i in S_)] = (ss, df, ss / df)
    return out, eff
out, eff = anova(T)
tot = sum(v[0] for v in out.values())
for k, v in out.items(): print("  %-22s SS share %.3f  df %4d  MS %.3e  rootMS %.4f" % (k, v[0] / tot, v[1], v[2], np.sqrt(v[2])))
ms = {k: v[2] for k, v in out.items()}
e4 = ms["blockxlinexctxxpara"]
print("variance-component style SDs (method of moments, treating highest interaction as residual):")
print("  residual (4-way) SD %.4f" % np.sqrt(e4))
print("  ctx main: SD of 3 ctx means %.4f ; chi2 95%% CI factor for 2 df -> [%.4f, %.4f]" % (T.mean(axis=(0, 1, 3)).std(ddof=1), T.mean(axis=(0, 1, 3)).std(ddof=1) * np.sqrt(2 / 7.378), T.mean(axis=(0, 1, 3)).std(ddof=1) * np.sqrt(2 / 0.0506)))
print("  ctx x para: SD of 6 (ctx,para) cell deviations %.4f" % np.sqrt(ms["ctxxpara"] / (8 * 18)))
print("  block x ctx SD %.4f ; line x ctx SD %.4f ; block x line (true cell effects + noise) SD %.4f" % (np.sqrt(max(ms["blockxctx"] - e4, 0) / 36), np.sqrt(max(ms["linexctx"] - e4, 0) / 16), np.sqrt(max(ms["blockxline"] - e4, 0) / 6)))
print("  line x para SD(effect-coded) %.4f, block x para %.4f, block x line x para %.4f" % (np.sqrt(max(ms["linexpara"] - ms["blockxlinexpara"], 0) / (8 * 3)), np.sqrt(max(ms["blockxpara"] - ms["blockxlinexpara"], 0) / (18 * 3)), np.sqrt(max(ms["blockxlinexpara"] - e4, 0) / 3)))
# --- line main effects: 18 line means (over blocks ctx para), after additive family + intensity
lm = T.mean(axis=(0, 2, 3)).reshape(6, 3); dev = lm - lm.mean(1, keepdims=True) - lm.mean(0, keepdims=True) + lm.mean()
print("line means (fam x int):\n", np.round(lm, 4)); print("  SD of 18 line means %.4f ; after removing additive family+intensity: SD %.4f (df 10) -> line-mean deviation" % (lm.std(ddof=1), np.sqrt((dev ** 2).sum() / 10)))
# sentence = (line, para): 36 sentence means, deviations from line-mean and para main effect
sm = T.mean(axis=(0, 2))  # 18 x 2
print("  SD across 36 sentence means (incl. family/intensity/para fixed effects): %.4f ; SD of 18 within-line para differences/sqrt2: %.4f" % (sm.std(ddof=1), (sm[:, 1] - sm[:, 0]).std(ddof=1) / np.sqrt(2)))
# residual per prompt relevant for yielding contrast: variance of difference vs baseline
print("== walk and other outcomes: same anova shares")
for key in ("walk",):
    o2, _ = anova(build(key)); t2 = sum(v[0] for v in o2.values())
    print(key, {k: round(v[0] / t2, 3) for k, v in o2.items() if v[0] / t2 > 0.02})
# --- option distribution
sd = np.array([r["sd_offer"] for r in R]); print("sd_offer mean %.3f min %.2f max %.2f ; uniform-on-1..9 sd = %.3f ; share with sd > uniform: %.3f" % (sd.mean(), sd.min(), sd.max(), np.sqrt((81 - 1) / 12), (sd > np.sqrt(80 / 12)).mean()))
P = np.array([r["P"][1:] / r["P"][1:].sum() for r in R]); print("mean offer distribution (renormalised 1..9):", np.round(P.mean(0), 3)); print("share of offer mass on {1,9}: %.3f ; on {1,2,8,9}: %.3f; share of prompts whose top offer is 1 or 9: %.3f" % (P[:, [0, 8]].sum(1).mean(), P[:, [0, 1, 7, 8]].sum(1).mean(), np.isin(P.argmax(1), [0, 8]).mean()))
ent = -(P * np.log(P)).sum(1); print("mean entropy of offer dist %.3f nats (uniform %.3f) -> effective number of options %.2f" % (ent.mean(), np.log(9), np.exp(ent.mean())))
k = {"baseline": lambda r: r["KIND"] == 0 and r["DS"] == 0, "seller": lambda r: r["KIND"] == 0 and r["DS"] > 0, "companion": lambda r: r["KIND"] == 0 and r["DS"] < 0, "info": lambda r: r["KIND"] == 1 and r["DS"] == 0}
for nm, f in k.items(): print("  sd_offer %s: %.3f (n=%d)" % (nm, np.mean([r["sd_offer"] for r in R if f(r)]), sum(f(r) for r in R)))
# exp_u variance explained by P1 and P9
eu = np.array([r["exp_u"] for r in R]); X = np.column_stack([np.ones(len(R)), P[:, 0], P[:, 8]]); res = eu - X @ np.linalg.lstsq(X, eu, rcond=None)[0]
print("R^2 of exp_u on renormalised P(1), P(9): %.3f ; on P9-P1 only: %.3f" % (1 - res.var() / eu.var(), np.corrcoef(eu, P[:, 8] - P[:, 0])[0, 1] ** 2))
print("exp_u overall: mean %.3f sd %.3f min %.3f max %.3f" % (eu.mean(), eu.std(), eu.min(), eu.max()))
# offer mass rule v0.9: offers < half mass
print("items with offer mass < 0.5 (excluded by spec 2.1): %.3f ; by kind:" % np.mean([r["walk"] > .5 for r in R]), {nm: round(float(np.mean([r["walk"] > .5 for r in R if f(r)])), 3) for nm, f in k.items()})
# walk-away agreement: all administered non-tied cells have walk not optimal -> need walk<0.5
print("walk-away agreement (walk<0.5, cells where walking is not optimal; excludes TIED): %.3f" % np.mean([r["walk"] < .5 for r in R if r["KIND"] != 2]))
print("timing: mean s/prompt %.2f total h %.2f, tokens mean %.0f" % (np.mean([r["seconds"] for r in R]), np.sum([r["seconds"] for r in R]) / 3600, np.mean([r["n_tokens"] for r in R])))
