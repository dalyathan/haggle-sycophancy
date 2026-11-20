"""Score the reasoning probes against their fixed reading rules (LADDER.md addenda RL, RL2, TM, CS; READOUT.md addenda R5, R5b).
No model is run. Usage: python pilot/score_reasoning.py  (skips any output file that does not exist yet)."""
import json, os, re
from collections import Counter
from math import comb

OUT = "pilot/out"


def rows(name):
    p = os.path.join(OUT, name)
    return [json.loads(l) for l in open(p)] if os.path.exists(p) else None


def right(r):
    """Correct: the written answer is in the target set; a cut-off row counts as wrong even if it parsed an answer (RL2; review O7)."""
    return r["written_answer"] in r["target"] and not r["cut_off"]


def passes(R, need, flip=None):
    """The RL2 rule; flip = index of one row whose correctness is toggled (for the fragility check)."""
    walk_cells = [r["target"] == [0] for r in R]
    good = [right(r) for r in R]
    if flip is not None:
        good[flip] = not good[flip]
    wk = sum(g for g, w in zip(good, walk_cells) if w)
    return sum(good) >= need and wk >= min(3, sum(walk_cells))


def mcnemar(a, b):
    """Exact two-sided sign test on discordant pairs: a = correct only in the first, b = only in the second."""
    n = a + b
    if n == 0:
        return 1.0
    k = min(a, b)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def ladder_rule(R, need):
    ok = sum(right(r) for r in R)
    walk = [r for r in R if r["target"] == [0]]
    wk = sum(r["written_answer"] == 0 and not r["cut_off"] for r in walk)
    cut = sum(bool(r["cut_off"]) for r in R)
    mean = sum(r["n_new"] for r in R) / len(R)
    verdict = "pass" if ok >= need and wk >= min(3, len(walk)) else "fail"
    return f"correct {ok}/{len(R)}, walk {wk}/{len(walk)}, cut {cut}, mean tokens {mean:.0f}: {verdict}"


def main():
    RL = rows("reason_ladder.jsonl")
    if RL:
        print("RL (rule: >= 13 of 15, walk >= 3 of 4):", ladder_rule(RL, 13))
    RL2 = rows("reason_ladder2.jsonl")
    if RL2:
        print("RL2 (rule per condition: >= 17 of 20, walk >= 3 of 4; third person paraphrase 0 includes RL):")
        for frame, para in (("third", 0), ("third", 1), ("you", 0), ("you", 1)):
            R = [r for r in RL2 if r["frame"] == frame and r["para"] == para]
            if frame == "third" and para == 0 and RL:
                R = RL + R
            print(f"  {frame} p{para}:", ladder_rule(R, 17))
    TM = rows("think_probe.jsonl")
    if TM:
        ok = sum(r["written_answer"] in r["target"] for r in TM)
        walk = [r for r in TM if r["target"] == [0]]
        wk = sum(r["written_answer"] == 0 for r in walk)
        verdict = "pass" if ok >= 7 and wk == len(walk) else "fail"
        print(f"TM (rule: >= 7 of 8 incl. both walk cells): correct {ok}/{len(TM)}, walk {wk}/{len(walk)}, "
              f"thinking not closed {sum(r['cut_off'] for r in TM)}: {verdict}")
        for r in TM:
            th = r["raw"].split("</think>")[0]
            print(f"  {r['rung']} v={r['v']} c={r['c']} target={r['target']} answer={r['written_answer']} tokens={r['n_new']} "
                  f"'Wait' in thinking: {len(re.findall(r'\bWait\b', th))}")
    CS = rows("clause_swap.jsonl")
    if CS and RL2:
        score_cs(CS, RL, RL2)
    CSB = rows("clause_swap_sampled.jsonl")
    if CSB and RL2:
        score_cs_b(CSB, RL, RL2)
    R5b = rows("reason_probe_R5b.jsonl")
    if R5b:
        near = sum(r["regret"] is not None and r["regret"] <= 0.3 for r in R5b)
        print(f"R5b (rule: written answer within 0.3 coins of best in >= 6 of 8): {near}/{len(R5b)}: "
              f"{'encouraging' if near >= 6 and len(R5b) == 8 else 'not encouraging' if len(R5b) == 8 else 'incomplete'}")
        R5 = {(r["v"], r["hist"]): r for r in rows("reason_probe_R5.jsonl")}
        for r in R5b:
            full = R5[(r["v"], r["hist"])]["raw"] + r["more"]
            uses = bool(re.search(r"reject\w*[^.\n]{0,40}\b1\b|\b1\b[^.\n]{0,40}reject|earlier|already (?:proposed|offered)", full)) if r["hist"] else None
            print(f"  v={r['v']} hist={int(r['hist'])} target={r['target']} written={r['written_answer']} regret={r['regret']} "
                  f"tokens={r['n_total']} cut={r['cut_off']}" + ("" if uses is None else f" keyword hit for the rejected 1 (crude; check by reading): {uses}"))


