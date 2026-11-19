"""Confirmation run (D20, from v0.7): re-run every rung-3 gate with fresh seeds on the cheapest designs that
passed rung 3, in order of N*. The selected design is the cheapest one that passes both rung 3 and this
rerun. Selecting the cheapest of 18 noisy passes favours designs that were lucky once; an independent
rerun removes that selection effect for the chosen design. Rule fixed before this script was run."""
import json, os, sys
import numpy as np
import stats_layer as S

K_FIRST = int(os.environ.get("K", 4))


def w_confirm(i, P, Cc, N, r, rp):
    D = S.Design(*S.unpack(i)); rng = S.seeded("confirm", i)
    rv = np.array([r[n] for n in D.names]); rpv = np.array([rp[n] for n in D.names])
    return S._json({**S.v2_v3(D, P, Cc, 100, rng, rv), **S.size_gate(D, P, Cc, 500, rng, rpv),
                    **S.v4(D, P, Cc, 100, rng, rv), "N": N, "P": P, "C": Cc})


if __name__ == "__main__":
    r2l = [json.loads(l) for l in open(f"{S.OUT}/rung2.jsonl")]
    r2 = {r["id"]: r for r in r2l}
    r3 = {json.loads(l)["id"]: json.loads(l) for l in open(f"{S.OUT}/rung3.jsonl")}
    order = [i for i in S.robust_order(r2l)[:50]
             if i in r3 and r3[i]["V2"] and r3[i]["V3"] and r3[i]["V4"] and r3[i]["SIZE"]]   # rung-3 ranking
    todo = order[:K_FIRST]
    args = S.rung3_args(r2, todo)
    W = int(os.environ.get("WORKERS", os.cpu_count() or 1))
    out = S.checkpointed(f"{S.OUT}/confirm.jsonl", todo, w_confirm, args, W)
    res = {r["id"]: r for r in out}
    for i in todo:
        r = res[i]; ok = r["V2"] and r["V3"] and r["V4"] and r["SIZE"]
        print(f"N*={r['N']:,} confirm {'PASS' if ok else 'fail'} V2={r['V2']} V3={r['V3']} V4={r['V4']} "
              f"SIZE={r['SIZE']} size_max={r['size_max']:.3f} grid={r['bias_lamS_grid']:.3f}  {i}")
    sel = next((i for i in todo if res[i]["V2"] and res[i]["V3"] and res[i]["V4"] and res[i]["SIZE"]), None)
    print("selected:", sel)
