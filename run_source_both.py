"""Side check: rungs 2-3 on the cheapest designs whose information comes from both sources
(seller cheap talk and verified), which never reach the overall top 50. Results in stats_out/both/."""
import json, os, time
import stats_layer as S

if __name__ == "__main__":
    t0 = time.time(); out = f"{S.OUT}/both"; os.makedirs(out, exist_ok=True)
    W = int(os.environ.get("WORKERS", os.cpu_count() or 1))
    r1 = [json.loads(l) for l in open(f"{S.OUT}/rung1.jsonl")]
    feas = sorted((r for r in r1 if r["res"] and S.required(*S.unpack(r["id"])) and S.unpack(r["id"])[0].source == "both"),
                  key=lambda r: (r["res"]["N"], r["res"]["se_l"]))
    by_id = {r["id"]: r for r in feas}
    PC = {i: (by_id[i]["res"]["P"], by_id[i]["res"]["C"]) for i in by_id}
    top = [r["id"] for r in feas[:100]]
    r2 = S.checkpointed(f"{out}/rung2.jsonl", top, S.w_rung2, PC, W)
    rank = {i: k for k, i in enumerate(top)}
    robust = sorted((r["id"] for r in r2 if min(r["p1"], r["p2"]) >= 0.8), key=rank.get)
    print(f"rung 2: {len(robust)}/{len(r2)} keep power ({time.time() - t0:.0f}s)")
    r3 = S.checkpointed(f"{out}/rung3.jsonl", robust[:50], S.w_gates,
                        {i: PC[i] + (by_id[i]["res"]["N"],) for i in robust[:50]}, W)
    print(f"rung 3: {sum(r['V2'] and r['V3'] and r['V4'] for r in r3)}/{len(r3)} pass V2, V3 and V4 ({time.time() - t0:.0f}s)")
    for k in ("V2", "V3", "V4"):
        print(f"  {k} pass rate {sum(r[k] for r in r3)}/{len(r3)}")
