exec(open("work/load.py").read())
import kernel as K
rng = np.random.default_rng(99)
items = K.items_for(("quality_down", "cost_reveal"), "both", False, 9)
base = {r["BLOCK"]: c for c, r in cells.items() if r["KIND"] == BASE and r["DS"] == 0 and r["ITEM"] == 0}
def find(pred): return {(r["BLOCK"], int(r["ITEM"])): c for c, r in cells.items() if pred(r)}
info = find(lambda r: r["KIND"] == SCORED and r["DS"] == 0 and r["ITEM"] > 0)
tied = find(lambda r: r["KIND"] == TIED and r["DS"] == 0)
flat = find(lambda r: r["KIND"] == SCORED and r["DS"] == 2 and r["FAM"] == 0)
ctli = find(lambda r: r["KIND"] == CTRLINFO)
flatbase = {r["BLOCK"]: c for c, r in cells.items() if r["KIND"] == BASE and r["DS"] == 2 and r["FAM"] == 0}
print(len(info), len(tied), len(flat), len(ctli))
def d(c, rc, key="exp_u"): return np.array([[Y[(c, x, p)][key] - Y[(rc, x, p)][key] for p in range(2)] for x in range(3)])
def fit(rows, xk, intercept=True, B=4000):
    # rows: list of (r, dmean_over_6, block)
    x = np.array([r[xk] for r, _ in rows]); y = np.array([dd for _, dd in rows]); bl = np.array([r["BLOCK"] for r, _ in rows])
    def sl(x, y):
        if intercept:
            return np.polyfit(x, y, 1)[0]
        return (x * y).sum() / (x * x).sum()
    ub = np.unique(bl); bs = []
    for _ in range(B):
        idx = np.concatenate([np.flatnonzero(bl == b) for b in rng.choice(ub, len(ub))])
        if np.ptp(x[idx]) > 0: bs.append(sl(x[idx], y[idx]))
    return sl(x, y), np.quantile(bs, .025), np.quantile(bs, .975), len(rows)
allrows = [(cells[c], dd) for (b, k), c in info.items() for dd in d(c, base[b]).reshape(-1)]
cred = [(r, dd) for r, dd in allrows if r["CRED"] == 1]
print("w credible, with intercept: %+.4f [%+.4f,%+.4f] n=%d" % fit(cred, "DU"))
print("w credible, through origin: %+.4f [%+.4f,%+.4f] n=%d" % fit(cred, "DU", False))
x = np.array([r["DU"] for r, _ in cred]); y = np.array([dd for _, dd in cred]); print("   intercept %.4f; ratio of means %.3f; fidelity mean(d/DU | DU!=0) %.3f; n DU==0: %d" % (np.polyfit(x, y, 1)[1], y.mean() / x.mean(), np.mean(y[x != 0] / x[x != 0]), (x == 0).sum()))
for nm, sel in (("interior slope cells only (INT=1)", lambda r: r["INT"] == 1), ("seller credible", lambda r: r["SRC"] == 1), ("inspector", lambda r: r["SRC"] == 0),
                ("quality_down", lambda r: items[int(r["ITEM"]) - 1][0] == "quality_down"), ("cost low", lambda r: items[int(r["ITEM"]) - 1][:2] == ("cost_reveal", "low")),
                ("cost high insp", lambda r: items[int(r["ITEM"]) - 1][:2] == ("cost_reveal", "high")), ("DU<0", lambda r: r["DU"] < 0), ("DU>0", lambda r: r["DU"] > 0)):
    sub = [(r, dd) for r, dd in cred if sel(r)]
    xx = np.array([r["DU"] for r, _ in sub]); yy = np.array([dd for _, dd in sub])
    f1 = fit(sub, "DU") if np.ptp(xx) > 0 else (float('nan'),) * 3 + (len(sub),)
    print("  %-34s n=%3d slope(int) %+.3f [%+.3f,%+.3f]  origin %+.3f  mean d %+.3f mean DU %+.3f" % (nm, len(sub), f1[0], f1[1], f1[2], fit(sub, "DU", False)[0], yy.mean(), xx.mean()))
print("per item x block (mean over 6): d exp_u | DU | d walk | exp_offer before->after | P1,P9 before->after")
for (b, k), c in sorted(info.items(), key=lambda t: (t[0][1], t[0][0])):
    r = cells[c]; rb = base[b]
    pa = np.mean([Y[(c, x, p)]["P"] for x in range(3) for p in range(2)], 0); pb = np.mean([Y[(rb, x, p)]["P"] for x in range(3) for p in range(2)], 0)
    print("  %-34s v=%2d h=%d cred=%d  d=%+.3f DU=%+.3f DUN=%+.3f dwalk=%+.3f  P0 %.2f->%.2f P1 %.2f->%.2f P9 %.2f->%.2f  mode offer %d->%d (target %d)" % (items[k - 1], r["v"], r["hist"], r["CRED"], d(c, rb).mean(), r["DU"], r["DUN"], d(c, rb, "walk").mean(), pb[0], pa[0], pb[1], pa[1], pb[9], pa[9], np.argmax(pb[1:]) + 1, np.argmax(pa[1:]) + 1, round((r["U0"] + r["DU"]) * 8 + 1)))
for (b, k), c in tied.items():
    r = cells[c]; print("  TIED", items[k - 1], r["v"], r["hist"], "d=%+.3f dwalk=%+.3f" % (d(c, base[b]).mean(), d(c, base[b], "walk").mean()))
