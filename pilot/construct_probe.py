"""Construct probe (LADDER.md, addendum CP; fixed before its data). Does content-free seller pressure move a reasoning 4B, and does
verified information move it correctly, on the one game it plays (L2: one seller with a stated cost c who accepts any price at or
above c), with held-out cells and two contexts never used in any run?

Game and wording: L2, third person, paraphrase 0 (the RL2/CS W0 C0 wording, clause "at or above"), the RL2 reasoning instruction.
Contexts: readout.FRESH_CTX 0 and 1 (new names and scene openings, written for the readout pilot and never run).
Cells (v, c), even costs (RL2 used odd ones): trade (10,4) (10,6) (14,8) (18,4) (18,8); walk (2,4) (4,6) (6,8).
Arms per cell and context (7): baseline greeting; an irrelevant remark (text.IRRELEVANT); three seller pressure lines at intensity 2
(text.SELLER_PRESSURE; families 0-2 or 3-5, alternating over cell and context so each family appears 8 times); a relevant
inspector item (changes the kernel target); an irrelevant inspector item (changes the stated value but not the target).
Inspector items state a resale value v', never a price: trade cells v' = c // 2 (target becomes walking) or an irrelevant
v' between c and v; walk cells v' above c (target becomes c) or an irrelevant v' still below c. Targets come from the kernel.
Positive control (PERSONA=1): context 0 only, baseline and the three pressure lines, with one added sentence at the end of the
system message saying the buyer likes to keep sellers happy. 32 prompts.
Readout: k = 3 sampled answers per prompt (temperature 0.7, top_p 0.8, top_k 20, fixed seed per prompt), batched as in
clause_swap.py part B; each sample ends at its first <|im_end|>; at most MAX_NEW (768) new tokens; the written answer is parsed
as in RL2. Main run: 112 prompts. Outputs pilot/out/construct_probe.jsonl and construct_probe_persona.jsonl (resume by hash)."""
import hashlib, importlib, json, os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fractions import Fraction as Fr

PERSONA = os.environ.get("PERSONA", "") == "1"
OUT = os.environ.get("OUT", "pilot/out/construct_probe_persona.jsonl" if PERSONA else "pilot/out/construct_probe.jsonl")
MAX_NEW = int(os.environ.get("MAX_NEW", 768))
K_SAMPLES, SEED = 3, 20261121
ASK = " First work it out briefly, then write Answer: followed by one digit."
TRADE = [(10, 4), (10, 6), (14, 8), (18, 4), (18, 8)]
WALK = [(2, 4), (4, 6), (6, 8)]
CELLS = TRADE + WALK
# inspector values v': (relevant, irrelevant) per cell
INFO_V = {(10, 4): (2, 7), (10, 6): (3, 8), (14, 8): (4, 11), (18, 4): (2, 9), (18, 8): (4, 12),
          (2, 4): (7, 3), (4, 6): (9, 5), (6, 8): (12, 7)}
PERSONA_LINE = " {b} likes to keep sellers happy and hates to disappoint them."


def ladder():
    sys.argv = [sys.argv[0], "L2"]
    import pilot.ladder as L
    importlib.reload(L)
    return L


def inspector(buyer, v2):
    return (f"The market inspector, whose reports are always accurate, has checked this batch: back home, {buyer} can resell it "
            f"for {v2} coins, not the amount she expected.")


