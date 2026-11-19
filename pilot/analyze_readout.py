"""Analysis of the readout pilot (pilot/READOUT.md, acceptance rule v2).
Usage: python pilot/analyze_readout.py pilot/out/readout_R0.jsonl [more files]
Cell annotations (targets, payoffs, optimal moves) are rebuilt from readout.build() for the file's variant and matched by
position, so rows written by an earlier version of readout.py are annotated with the current kernel targets."""
import json, os, sys
from collections import defaultdict
import warnings
import numpy as np
warnings.filterwarnings("ignore", category=RuntimeWarning)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

STAGEB = "pilot/out/pilot_4b.jsonl"
ANN = ("U", "target", "update", "target0", "u0", "du", "hash")


def load(path):
    from pilot import readout as RO
    R = [json.loads(l) for l in open(path)]
    RO.VARIANT, RO.FRESH = R[0]["variant"], bool(R[0].get("fresh"))
    P = RO.build()
    for r, p in zip(R, P):
        same = all(r.get(k) == p.get(k) for k in ("kind", "block", "ctx", "para", "item", "remark"))
        assert same and r.get("hash", p["hash"]) == p["hash"], "row does not match the prompt list"
        for k in ANN:
            r[k] = p[k]
    return R


def rank(x):
    x = np.asarray(x, float); o = np.argsort(x, kind="mergesort"); r = np.empty(len(x)); r[o] = np.arange(len(x))
    for v in np.unique(x):
        m = x == v; r[m] = r[m].mean()
    return r


def spearman(a, b):
    return float(np.corrcoef(rank(a), rank(b))[0, 1])


def qn(r):
    q = np.asarray(r["probs"], float); return q / q.sum()


def pay(r, q=None):
    q = qn(r) if q is None else q
    return float(sum(q[a] * r["U"][a - 1] for a in range(1, 10)))          # walking pays 0


def best_pay(r):
    return max(max(r["U"]), 0.0)


def value_only(v):
    return int(min(9, max(1, round(v / 2))))


def mean_by(rows, key, f):
    d = defaultdict(list)
    for r in rows:
        d[key(r)].append(f(r))
    return {k: float(np.mean(v)) for k, v in d.items()}


