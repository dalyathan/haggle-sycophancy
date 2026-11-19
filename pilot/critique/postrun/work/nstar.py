exec(open("work/load.py").read())
import stats_layer as S, time
from pilot import run_pilot as RP
D = S.Design(*S.unpack(RP.DESIGN))
for nm, comp in (("declared", S.COMP), ("measured (script values, line 0.008)", dict(sig_e=0.0225, sig_ctx=0.0148, sig_par=0.027, sig_line=0.008, rho=0.6)),
                 ("measured, ctx at upper CI 0.093", dict(sig_e=0.0225, sig_ctx=0.093, sig_par=0.027, sig_line=0.008, rho=0.6)),
                 ("measured, rho=0", dict(sig_e=0.0225, sig_ctx=0.0148, sig_par=0.027, sig_line=0.008, rho=0.0))):
    t = time.time(); res = S.cheapest(D, comp); print(nm, {k: (v if not isinstance(v, dict) else {a: round(float(b), 4) for a, b in v.items()}) for k, v in res.items()} if isinstance(res, dict) else res, "%.1fs" % (time.time() - t))
    try:
        se = S.closed_form(D, 2, 6, comp); print("   at (2,6):", se if not hasattr(se, "items") else {k: round(float(v), 4) for k, v in se.items()})
    except Exception as e: print("   err", e)
# attrition by item
import kernel as K
items = K.items_for(("quality_down", "cost_reveal"), "both", False, 9)
for k in range(1, 7):
    rs = [r for r in R if r["KIND"] == 1 and r["DS"] == 0 and r["ITEM"] == k]
    print(items[k - 1], "share walk>0.5: %.2f mean walk %.2f n=%d" % (np.mean([r["walk"] > .5 for r in rs]), np.mean([r["walk"] for r in rs]), len(rs)))
