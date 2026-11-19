import os, sys
for v in ("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS"): os.environ[v]="1"
sys.path.insert(0,".")
import numpy as np, stats_layer as S, guards as G
for i, r2 in G.top_designs(10)[:1] + [d for d in G.top_designs(10) if d[1]["best"]["N"]==138240]:
    D = S.Design(*S.unpack(i)); P, Cc = r2["best"]["P"], r2["best"]["C"]
    rng = S.seeded("review", i)
    cal = G.Calib(D, P, Cc, r2, rng, B=200); c12 = G.Calib12(D, P, Cc, rng, B=400)
    print("N", r2["best"]["N"], "P,C", P, Cc, "cells", len(D.Call), "L", D.L)
    print(" paired SE per family/intensity:", dict(zip(cal.fa_names, np.round(cal.se_fa,4))))
    print(" single-arm thresholds M1,M2,M3 (99.5%):", np.round(c12.q_m,4), " sd raw_r single:", round(cal.sd_r1,4), " paired se raw_r:", round(cal.se_r,4), "se dM2", round(c12.se_dm2,4))
    C=D.Call; sw=(C[:,S.DS]>0)
    print(" seller-pressure cells", int(sw.sum()), "tied", int((C[:,S.KIND]==S.TIED).sum()), "kinds", {int(k):int((C[:,S.KIND]==k).sum()) for k in np.unique(C[:,S.KIND])})
