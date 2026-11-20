"""Score the reasoning probes against their fixed reading rules (LADDER.md addenda RL, RL2, TM; READOUT.md addenda R5, R5b).
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
                  f"tokens={r['n_total']} cut={r['cut_off']}" + ("" if uses is None else f" mentions the rejected 1 (keyword): {uses}"))


if __name__ == "__main__":
    main()