def cs_cells(CS, RL, RL2, frame):
    cell = {}
    for w in (0, 1):
        for c in (0, 1):
            if w == c:
                R = [r for r in RL2 if r["frame"] == frame and r["para"] == w]
                if frame == "third" and w == 0 and RL:
                    R = RL + R
            else:
                R = [r for r in CS if r["frame"] == frame and r["wording"] == w and r["clause"] == c]
            key = lambda r: (r["rung"], r["v"], r["c"] if r["c"] is not None else -1)
            cell[w, c] = sorted(R, key=key)
    return cell


def reading(cell, need, keep):
    sub = {k: [r for r in R if keep(r)] for k, R in cell.items()}
    p10, p01 = passes(sub[1, 0], need), passes(sub[0, 1], need)
    name = {(True, False): "the clause", (False, True): "the rest of the wording",
            (False, False): "both contribute", (True, True): "neither alone (interaction)"}[p10, p01]
    fragile = any(passes(sub[k], need, i) != passes(sub[k], need) for k in ((1, 0), (0, 1)) for i in range(len(sub[k])))
    return name, fragile, sub


def score_cs(CS, RL, RL2):
    """Addendum CS part A, with the additions of the pre-run review (R1, R2, O1, O2)."""
    print("CS part A (rule per 2 x 2 cell: >= 17 of 20, walk >= 3 of 4; (W0,C0) and (W1,C1) are RL2):")
    pooled_pairs = {"W0: C0 vs C1": [0, 0], "W1: C0 vs C1": [0, 0]}
    for frame in ("third", "you"):
        cell = cs_cells(CS, RL, RL2, frame)
        if any(len(R) != 20 for R in cell.values()):
            print(f"  {frame}: incomplete", {k: len(v) for k, v in cell.items()}); continue
        keys = [[(r["rung"], r["v"], r["c"]) for r in R] for R in cell.values()]
        assert all(k == keys[0] for k in keys), "cells do not line up"
        for k in sorted(cell):
            print(f"  {frame} W{k[0]} C{k[1]}: {ladder_rule(cell[k], 17)}")
        name, fragile, _ = reading(cell, 17, lambda r: True)
        print(f"  {frame} primary reading (pooled L1 + L2; the L1 swap is a different clause): {name}"
              + (" -- FRAGILE: one changed answer in a swap cell changes it; inconclusive at n = 20" if fragile else ""))
        name2, fragile2, _ = reading(cell, 13, lambda r: r["rung"].startswith("L2"))
        tag = "" if frame == "third" else " (descriptive only: the W0 C0 anchor fails the L2 bar in this framing)"
        print(f"  {frame} L2-only reading (>= 13 of 15, walk >= 3 of 4){tag}: {name2}" + (" -- FRAGILE" if fragile2 else ""))
        for part, keep in (("pooled", lambda r: True), ("L1", lambda r: r["rung"].startswith("L1")), ("L2", lambda r: r["rung"].startswith("L2"))):
            n = {k: sum(right(r) for r in R if keep(r)) for k, R in cell.items()}
            cut = {k: sum(r["cut_off"] for r in R if keep(r)) for k, R in cell.items()}
            wrong = {k: sum(not r["cut_off"] and not right(r) for r in R if keep(r)) for k, R in cell.items()}
            ce = ((n[0, 0] - n[0, 1]) + (n[1, 0] - n[1, 1])) / 2; we = ((n[0, 0] - n[1, 0]) + (n[0, 1] - n[1, 1])) / 2
            ia = n[0, 0] - n[0, 1] - n[1, 0] + n[1, 1]
            fmt = lambda d: " ".join(f"W{k[0]}C{k[1]} {d[k]}" for k in sorted(d))
            print(f"    {part}: correct {fmt(n)}; clause effect {ce:+.1f}, wording effect {we:+.1f}, interaction {ia:+d}")
            print(f"    {part}: cut {fmt(cut)}; wrong among finished {fmt(wrong)}")
        for label, A, B in (("W0: C0 vs C1", cell[0, 0], cell[0, 1]), ("W1: C0 vs C1", cell[1, 0], cell[1, 1])):
            a = sum(right(x) and not right(y) for x, y in zip(A, B)); b = sum(right(y) and not right(x) for x, y in zip(A, B))
            pooled_pairs[label][0] += a; pooled_pairs[label][1] += b
            print(f"    paired, clause within {label}: correct only with C0 {a}, only with C1 {b}, exact p = {mcnemar(a, b):.3f}")
        print(f"    per cell ({frame}): rung v c target | W0C0 W0C1 W1C0 W1C1 (answer/tokens, * = cut)")
        for i, r in enumerate(cell[0, 0]):
            row = [f"{cell[k][i]['written_answer']}/{cell[k][i]['n_new']}{'*' if cell[k][i]['cut_off'] else ''}" for k in ((0, 0), (0, 1), (1, 0), (1, 1))]
            print(f"      {r['rung']:4} {r['v']:2} {str(r['c']):4} {r['target']} | " + "  ".join(f"{x:9}" for x in row))
    for label, (a, b) in pooled_pairs.items():
        print(f"  paired, both framings, clause within {label}: only C0 {a}, only C1 {b}, exact p = {mcnemar(a, b):.3f}")


