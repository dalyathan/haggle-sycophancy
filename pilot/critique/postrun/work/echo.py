exec(open("work/load.py").read())
bl = [r for r in R if r["KIND"] in (0, 4) and r["DS"] >= 0 and r["ITEM"] == 0]   # no-info cells: baseline, seller pressure, controls
print("no-info prompts:", len(bl))
print("mean P(d) by (v,hist) over no-info cells; digits 0..9")
for v, h in sorted({(r["v"], r["hist"]) for r in bl}):
    print(v, int(h), np.round(np.mean([r["P"] for r in bl if r["v"] == v and r["hist"] == h], 0), 3))
for dgt, vv in ((2, 2), (6, 6)):
    a = np.mean([r["P"][dgt] for r in bl if r["v"] == vv]); b = np.mean([r["P"][dgt] for r in bl if r["v"] != vv])
    print("P(%d) when v=%d: %.3f ; other values: %.3f" % (dgt, vv, a, b))
print("P(4) [floor digit] mean %.3f, P(8) [top cost] %.3f vs P(3) %.3f P(5) %.3f P(6|v!=6) %.3f P(7) %.3f" % (tuple(np.mean([r["P"][d] for r in bl]) for d in (4, 8, 3, 5)) + (np.mean([r["P"][6] for r in bl if r["v"] != 6]), np.mean([r["P"][7] for r in bl]))))
# share of mass on digits named in prompt for each no-info prompt: {0,1,9} instruction, 8, 4, v digits
def named(r):
    s = {0, 1, 9, 8, 4} | {int(ch) for ch in str(r["v"])}; return s
print("mean mass on digits literally present in the prompt (0,1,9,8,4,value digits): %.3f ; on the instruction's 0/1/9 only: %.3f" % (np.mean([sum(r["P"][d] for d in named(r)) for r in bl]), np.mean([r["P"][[0, 1, 9]].sum() for r in bl])))
# mass on the optimal offer vs mass on other offers, baseline
base = [r for r in R if r["KIND"] == 0 and r["DS"] == 0]
print("baseline: mean P(optimal offer) %.3f ; chance among 10 = 0.1 ; rank of optimal among offers (1=top): %s" % (np.mean([r["P"][round(r["U0"] * 8 + 1)] for r in base]), Counter(int((r["P"][1:] > r["P"][round(r["U0"] * 8 + 1)]).sum()) + 1 for r in base)))
allp = [r for r in R if r["KIND"] in (0, 1, 4, 5)]
tgt = lambda r: round((r["U0"] + r["DU"]) * 8 + 1)
print("all scored/base/control prompts (n=%d): mean P(target offer) %.3f ; argmax-of-offers == target: %.3f ; argmax overall == target %.3f" % (len(allp), np.mean([r["P"][tgt(r)] for r in allp]), np.mean([np.argmax(r["P"][1:]) + 1 == tgt(r) for r in allp]), np.mean([r["argmax"] == tgt(r) for r in allp])))
ex = [r for r in allp if tgt(r) not in (1, 9)]
print("  excluding targets 1 and 9 (n=%d): P(target) %.3f ; argmax-of-offers == target %.3f" % (len(ex), np.mean([r["P"][tgt(r)] for r in ex]), np.mean([np.argmax(r["P"][1:]) + 1 == tgt(r) for r in ex])))
# top10 non-digit tokens
nd = Counter(t for r in R for t, p in r["top10"] if t.strip() not in list("0123456789")); print("non-digit tokens in top10:", nd.most_common(8))
print("tokens with leading/trailing space among top10 digits:", Counter(t for r in R for t, p in r["top10"] if t != t.strip()).most_common(5))
