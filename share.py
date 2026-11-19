"""Run one share of a rung on its own machine (v0.9). Every design's random stream comes from its id
(stats_layer.seeded), so results do not depend on the machine. Share k of n takes every n-th design not
yet in the rung's main file. Usage: python3 share.py rung2|rung3 k n
Output: stats_out/<version>/<rung>_part<k>.jsonl, merged into <rung>.jsonl afterwards (merge.py)."""
import json, os, sys
import stats_layer as S

if __name__ == "__main__":
    stage, k, n = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    load = lambda f: [json.loads(l) for l in open(f)] if os.path.exists(f) else []
    W = int(os.environ.get("WORKERS", os.cpu_count() or 1))
    done = {r["id"] for r in load(f"{S.OUT}/{stage}.jsonl")}
    if stage == "rung2":
        _, feas = S.feasible(load(f"{S.OUT}/rung1.jsonl"))
        PC = {r["id"]: (r["res"]["best"]["P"], r["res"]["best"]["C"]) for r in feas}
        todo = [r["id"] for r in feas[:1000] if r["id"] not in done][k::n]
        args, fn = {i: PC[i] for i in todo}, S.w_rung2
    else:
        r2 = load(f"{S.OUT}/rung2.jsonl")
        top = S.robust_order(r2)[:50]
        todo = [i for i in top if i not in done][k::n]
        args, fn = S.rung3_args({r["id"]: r for r in r2}, todo), S.w_gates
    print(f"{stage} share {k} of {n}: {len(todo)} designs", flush=True)
    S.checkpointed(f"{S.OUT}/{stage}_part{k}.jsonl", todo, fn, args, W)
    print("done", flush=True)