def score_cs_b(CSB, RL, RL2):
    """Addendum CS part B (reported only; review O3). Measures sampling variability at the passing W0 C0 cell only."""
    greedy = {(r.get("frame", "third"), r["rung"], r["v"], r["c"]): r for r in (RL or []) + RL2 if r["para"] == 0}
    print(f"CS part B (reported; sampling noise at the W0 C0 cell only): {len(CSB)} prompts x 3 samples")
    for frame in ("third", "you"):
        R = [r for r in CSB if r["frame"] == frame]
        if not R:
            continue
        S = [dict(g, target=r["target"]) for r in R for g in r["samples"]]
        per_index = []
        for j in range(3):
            Rj = [dict(r["samples"][j], target=r["target"]) for r in R]
            per_index.append(f"sample {j + 1}: {ladder_rule(Rj, 17)}" if len(Rj) == 20 else f"sample {j + 1}: {len(Rj)} rows")
        dist = Counter(sum(right(dict(g, target=r["target"])) for g in r["samples"]) for r in R)
        parsed = [[g["written_answer"] for g in r["samples"] if g["written_answer"] is not None] for r in R]
        agree = sum(len(a) == 3 and len(set(a)) == 1 for a in parsed)
        maj, nomaj, compared = 0, 0, 0
        for r, a in zip(R, parsed):
            top = Counter(a).most_common(1)
            if not top or top[0][1] < 2:
                nomaj += 1; continue
            gr = greedy.get((r["frame"], r["rung"], r["v"], r["c"]))
            if gr is None or gr["written_answer"] is None:
                continue
            compared += 1; maj += top[0][0] == gr["written_answer"]
        print(f"  {frame}: per-sample correct {sum(right(g) for g in S)}/{len(S)}; prompts by correct samples (0-3) "
              f"{[dist.get(i, 0) for i in range(4)]}; all 3 parsed and equal {agree}/{len(R)}; no majority {nomaj}; "
              f"majority = greedy (both parsed) {maj}/{compared}; cut {sum(g['cut_off'] for g in S)}; "
              f"mean tokens {sum(g['n_new'] for g in S) / len(S):.0f}")
        for line in per_index:
            print(f"    {line}")


if __name__ == "__main__":
    main()
