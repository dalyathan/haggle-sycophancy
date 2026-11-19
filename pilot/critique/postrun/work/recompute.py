exec(open("work/load.py").read())
import kernel as K
from fractions import Fraction as Fr
rng = np.random.default_rng(12345)
A = np.arange(1, 10)
def g(c, ctx, p, k="exp_u"): return Y[(c, ctx, p)][k]
print("== 1 usability")
cov = np.array([r["coverage"] for r in R]); walk = np.array([r["walk"] for r in R])
print("coverage median %.4f min %.4f share<0.9 %.3f" % (np.median(cov), cov.min(), (cov < .9).mean()))
print("walk mean %.3f median %.3f share>0.5 %.3f ; argmax offer %.3f" % (walk.mean(), np.median(walk), (walk > .5).mean(), np.mean([r["argmax"] > 0 for r in R])))
pm = [r["p_digit_after_1"] for r in R if r["p_digit_after_1"] is not None]
print("p_digit_after_1: n=%d mean %.4f median %.4f max %.4f" % (len(pm), np.mean(pm), np.median(pm), max(pm)))
print("  eligible P(1)>0.1:", sum(r["P"][1] > .1 for r in R), "of", len(R))
for v in (2, 6, 10, 14, 18):
    rs = [r for r in R if r["v"] == v]
    pp = [r["p_digit_after_1"] for r in rs if r["p_digit_after_1"] is not None]
    print("  v=%2d meanP(1)=%.3f share P(1)>0.1 %.2f  sample n=%d mean p_multi %.4f max %.4f" % (v, np.mean([r["P"][1] for r in rs]), np.mean([r["P"][1] > .1 for r in rs]), len(pp), np.mean(pp) if pp else float('nan'), max(pp) if pp else float('nan')))
by_para = [np.mean([r["walk"] for r in R if r["para"] == p]) for p in (0, 1)]
print("walk by para", by_para, "by ctx", [np.mean([r["walk"] for r in R if r["ctx"] == c]) for c in range(3)])
print("mean prob vector all prompts:", np.round(np.mean([r["P"] for r in R], axis=0), 3))

print("== 2 competence")
base = {r["BLOCK"]: c for c, r in cells.items() if r["KIND"] == BASE and r["DS"] == 0 and r["ITEM"] == 0}
mu = K.prior(("rational", "gullible", "floor_low"), "rational_heavy")
def rank(x):
    x = np.asarray(x, float); o = np.argsort(x); rk = np.empty(len(x)); rk[o] = np.arange(len(x))
    for val in np.unique(x): rk[x == val] = rk[x == val].mean()
    return rk
def sp(a, b): return np.corrcoef(rank(a), rank(b))[0, 1]
rows = []
for b, c in sorted(base.items()):
    r0 = cells[c]; v, h = r0["v"], r0["hist"]
    bel = K.belief(mu, 9, h)
    U = np.array([float((Fr(v) - a) * sum(p for k, p in bel.items() if K.accepts(k, a, 9))) for a in A])
    rs = [Y[(c, x, p)] for x in range(3) for p in range(2)]
    Pm = np.mean([r["P"] / r["P"].sum() for r in rs], axis=0)
    pay = np.mean([(r["P"][1:] / r["P"].sum() * U).sum() for r in rs])
    vo = min(9, max(1, round(v / 2)))
    ir = np.mean([(r["P"][1:] / r["P"].sum())[A > v].sum() for r in rs])
    mode = [int(np.argmax(r["P"][1:])) + 1 for r in rs]
    rows.append(dict(v=v, h=h, u0=r0["U0"], eu=np.mean([r["exp_u"] for r in rs]), eo=np.mean([r["exp_offer"] for r in rs]), walk=np.mean([r["walk"] for r in rs]),
                     reg=U.max() - pay, regvo=U.max() - U[vo - 1], vou=(vo - 1) / 8, Pm=Pm, ir=ir, mode=mode, unif=U.max() - U.mean(), mid=U.max()-U[4],
                     eu_each=[r["exp_u"] for r in rs], sd=np.mean([r["sd_offer"] for r in rs])))
for x in rows:
    print("v=%2d h=%d u0=%.3f a*=%d exp_u=%.3f offer=%.2f walk=%.2f regret=%.2f (value-only %.2f, uniform-over-offers %.2f, const5 %.2f) IR=%.2f sd=%.2f modes=%s" % (x["v"], x["h"], x["u0"], round(x["u0"]*8+1), x["eu"], x["eo"], x["walk"], x["reg"], x["regvo"], x["unif"], x["mid"], x["ir"], x["sd"], x["mode"]))
    print("      mean dist 0..9:", np.round(x["Pm"], 2))
u0 = [x["u0"] for x in rows]; eu = [x["eu"] for x in rows]; vou = [x["vou"] for x in rows]
print("Spearman tie-aware: model %.3f, value-only %.3f ; (script's argsort version: model %.3f value-only %.3f)" % (sp(eu, u0), sp(vou, u0),
      np.corrcoef(np.argsort(np.argsort(eu)), np.argsort(np.argsort(u0)))[0,1], np.corrcoef(np.argsort(np.argsort(vou)), np.argsort(np.argsort(u0)))[0,1]))
print("Pearson model %.3f ; slope of exp_u on u0 (alpha1) %.3f intercept %.3f" % (np.corrcoef(eu, u0)[0,1], *np.polyfit(u0, eu, 1)))
print("MAE model %.3f value-only %.3f const-0.5 %.3f ; regret model %.3f value-only %.3f uniform %.3f const5 %.3f" % (np.mean(np.abs(np.array(eu)-u0)), np.mean(np.abs(np.array(vou)-u0)), np.mean(np.abs(0.5-np.array(u0))),
      np.mean([x["reg"] for x in rows]), np.mean([x["regvo"] for x in rows]), np.mean([x["unif"] for x in rows]), np.mean([x["mid"] for x in rows])))
# per-prompt spearman (each ctx/para separately)
sps = [sp([x["eu_each"][i] for x in rows], u0) for i in range(6)]
print("Spearman per (ctx,para) replicate:", np.round(sps, 2))
# bootstrap over blocks is meaningless w/ 8; permutation p for spearman
obs = sp(eu, u0); perm = [sp(rng.permutation(eu), u0) for _ in range(20000)]
print("perm p (one-sided) for model Spearman %.3f: %.4f" % (obs, np.mean(np.array(perm) >= obs)))
# value vs history: regress exp_offer on v and hist
X = np.column_stack([np.ones(8), [x["v"] for x in rows], [x["h"] for x in rows]]); co = np.linalg.lstsq(X, [x["eo"] for x in rows], rcond=None)[0]
print("exp_offer ~ %.2f + %.3f*v + %.2f*hist" % tuple(co))
# IR overall
ir_all = np.mean([(r["P"][1:] / r["P"].sum())[A > r["VBAR"]].sum() for r in R]); print("possible-loss mass (offers > vbar) all prompts: %.3f ; in cells with vbar<9: %.3f" % (ir_all, np.mean([(r["P"][1:] / r["P"].sum())[A > r["VBAR"]].sum() for r in R if r["VBAR"] < 9])))
