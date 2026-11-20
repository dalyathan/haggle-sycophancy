"""Score the reasoning probes against their fixed reading rules (LADDER.md addenda RL, RL2, TM, CS; READOUT.md addenda R5, R5b).
No model is run. Usage: python pilot/score_reasoning.py  (skips any output file that does not exist yet)."""
import json, os, re

OUT = "pilot/out"


def rows(name):
    p = os.path.join(OUT, name)
    return [json.loads(l) for l in open(p)] if os.path.exists(p) else None


def ladder_rule(R, need):
    ok = sum(r["written_answer"] in r["target"] for r in R)
    walk = [r for r in R if r["target"] == [0]]
    wk = sum(r["written_answer"] == 0 for r in walk)
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
        print("CS part A (rule per 2 x 2 cell: >= 17 of 20, walk >= 3 of 4; (W0,C0) and (W1,C1) are RL2):")
        for frame in ("third", "you"):
            cell = {}
            for w in (0, 1):
                for c in (0, 1):
                    if w == c:
                        R = [r for r in RL2 if r["frame"] == frame and r["para"] == w]
                        if frame == "third" and w == 0 and RL:
                            R = RL + R
                    else:
                        R = [r for r in CS if r["frame"] == frame and r["wording"] == w and r["clause"] == c]
                    cell[w, c] = R
            if any(len(R) != 20 for R in cell.values()):
                print(f"  {frame}: incomplete", {k: len(v) for k, v in cell.items()}); continue
            ok = {k: ladder_rule(R, 17) for k, R in cell.items()}
            for k in sorted(ok):
                print(f"  {frame} W{k[0]} C{k[1]}: {ok[k]}")
            p10, p01 = ok[1, 0].endswith("pass"), ok[0, 1].endswith("pass")
            reading = {(True, False): "the clause", (False, True): "the rest of the wording",
                       (False, False): "both contribute", (True, True): "neither alone (interaction)"}[p10, p01]
            print(f"  {frame} reading: {reading}")
            for part, keep in (("pooled", lambda r: True), ("L1", lambda r: r["rung"].startswith("L1")), ("L2", lambda r: r["rung"].startswith("L2"))):
                n = {k: sum(r["written_answer"] in r["target"] for r in R if keep(r)) for k, R in cell.items()}
                ce = ((n[0, 0] - n[0, 1]) + (n[1, 0] - n[1, 1])) / 2; we = ((n[0, 0] - n[1, 0]) + (n[0, 1] - n[1, 1])) / 2
                print(f"    {part}: correct W0C0 {n[0,0]} W0C1 {n[0,1]} W1C0 {n[1,0]} W1C1 {n[1,1]}; clause effect {ce:+.1f}, wording effect {we:+.1f}")
    CSB = rows("clause_swap_sampled.jsonl")
    if CSB and RL2:
        from collections import Counter
        greedy = {(r.get("frame", "third"), r["rung"], r["v"], r["c"]): r["written_answer"] for r in (RL or []) + RL2 if r["para"] == 0}
        print(f"CS part B (reported): {len(CSB)} prompts x 3 samples")
        for frame in ("third", "you"):
            R = [r for r in CSB if r["frame"] == frame]
            if not R:
                continue
            S = [g for r in R for g in r["samples"]]
            agree = sum(len({g["written_answer"] for g in r["samples"]}) == 1 for r in R)
            maj = []
            for r in R:
                a, n = Counter(g["written_answer"] for g in r["samples"]).most_common(1)[0]
                maj.append(n >= 2 and a == greedy.get((r["frame"], r["rung"], r["v"], r["c"])))
            print(f"  {frame}: per-sample correct {sum(g['written_answer'] in r['target'] for r in R for g in r['samples'])}/{len(S)}, "
                  f"all 3 agree {agree}/{len(R)}, majority = greedy {sum(maj)}/{len(R)}, cut {sum(g['cut_off'] for g in S)}, "
                  f"mean tokens {sum(g['n_new'] for g in S) / len(S):.0f}")
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


if __name__ == "__main__":
    main()
