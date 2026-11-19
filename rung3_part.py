"""Run one share of rung 3 (gates V2, V3, VS, V4) on its own machine. Every design's random stream comes
from its id (stats_layer.seeded), so results do not depend on which machine runs it. The remaining
designs are those of the top 50 not yet in stats_out/<version>/rung3.jsonl; share k of n takes every
n-th of them starting at k. Output: rung3_part<k>.jsonl, merged into rung3.jsonl afterwards.
Usage: python3 rung3_part.py k n"""
import json, os, sys
import stats_layer as S

if __name__ == "__main__":
    k, n = int(sys.argv[1]), int(sys.argv[2])
    r2 = [json.loads(l) for l in open(f"{S.OUT}/rung2.jsonl")]
    r2d = {r["id"]: r for r in r2}
    robust = sorted((r["id"] for r in r2 if r["best"] and min(r["H1"], r["H2"], r["H3"], r["H4"]) >= 0.8),
                    key=lambda i: (r2d[i]["best"]["N"], -r2d[i]["H1"], i))
    done = {json.loads(l)["id"] for l in open(f"{S.OUT}/rung3.jsonl")} if os.path.exists(f"{S.OUT}/rung3.jsonl") else set()
    todo = [i for i in robust[:50] if i not in done][k::n]
    print(f"share {k} of {n}: {len(todo)} designs", flush=True)
    args = {i: (r2d[i]["best"]["P"], r2d[i]["best"]["C"], r2d[i]["best"]["N"], r2d[i]["r"], r2d[i]["r_pair"]) for i in todo}
    W = int(os.environ.get("WORKERS", os.cpu_count() or 1))
    S.checkpointed(f"{S.OUT}/rung3_part{k}.jsonl", todo, S.w_gates, args, W)
    print("done", flush=True)
