exec(open("work/load.py").read())
import kernel as K, stats_layer as S
from pilot import run_pilot as RP
print(len(R), len(Y), len(cells), Counter(Counter(r["cell"] for r in R).values()))
# regenerate prompts and compare annotations and order
pr = RP.build()
print("prompts regenerated", len(pr))
bad = 0
for a, b in zip(pr, R):
    for k in ("cell","ctx","para","v","hist","U0","DU","DS","FAM","CRED","BLOCK","ITEM","GROUP","KIND","DUN"):
        if a[k] != b[k]: bad += 1
print("annotation mismatches", bad)
# recompute stored summaries from probs
mx = 0
for r in R:
    d = r["P"]; cov = d.sum(); q = d/cov; off = q[1:]/q[1:].sum(); eo = (np.arange(1,10)*off).sum()
    mx = max(mx, abs(cov-r["coverage"]), abs(q[0]-r["walk"]), abs(eo-r["exp_offer"]), abs((eo-1)/8-r["exp_u"]), abs(np.sqrt(((np.arange(1,10)-eo)**2*off).sum())-r["sd_offer"]), abs(int(np.argmax(q))-r["argmax"]))
print("max summary discrepancy", mx)
print("kinds", Counter((r["KIND"], np.sign(r["DS"])) for r in cells.values()))
# independent kernel check of U0 and DU
s, lv, dr = S.unpack(RP.DESIGN)
mu = K.prior(s.types, s.shape); print(mu, s)
items = K.items_for(s.info, s.source, s.graded, s.pmax)
for v in K.ladder(5, 9):
    for h in (False, True):
        b = K.belief(mu, 9, h)
        U = {a: float((v-a)*sum(p for k,p in b.items() if K.accepts(k,a,9))) for a in range(1,10)}
        A0 = K.optimal(b, v, 9, True)
        print(v, h, sorted(A0), {a: round(u,3) for a,u in U.items()})
blocks = sorted({(r["BLOCK"], r["v"], r["hist"], r["U0"]) for r in cells.values()}); print(blocks)
for c, r in sorted(cells.items()):
    if r["DS"] == 0 and r["ITEM"] > 0 and r["KIND"] in (1,2):
        print(c, r["v"], int(r["hist"]), items[int(r["ITEM"])-1], "kind", r["KIND"], "cred", r["CRED"], "U0", r["U0"], "DU", round(r["DU"],3), "DUN", round(r["DUN"],3), "VBAR", r["VBAR"], "INT", r["INT"])
# show two prompts
for i in (0, 1):
    print(pr[i]["messages"][0]["content"]); print(pr[i]["messages"][1]["content"]); print("====")