def acceptance(R):
    B = [r for r in R if r["kind"] == "base"]
    out = {}
    cov = np.array([r["coverage"] for r in B])
    out["A1"] = (f"coverage median {np.median(cov):.4f} (>= 0.9)", np.median(cov) >= 0.9)
    sd = np.median([r["sd_offer"] for r in B])
    ends = np.median([(qn(r)[1] + qn(r)[9]) / max(qn(r)[1:].sum(), 1e-12) for r in B])
    out["A2"] = (f"offer SD median {sd:.2f} coins (< 2.0), end mass of the offer distribution median {ends:.3f} (< 0.4)", sd < 2.0 and ends < 0.4)
    opt = np.mean([sum(qn(r)[a] for a in r["target"]) for r in B])
    out["A3"] = (f"mass on the kernel target {opt:.3f} (>= 0.25)", opt >= 0.25)
    byb = defaultdict(list)
    for r in B:
        byb[r["block"]].append(r)
    reg = np.mean([np.mean([best_pay(r) - pay(r) for r in rs]) for rs in byb.values()])
    reg_walk = np.mean([np.mean([qn(r)[0] * best_pay(r) for r in rs]) for rs in byb.values()])
    reg5 = np.mean([best_pay(rs[0]) - rs[0]["U"][4] for rs in byb.values()])
    regv = np.mean([best_pay(rs[0]) - rs[0]["U"][value_only(rs[0]["v"]) - 1] for rs in byb.values()])
    out["A4"] = (f"regret {reg:.3f} coins (walk part {reg_walk:.3f}, offer part {reg - reg_walk:.3f}) vs always-5 {reg5:.3f}, value-only {regv:.3f}",
                 reg < reg5 and reg < regv)
    eu = mean_by([r for r in B if r["u0"] is not None], lambda r: r["block"], lambda r: r["exp_u"])
    u0 = {r["block"]: r["u0"] for r in B if r["u0"] is not None}
    ks = sorted(eu)
    slope = float(np.polyfit([u0[k] for k in ks], [eu[k] for k in ks], 1)[0])
    rho = spearman([eu[k] for k in ks], [u0[k] for k in ks])
    out["A5"] = (f"slope of block-mean exp_u on u0 {slope:.3f} (>= 0.5); tie-aware Spearman {rho:.3f} (reported)", slope >= 0.5)
    eo = mean_by(B, lambda r: (r["v"], r["hist"]), lambda r: r["exp_offer"])
    ch = [eo[(v, True)] - eo[(v, False)] for v in (10, 14, 18)]
    out["A6"] = (f"history effect at v = 10, 14, 18: {', '.join(f'{c:+.2f}' for c in ch)} coins (optimal +1, +2, +1; all > 0 and mean >= 0.67)",
                 all(c > 0 for c in ch) and np.mean(ch) >= 0.67)
    base = {(r["block"], r["ctx"], r["para"]): r for r in B}
    irr = [r for r in R if r["kind"] == "irrelevant"]
    if irr:
        de = np.mean([r["exp_u"] - base[(r["block"], r["ctx"], r["para"])]["exp_u"] for r in irr])
        dw = np.mean([r["walk"] - base[(r["block"], r["ctx"], r["para"])]["walk"] for r in irr])
        ir = defaultdict(list)
        for r in irr:
            ir[(r["block"], r["ctx"], r["para"])].append(qn(r))
        cp = {}
        for d in (3, 7):
            xs = [qn(r)[d] - np.mean([x[d] for x in ir[(r["block"], r["ctx"], r["para"])]]) for r in R if r["kind"] == "number" and r["remark"] == d]
            cp[d] = float(np.mean(xs))
        out["A7"] = (f"irrelevant remarks vs baseline: exp_u {de:+.4f} (|.| <= 0.03), walk {dw:+.4f} (<= 0.05); "
                     f"number copying P(3) {cp[3]:+.4f}, P(7) {cp[7]:+.4f} (<= 0.05)",
                     abs(de) <= 0.03 and dw <= 0.05 and cp[3] <= 0.05 and cp[7] <= 0.05)
    return out, byb