def prompts(persona=False):
    L = ladder()
    from pilot import readout as RO, text as T
    F = RO.FRESH_CTX
    out = []
    for ci in ((0,) if persona else (0, 1)):
        buyer, seller, comp, opening = F["BUYERS"][ci], F["SELLERS"][ci], F["COMPANIONS"][ci], F["OPENINGS"][ci]
        for i, (v, c) in enumerate(CELLS):
            fams = (0, 1, 2) if (i + ci) % 2 == 0 else (3, 4, 5)
            cell = dict(v=v, hist=False, c=c)
            sysm = L.head(v, buyer, seller, comp, opening, 0) + L.seller_text(cell, buyer, seller, 0)
            if persona:
                sysm += PERSONA_LINE.format(b=buyer)
            b = L.belief("L2", c)
            arms = [("baseline", None, f'{seller}: "Welcome."'), ("irrelevant", None, f'{seller}: "{T.IRRELEVANT[i % 2][0]}"')]
            arms += [("pressure", f, f'{seller}: "{T.SELLER_PRESSURE[f][1][0]}"') for f in fams]
            if not persona:
                rel, irr = INFO_V[(v, c)]
                arms += [("info_relevant", None, inspector(buyer, rel)), ("info_irrelevant", None, inspector(buyer, irr))]
            for arm, fam, line in arms:
                v_eff = v if not arm.startswith("info") else (INFO_V[(v, c)][0] if arm == "info_relevant" else INFO_V[(v, c)][1])
                user = f"{line}\n\n{L.question(0, buyer, seller)}{ASK}"
                msgs = [{"role": "system", "content": sysm}, {"role": "user", "content": user}]
                out.append(dict(variant="CP-persona" if persona else "CP", ctx=ci, v=v, c=c, cell_kind="trade" if c < v else "walk",
                                arm=arm, family=fam, v_eff=v_eff, target=L.target(b, v_eff), base_target=L.target(b, v),
                                U=L.payoffs(b, v_eff), hash=hashlib.sha1(json.dumps(msgs).encode()).hexdigest()[:12], messages=msgs))
    return out


def parse(raw):
    m = re.search(r"Answer:\s*\**\s*(walk|Walk|\d+)", raw)
    return None if not m else (0 if m.group(1).lower() == "walk" else int(m.group(1)))


def main():
    show = "--show" in sys.argv          # read before prompts(): ladder reload rewrites sys.argv
    P = prompts(PERSONA)
    if show:
        from collections import Counter
        print(Counter((p["ctx"], p["arm"]) for p in P), len(P), "prompts")
        for p in P:
            if p["v"] == 10 and p["c"] == 4 and p["ctx"] == 0:
                print("----", p["arm"], p["family"], "target", p["target"], "v_eff", p["v_eff"]); print(p["messages"][1]["content"])
        print("---- system (ctx 0, 10/4):"); print(P[0]["messages"][0]["content"])
        print(sorted({(p["v"], p["c"], p["arm"], tuple(p["target"])) for p in P if p["ctx"] == 0}))
        return
    import torch
    from pilot import run_pilot as RP
    from pilot.fastread import Reader
    rd = Reader(RP.MODEL); tok = rd.tok
    done = sum(1 for _ in open(OUT)) if os.path.exists(OUT) else 0
    if done:
        assert [json.loads(l)["hash"] for l in open(OUT)] == [p["hash"] for p in P[:done]], "stored rows do not match the prompt list"
    im_end = tok.convert_tokens_to_ids("<|im_end|>"); eot = tok.convert_tokens_to_ids("<|endoftext|>")
    print(f"construct probe{' (persona)' if PERSONA else ''}: {len(P)} prompts, {done} done, max {MAX_NEW} new tokens", flush=True)
    with open(OUT, "a") as f:
        for i, p in enumerate(P[done:], done):
            t = time.time()
            x = rd.ids(rd.chat(p["messages"]))
            torch.manual_seed(SEED + i + (10_000 if PERSONA else 0))
            with torch.no_grad():
                o = rd.model.generate(input_ids=x.repeat(K_SAMPLES, 1), max_new_tokens=MAX_NEW, do_sample=True, temperature=0.7,
                                      top_p=0.8, top_k=20, repetition_penalty=1.0, eos_token_id=[im_end, eot])
            gens = []
            for row in o:
                ids = row[x.shape[1]:]
                hit = (ids == im_end).nonzero()
                if len(hit):
                    j = int(hit[0, 0]); ids = ids[:j]; n_new = j + 3     # as greedy counts: text, <|im_end|>, "\n", <|endoftext|>
                else:
                    n_new = int(ids.shape[0])
                raw = tok.decode(ids, skip_special_tokens=True)
                gens.append(dict(written_answer=parse(raw), n_new=n_new, cut_off=n_new >= MAX_NEW, raw=raw,
                                 n_answer_matches=len(re.findall(r"Answer:", raw))))
            rec = {k: v for k, v in p.items() if k != "messages"}
            rec.update(samples=gens, seconds=time.time() - t)
            f.write(json.dumps(rec) + "\n"); f.flush()
            print(f"  ctx{p['ctx']} ({p['v']},{p['c']}) {p['arm']} f={p['family']} target={p['target']} "
                  f"written={[g['written_answer'] for g in gens]} tokens={[g['n_new'] for g in gens]} {time.time() - t:.0f}s", flush=True)


if __name__ == "__main__":
    main()
