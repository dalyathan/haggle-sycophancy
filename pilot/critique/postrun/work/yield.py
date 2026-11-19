exec(open("work/load.py").read())
rng = np.random.default_rng(777)
PN = 36
base = {r["BLOCK"]: c for c, r in cells.items() if r["KIND"] == BASE and r["DS"] == 0 and r["ITEM"] == 0}
neut = {(r["BLOCK"], int(r["GROUP"] - PN - 1)): c for c, r in cells.items() if r["KIND"] == CTRL and PN + 2 <= r["GROUP"] < PN + 5}
irr = {(r["BLOCK"], int(r["GROUP"] - PN)): c for c, r in cells.items() if r["KIND"] == CTRL and r["GROUP"] in (PN, PN + 1)}
blocks = sorted(base)
def line(r):
    g = int(r["GROUP"]); return g // 6, (g % 6) // 2 + 1, (1, -1)[g % 2]
for c, r in cells.items():
    if r["KIND"] == BASE and r["DS"] != 0:
        f, l, d = line(r); assert f == r["FAM"] and l * d == r["DS"], (f, l, d, r["FAM"], r["DS"])
SP = [(c, r) for c, r in cells.items() if r["KIND"] == BASE and r["DS"] > 0]
print("seller pressure cells", len(SP))
def arr(key, refmap):
    # D[block, fam, int, ctx, para]
    D = np.full((8, 6, 3, 3, 2), np.nan)
    for c, r in SP:
        f, l, d = line(r); b = blocks.index(r["BLOCK"])
        rc = refmap(r)
        for x in range(3):
            for p in range(2):
                D[b, f, l - 1, x, p] = Y[(c, x, p)][key] - (Y[(rc, x, p)][key] if rc is not None else 0)
    return D
def ci_block(D, B=5000):
    m = np.nanmean(D); bm = D.reshape(8, -1).mean(1)
    bs = [bm[rng.integers(0, 8, 8)].mean() for _ in range(B)]
    return m, np.quantile(bs, .025), np.quantile(bs, .975)
def tci(x):
    x = np.asarray(x); n = len(x); m = x.mean(); se = x.std(ddof=1) / np.sqrt(n)
    from math import sqrt
    tq = {2: 4.303, 5: 2.571, 7: 2.365, 17: 2.110, 35: 2.030, 2:4.303}.get(n - 1, 2.0)
    return m, m - tq * se, m + tq * se, se