# credulity
nc = [(r, dd) for r, dd in allrows if r["CRED"] == 0]
ncd = [(r, dd) for r, dd in nc if not (r["v"] == 2 or (r["v"] == 6 and r["hist"]))]
print("credulity nu with intercept: %+.4f [%+.4f,%+.4f] n=%d" % fit(ncd, "DUN")); print("credulity nu through origin: %+.4f [%+.4f,%+.4f] n=%d" % fit(ncd, "DUN", False))
print("  mean shift on non-credible claim, all 8 blocks: %+.4f ; defined blocks %+.4f; v=2,6 blocks %+.4f" % (np.mean([dd for _, dd in nc]), np.mean([dd for _, dd in ncd]), np.mean([dd for r, dd in nc if (r["v"] == 2 or (r["v"] == 6 and r["hist"]))])))
# seller vs inspector high-cost in same blocks
pairs = []
for b in base:
    if (b, 5) in info and (b, 6) in info:
        pairs.append((cells[info[(b, 5)]]["v"], cells[info[(b, 5)]]["hist"], d(info[(b, 5)], base[b]).mean(), d(info[(b, 6)], base[b]).mean(), cells[info[(b, 6)]]["DU"]))
print("  high-cost claim: (v,h, shift seller[non-credible], shift inspector[credible], DU inspector)"); [print("   ", p) for p in pairs]
ps = np.array([p[2] for p in pairs]); pi = np.array([p[3] for p in pairs]); print("  mean seller %+.4f inspector %+.4f ratio %.2f ; diff insp-seller %+.4f se %.4f" % (ps.mean(), pi.mean(), ps.mean() / pi.mean(), (pi - ps).mean(), (pi - ps).std(ddof=1) / np.sqrt(len(ps))))
# seller vs inspector for credible items (quality down, cost low)
for ks, ki, nm in ((1, 2, "quality_down"), (3, 4, "cost low")):
    dd = [(d(info[(b, ks)], base[b]).mean(), d(info[(b, ki)], base[b]).mean()) for b in base if (b, ks) in info and (b, ki) in info]
    dd = np.array(dd); print("  %s: seller %+.4f inspector %+.4f (n blocks %d)" % (nm, dd[:, 0].mean(), dd[:, 1].mean(), len(dd)))
# blunting
frows = [(cells[c], dd) for (b, k), c in flat.items() for dd in d(c, flatbase[b]).reshape(-1) if cells[c]["CRED"] == 1]
print("slope under flattery2: %+.4f [%+.4f,%+.4f] n=%d" % fit(frows, "DU"))
# paired kappa: difference of slopes via paired bootstrap over blocks
def slopes_boot(B=4000):
    keys = [(b, k) for (b, k) in info if cells[info[(b, k)]]["CRED"] == 1 and (b, k) in flat]
    X = np.array([cells[info[k]]["DU"] for k in keys]); y0 = np.array([d(info[k], base[k[0]]).mean() for k in keys]); y1 = np.array([d(flat[k], flatbase[k[0]]).mean() for k in keys]); bl = np.array([k[0] for k in keys])
    s = lambda x, y: np.polyfit(x, y, 1)[0]; obs = s(X, y1) - s(X, y0); ub = np.unique(bl); bs = []
    for _ in range(B):
        idx = np.concatenate([np.flatnonzero(bl == b) for b in rng.choice(ub, len(ub))])
        if np.ptp(X[idx]) > 0: bs.append(s(X[idx], y1[idx]) - s(X[idx], y0[idx]))
    return obs, np.quantile(bs, .025), np.quantile(bs, .975), len(keys)
print("kappa (flattery2 slope minus plain slope, paired): %+.4f [%+.4f,%+.4f] cells=%d" % slopes_boot())
print("non-credible under flattery:", np.mean([d(c, flatbase[b]).mean() for (b, k), c in flat.items() if cells[c]["CRED"] == 0]), "vs plain", np.mean([d(info[(b, k)], base[b]).mean() for (b, k), c in flat.items() if cells[c]["CRED"] == 0]))
# mu
m = np.array([d(c, info[(b, k)]).mean() for (b, k), c in ctli.items()]); bl = np.array([b for (b, k) in ctli])
bm = np.array([m[bl == b].mean() for b in np.unique(bl)])
print("mu: mean %+.4f n cells %d ; block-t se %.4f [%+.4f, %+.4f]; neutral s1 alone vs baseline was -0.0002" % (m.mean(), len(m), bm.std(ddof=1) / np.sqrt(8), m.mean() - 2.365 * bm.std(ddof=1) / np.sqrt(8), m.mean() + 2.365 * bm.std(ddof=1) / np.sqrt(8)))
mw = np.array([d(c, info[(b, k)], "walk").mean() for (b, k), c in ctli.items()]); print("   walk: %+.4f" % mw.mean())
# opposed cell agreement: seller pressure(flattery 2) + credible info with DU<0: share where exp_u moves down by >=0.05 relative to pressure-only cell
opp = [(d(c, flatbase[b]) <= -0.05).mean() for (b, k), c in flat.items() if cells[c]["CRED"] == 1 and cells[c]["DU"] < 0]
print("opposed-cell agreement (share prompts with shift <= -0.05): %.3f over %d cells" % (np.mean(opp), len(opp)))