def report(path):
    R = load(path); V = R[0]["variant"]
    print(f"== {path}: variant {V}, {len(R)} prompts{' (fresh contexts)' if R[0].get('fresh') else ''} ==")
    res, byb = acceptance(R)
    for k, (txt, ok) in res.items():
        print(f"{k} {txt}  {'pass' if ok else 'FAIL'}")
    ok = all(v[1] for v in res.values())
    print(f"VERDICT {V}: " + ("PASS" if ok else "FAIL on " + ", ".join(k for k, v in res.items() if not v[1])))
    print("baseline option distribution by block (walk, 1..9), mean over contexts and paraphrases:")
    for b, rs in sorted(byb.items()):
        q = np.mean([qn(r) for r in rs], 0); r0 = rs[0]
        print(f"   v={r0['v']:>2} hist={int(r0['hist'])} target={r0['target']}: " + " ".join(f"{x:.2f}" for x in q) +
              f"  exp_offer {np.mean([r['exp_offer'] for r in rs]):.2f}  regret {np.mean([best_pay(r) - pay(r) for r in rs]):.2f}")
    print("all prompts, mean distribution: " + " ".join(f"{x:.2f}" for x in np.mean([qn(r) for r in R], 0)))
    for k in ("p_space", "p_direct_digit", "p_word", "p_two_digit_after_1"):
        xs = [r[k] for r in R if r.get(k) is not None]
        if xs:
            print(f"reading: {k} mean {np.mean(xs):.4f} max {np.max(xs):.4f}")
    if V == "R4":
        g = [r["generation"] for r in R if r.get("generation")]
        print(f"reasoning: 'Answer' written in {np.mean([x['has_answer'] for x in g]):.2f}, cut off at the token limit in {np.mean([x['cut_off'] for x in g]):.2f}")
        return ok
    base = {(r["block"], r["ctx"], r["para"]): r for r in R if r["kind"] == "base"}
    by_item = defaultdict(list)
    for r in R:
        if r["kind"] == "info":
            b = base[(r["block"], r["ctx"], r["para"])]
            by_item[tuple(r["item"])].append(dict(du=r["du"] if r["update"] == "move" else None, d=r["exp_u"] - b["exp_u"],
                                                  dw=r["walk"] - b["walk"], walk_t=r["target"] == [0], reg=best_pay(r) - pay(r),
                                                  tmass=sum(qn(r)[a] for a in r["target"])))
    print("updating by item: mean shift in exp_u | mean optimal move (scored cells) | within-item slope | walk shift | "
          "walk-target share | mass on target | regret")
    for it, xs in sorted(by_item.items()):
        d = [x for x in xs if x["du"] is not None]
        sl = float(np.polyfit([x["du"] for x in d], [x["d"] for x in d], 1)[0]) if len({x["du"] for x in d}) > 1 else float("nan")
        print(f"   {str(it):38s} {np.mean([x['d'] for x in xs]):+.3f} | {np.mean([x['du'] for x in d]) if d else float('nan'):+.3f} | "
              f"{sl:+.3f} | {np.mean([x['dw'] for x in xs]):+.3f} | {np.mean([x['walk_t'] for x in xs]):.2f} | "
              f"{np.mean([x['tmass'] for x in xs]):.2f} | {np.mean([x['reg'] for x in xs]):.2f}  n={len(xs)}")
    sc = [x for xs in by_item.values() for x in xs if x["du"] is not None]
    if len({x["du"] for x in sc}) > 1:
        print(f"pooled updating slope (scored move cells, through the origin): "
              f"{np.sum([x['du'] * x['d'] for x in sc]) / np.sum([x['du'] ** 2 for x in sc]):+.3f}")
    pd = [np.mean([r["exp_u"] for r in rs if r["para"] == 1]) - np.mean([r["exp_u"] for r in rs if r["para"] == 0]) for rs in byb.values()]
    print(f"paraphrase 1 minus 0 on baselines (exp_u): {np.mean(pd):+.4f}" + ("  [R2: paraphrase and option order together]" if V == "R2" else ""))
    if V == "R0" and not R[0].get("fresh"):
        fast_path_gate(R)
    return ok


def fast_path_gate(R):
    """READOUT.md gate: the fast path (prefix cache plus batching) against the stored stage-B outputs on shared prompts."""
    from pilot import run_pilot as RP, readout as RO
    RO.VARIANT, RO.FRESH = "R0", False
    new = RO.build(); old = RP.build(); stored = [json.loads(l) for l in open(STAGEB)]
    key = lambda p: (p["messages"][0]["content"], p["messages"][1]["content"])
    oi = {key(p): i for i, p in enumerate(old)}
    dp, de = [], []
    for i, p in enumerate(new[:len(R)]):
        j = oi.get(key(p))
        if j is not None and j < len(stored):
            dp.append(np.abs(np.asarray(R[i]["probs"]) - np.asarray(stored[j]["probs"])).max())
            de.append(R[i]["exp_u"] - stored[j]["exp_u"])
    ok = max(dp) <= 0.03 and np.std(de) <= 0.005
    print(f"FAST-PATH GATE on {len(dp)} shared prompts: max abs prob diff {max(dp):.4f} (<= 0.03), exp_u difference mean {np.mean(de):+.4f}, "
          f"SD {np.std(de):.4f} (<= 0.005), max |.| {np.max(np.abs(de)):.4f}  {'pass' if ok else 'FAIL'}")


if __name__ == "__main__":
    out = {}
    for p in sys.argv[1:]:
        out[p] = report(p); print()
    if len(out) > 1:
        print("summary:", {os.path.basename(k): ("PASS" if v else "FAIL") for k, v in out.items()})