names = ["flattery", "sympathy", "displeasure", "urgency", "rapport", "insistence"]
for key in ("exp_u", "walk"):
    print("=====", key)
    Db = arr(key, lambda r: base[r["BLOCK"]]); Dn = arr(key, lambda r: neut[(r["BLOCK"], int(r["DS"]))]); Raw = arr(key, lambda r: None)
    for nm, D in (("vs baseline", Db), ("vs neutral", Dn)):
        print(nm, "pooled mean %+.4f block-bootstrap [%+.4f, %+.4f]" % ci_block(D))
        print("   t-interval over 8 block means: %+.4f [%+.4f, %+.4f] se %.4f" % tci(D.reshape(8, -1).mean(1)))
        lm = D.mean(axis=(0, 3)).reshape(-1)   # 36 line x para means
        print("   t-interval over 36 sentence(line x para) means: %+.4f [%+.4f, %+.4f] se %.4f" % tci(lm))
        print("   t-interval over 18 lines: %+.4f [%+.4f, %+.4f] se %.4f" % tci(D.mean(axis=(0, 3, 4)).reshape(-1)))
        print("   over 3 contexts: %+.4f [%+.4f, %+.4f] se %.4f" % tci(D.mean(axis=(0, 1, 2, 4))), " by para:", np.round(D.mean(axis=(0, 1, 2, 3)), 4))
        print("   by intensity:", np.round(D.mean(axis=(0, 1, 3, 4)), 4), " by family:", np.round(D.mean(axis=(0, 2, 3, 4)), 4))
        print("   by block:", np.round(D.mean(axis=(1, 2, 3, 4)), 4))
        if nm == "vs baseline":
            for f in range(6):
                print("   %-12s" % names[f], "  ".join("s%d %+.4f [%+.4f,%+.4f]" % ((l + 1,) + ci_block(D[:, f:f+1, l:l+1])) for l in range(3)))
            print("   sentence-level (fam,int,para) means:\n", np.round(D.mean(axis=(0, 3)), 3).reshape(6, 6))
    # controls vs baseline
    def ctl(cmap, k):
        d = np.array([[[Y[(cmap[(b, k)], x, p)][key] - Y[(base[b], x, p)][key] for p in range(2)] for x in range(3)] for b in blocks]); return d
    for k in (1, 2, 3):
        d = ctl(neut, k); print("  neutral s%d minus baseline: %+.4f  by para %s  block-t [%+.4f,%+.4f]" % (k, d.mean(), np.round(d.mean(axis=(0, 1)), 4), *tci(d.mean(axis=(1, 2)))[1:3]))
    for k in (0, 1):
        d = ctl(irr, k); print("  irrelevant %d minus baseline: %+.4f  by para %s block-t [%+.4f,%+.4f]" % (k, d.mean(), np.round(d.mean(axis=(0, 1)), 4), *tci(d.mean(axis=(1, 2)))[1:3]))
    # all 10 control sentence(x para) means vs baseline
    cs = [ctl(neut, k).mean(axis=(0, 1)) for k in (1, 2, 3)] + [ctl(irr, k).mean(axis=(0, 1)) for k in (0, 1)]
    cs = np.concatenate(cs); print("  10 control sentence means vs baseline: mean %+.4f sd %.4f  -> seller minus all-controls: %+.4f" % (cs.mean(), cs.std(ddof=1), Db.mean() - cs.mean()))
    lm = Db.mean(axis=(0, 3)).reshape(-1); se = np.sqrt(lm.var(ddof=1) / 36 + cs.var(ddof=1) / 10)
    print("  seller(36 sentences) vs controls(10 sentences) Welch: diff %+.4f se %.4f  -> 95%% approx [%+.4f, %+.4f]" % (lm.mean() - cs.mean(), se, lm.mean() - cs.mean() - 2.1 * se, lm.mean() - cs.mean() + 2.1 * se))
    # companion
    CP = [(c, r) for c, r in cells.items() if r["KIND"] == BASE and r["DS"] < 0]
    d = np.array([[Y[(c, x, p)][key] - Y[(base[r["BLOCK"]], x, p)][key] for x in range(3) for p in range(2)] for c, r in CP])
    bl = defaultdict(list)
    for (c, r), dd in zip(CP, d): bl[r["BLOCK"]].append(dd.mean())
    print("  companion n=%d mean %+.4f block-t [%+.4f,%+.4f]; by family %s" % (d.size, d.mean(), *tci([np.mean(v) for v in bl.values()])[1:3], {int(f): round(float(np.mean([dd.mean() for (c, r), dd in zip(CP, d) if r["FAM"] == f])), 4) for f in (0, 2, 5)}))
# other probability shifts: P(9), P(1), P(0) raw (not renormalised)
print("===== per-digit mean shift, seller pressure minus baseline (prob over 10 digits)")
d = np.mean([Y[(c, x, p)]["P"] - Y[(base[r["BLOCK"]], x, p)]["P"] for c, r in SP for x in range(3) for p in range(2)], axis=0); print(np.round(d, 4))
print("neutral minus baseline:"); d = np.mean([Y[(c, x, p)]["P"] - Y[(base[b], x, p)]["P"] for (b, k), c in neut.items() for x in range(3) for p in range(2)], axis=0); print(np.round(d, 4))
print("irrelevant minus baseline:"); d = np.mean([Y[(c, x, p)]["P"] - Y[(base[b], x, p)]["P"] for (b, k), c in irr.items() for x in range(3) for p in range(2)], axis=0); print(np.round(d, 4))
CP = [(c, r) for c, r in cells.items() if r["KIND"] == BASE and r["DS"] < 0]
print("companion minus baseline:"); d = np.mean([Y[(c, x, p)]["P"] - Y[(base[r["BLOCK"]], x, p)]["P"] for c, r in CP for x in range(3) for p in range(2)], axis=0); print(np.round(d, 4))
# unconditional expected offer treating walk as 0? and shift in total mean
