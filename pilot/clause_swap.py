"""Clause-swap test (LADDER.md, addendum CS; diagnostic, fixed before its data).
RL2 found the reasoning readout passes paraphrase 0 and fails paraphrase 1, but paraphrase 1 rewrites every sentence. This test swaps
only the seller's acceptance clause between the two wordings, giving the two missing cells of a 2 x 2 (rest of wording W x clause C):
  (W0, C0) = RL2 paraphrase 0 and (W1, C1) = RL2 paraphrase 1 (already run); (W0, C1) and (W1, C0) are run here.
Clauses: L1  C0 "accepts any price at all"            C1 "accepts whatever price is offered"
         L2  C0 "accepts any price at or above c ..."   C1 "accepts any price that reaches c ..."
Same procedure as reason_ladder2.py: the same 20 cells (L1 at 5 values, L2 at 15 cells), context 0, both framings, reason first
("First work it out briefly, then write Answer: followed by one digit."), greedy, at most 512 new tokens. 80 prompts.
Part B (SAMPLE=1): k = 3 sampled answers (temperature 0.7, top_p 0.8, top_k 20, seed fixed) for the 40 (W0, C0) prompts, generated as
one batch of 3 per prompt, each sample truncated at its first <|im_end|> (pre-run review R5); reported only. Outputs: pilot/out/clause_swap.jsonl (A), pilot/out/clause_swap_sampled.jsonl (B).
The prompt hash covers the final messages (instruction included)."""
import hashlib, json, os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np

SAMPLE = os.environ.get("SAMPLE", "") == "1"
OUT = os.environ.get("OUT", "pilot/out/clause_swap_sampled.jsonl" if SAMPLE else "pilot/out/clause_swap.jsonl")
MAX_NEW = int(os.environ.get("MAX_NEW", 512))
K_SAMPLES, SEED = 3, 20261120

CLAUSES = {"L1": ("accepts any price at all.", "accepts whatever price is offered."),
           "L2": ("accepts any price at or above {c} {cn}.", "accepts any price that reaches {c} {cn}.")}


def swap(p):
    """Return p with the acceptance clause of the other paraphrase (in the system message only)."""
    base = p["rung"].rstrip("y")
    c = p["c"]; cn = "coin" if c == 1 else "coins"
    own, other = (CLAUSES[base][i].format(c=c, cn=cn) for i in ((0, 1) if p["para"] == 0 else (1, 0)))
    sysm = p["messages"][0]["content"]
    assert sysm.count(own) == 1, (p["rung"], p["para"], own)
    p["messages"][0]["content"] = sysm.replace(own, other)
    return p


def prompts(sampled=False):
    from pilot import reason_ladder2 as R2
    out = []
    for frame in ("third", "you"):
        for para in ((0,) if sampled else (0, 1)):
            for base in ("L1", "L2"):
                rung = base + ("y" if frame == "you" else "")
                for p in R2.rung_prompts(rung, para, "all"):
                    if not sampled:
                        p = swap(p)
                    p.update(variant="CS-B" if sampled else "CS", frame=frame, wording=para, clause=para if sampled else 1 - para)
                    p["hash"] = hashlib.sha1(json.dumps(p["messages"]).encode()).hexdigest()[:12]
                    out.append(p)
    return out


def parse(raw):
    m = re.search(r"Answer:\s*\**\s*(walk|Walk|\d+)", raw)
    return None if not m else (0 if m.group(1).lower() == "walk" else int(m.group(1)))


def main():
    show = "--show" in sys.argv          # read before prompts(): ladder.build() rewrites sys.argv
    P = prompts(SAMPLE)
    if show:
        from collections import Counter
        print(Counter((p["frame"], p["wording"], p["clause"], p["rung"]) for p in P), len(P), "prompts")
        for p in P:
            if p["rung"] in ("L2", "L2y") and p["v"] == 10 and p["c"] == 3:
                print("----", p["frame"], "W", p["wording"], "C", p["clause"]); print(p["messages"][0]["content"]); print(p["messages"][1]["content"])
        return
    import torch
    from pilot import run_pilot as RP
    from pilot.fastread import Reader
    rd = Reader(RP.MODEL); tok = rd.tok
    done = sum(1 for _ in open(OUT)) if os.path.exists(OUT) else 0
    if done:   # resume only onto the same prompt list (review O6)
        stored = [json.loads(l)["hash"] for l in open(OUT)]
        assert stored == [p["hash"] for p in P[:done]], "stored rows do not match the prompt list"
    im_end = tok.convert_tokens_to_ids("<|im_end|>")
    print(f"clause swap {'part B (sampled)' if SAMPLE else 'part A'}: {len(P)} prompts, {done} done, max {MAX_NEW} new tokens", flush=True)
    with open(OUT, "a") as f:
        for i, p in enumerate(P[done:], done):
            t = time.time()
            x = rd.ids(rd.chat(p["messages"]))
            with torch.no_grad():
                if SAMPLE:
                    torch.manual_seed(SEED + i)
                    o = rd.model.generate(input_ids=x.repeat(K_SAMPLES, 1), max_new_tokens=MAX_NEW, do_sample=True,
                                          temperature=0.7, top_p=0.8, top_k=20, repetition_penalty=1.0,
                                          eos_token_id=[im_end, tok.convert_tokens_to_ids("<|endoftext|>")])
                else:
                    o = rd.model.generate(input_ids=x, max_new_tokens=MAX_NEW, do_sample=False, repetition_penalty=1.0,
                                          temperature=None, top_p=None, top_k=None)
            rec = {k: v for k, v in p.items() if k not in ("messages", "buyer")}
            gens = []
            for row in o:
                ids = row[x.shape[1]:]
                if SAMPLE:
                    # review R5: a sample ends at its first <|im_end|>; n_new counted as greedy counts it (text tokens, <|im_end|>,
                    # "\n", <|endoftext|>: index of <|im_end|> + 3). Without <|im_end|> it ran to MAX_NEW and is cut off.
                    hit = (ids == im_end).nonzero()
                    if len(hit):
                        j = int(hit[0, 0]); ids = ids[:j]; n_new = j + 3
                    else:
                        n_new = int(ids.shape[0])
                else:
                    n_new = int(ids.shape[0])          # as in reason_ladder2.py
                raw = tok.decode(ids, skip_special_tokens=True)
                gens.append(dict(written_answer=parse(raw), n_new=n_new, cut_off=n_new >= MAX_NEW, raw=raw,
                                 n_answer_matches=len(re.findall(r"Answer:", raw))))
            if SAMPLE:
                rec.update(samples=gens)
            else:
                rec.update(gens[0])
            rec["seconds"] = time.time() - t
            f.write(json.dumps(rec) + "\n"); f.flush()
            print(f"  {p['frame']} W{p['wording']} C{p['clause']} {p['rung']} v={p['v']} c={p['c']} target={p['target']} "
                  f"written={[g['written_answer'] for g in gens]} tokens={[g['n_new'] for g in gens]} {time.time() - t:.0f}s", flush=True)


if __name__ == "__main__":
    main()
