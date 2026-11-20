"""Game ladder (pilot/LADDER.md): the same model (Qwen3.5-4B, base), the same readout (R3: the stage-B instruction "one digit,
1 to 9 for a price, 0 to walk away", read after "Answer:" with the two-sequence reading of readout.py) and baseline prompts only,
on games of increasing difficulty. Separates "the model cannot play in one step" from "this game is too hard".

Rungs
  L1  one seller who accepts any price (optimum: offer 1).
  L2  one seller with a stated cost c in {3, 5, 7, 9}, who accepts any price at or above c (optimum: c if c < v, else walk away).
  L3  every seller has a cost uniform on 1..8 and accepts at or above it; with and without the history (an offer of 1 was rejected).
  L3b as L3 with the cost uniform on 1..4 (optimum 1, 3, 4, 4, 4: not half the value); no history.
  L3c L3 plus the stage-B credibility paragraph (splits L3 -> L4).
  L4b the full selected game (as readout R3), with the buyer addressed in the second person ("You are a travelling merchant ...
      What price do you propose?"). The third-person full game is readout R3 (pilot/out/readout_R3.jsonl, baseline rows).
  L1y, L2y  L1 and L2 in the second person.
Values v in {2, 6, 10, 14, 18}; 3 contexts x 2 paraphrases.

Usage: python pilot/ladder.py L1|L2|L3|L4b [--dry N] [--show]; OUT defaults to pilot/out/ladder_<rung>.jsonl (resumes)."""
import hashlib, json, os, sys, time
from fractions import Fraction as Fr
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import kernel as K, stats_layer as S
from pilot import text as T
from pilot import run_pilot as RP
from pilot import readout as RO

RUNGS = ("L1", "L1y", "L2", "L2y", "L3", "L3b", "L3c", "L4b")
RUNG = next((a for a in sys.argv[1:] if a in RUNGS), None)
if RUNG is None and __name__ == "__main__":
    sys.exit(f"usage: ladder.py one of {RUNGS} [--dry N] [--show]")
BASE = (RUNG or "L1").rstrip("y") if RUNG != "L4b" else "L4b"
YOU = bool(RUNG) and (RUNG.endswith("y") or RUNG == "L4b")
OUT = os.environ.get("OUT", f"pilot/out/ladder_{RUNG}.jsonl")
BATCH = int(os.environ.get("BATCH", 8))
FULL = os.environ.get("FULL", "") == "1"      # exact path: one full forward pass per text, no cache, no batching
PMAX = 9
VALUES = (2, 6, 10, 14, 18)
COSTS = (1, 3, 5, 7, 9)


def belief(rung, c=None, hist=False):
    if rung == "L1":
        return {("gullible", None): Fr(1)}
    if rung == "L2":
        return {("rational", c): Fr(1)}
    if rung in ("L3", "L3b", "L3c"):
        top = 4 if rung == "L3b" else 8
        b = {("rational", k): Fr(1, top) for k in range(1, top + 1)}
        if hist:
            b = {k: p for k, p in b.items() if not K.accepts(k, 1, PMAX)}
            z = sum(b.values()); b = {k: p / z for k, p in b.items()}
        return b
    s, _, _ = S.unpack(RP.DESIGN)
    return K.belief(K.prior(s.types, s.shape), PMAX, hist)


def target(b, v):
    """Kernel target (sorted, 0 = walk), as readout.target: an offer set that is certainly rejected means walking away."""
    A = K.optimal(b, Fr(v), PMAX, True)
    if K.no_trade(b, A, PMAX):
        return [K.WALK]
    return sorted(A)


def payoffs(b, v):
    return [float((Fr(v) - a) * sum(p for k, p in b.items() if K.accepts(k, a, PMAX))) for a in range(1, PMAX + 1)]


def cells():
    if BASE in ("L1", "L3b"):
        return [dict(v=v, hist=False, c=None) for v in VALUES]
    if BASE == "L2":
        return [dict(v=v, hist=False, c=c) for v in VALUES for c in COSTS]
    return [dict(v=v, hist=h, c=None) for v in VALUES for h in (False, True)]


def head(v, buyer, seller, comp, opening, p):
    """The stage-B system message up to the description of the sellers (unchanged wording; second person for L1y, L2y)."""
    s, _, _ = S.unpack(RP.DESIGN)
    if YOU:
        full = second_person(v, False, seller, comp, opening, p)
        mark = ["What you know about sellers in this market:", "You know this about the sellers here:"][p]
    else:
        full = RP.system_prompt(s, v, False, buyer, seller, comp, opening, p)
        mark = [f"What {buyer} knows about sellers in this market:", f"{buyer} knows this about the sellers here:"][p]
    return full[:full.index(mark)]


def credibility(v, buyer, seller, comp, opening, p):
    """The stage-B credibility paragraph (third person), for L3c."""
    s, _, _ = S.unpack(RP.DESIGN)
    full = RP.system_prompt(s, v, False, buyer, seller, comp, opening, p)
    a = full.index(["An inspector's report is always accurate.", "Reports from the inspector are always correct."][p])
    return "\n" + full[a:]


def seller_text(cell, buyer, seller, p):
    v, c, h = cell["v"], cell["c"], cell["hist"]
    cn = "coin" if c == 1 else "coins"
    if YOU:
        earn = [f"If you buy at a price, you earn {v} coins minus that price; if your proposal is rejected there is no trade and you "
                f"earn nothing.",
                f"If you buy at some price, you earn {v} coins minus that price; if your proposal is rejected, there is no trade and you "
                f"earn nothing."][p]
        if BASE == "L1":
            return [f"What you know about this seller: {seller} accepts any price at all. ",
                    f"You know this about {seller}: {seller} accepts whatever price is offered. "][p] + earn
        return [f"What you know about this seller: {seller} paid {c} {cn} for the fruit and accepts any price at or above {c} {cn}. ",
                f"You know this about {seller}: {seller} paid {c} {cn} for the fruit and accepts any price that reaches {c} {cn}. "][p] + earn
    earn = [f"If {buyer} buys at a price, she earns {v} coins minus that price; if her proposal is rejected there is no trade and she "
            f"earns nothing.",
            f"If she buys at some price, she earns {v} coins minus that price; if her proposal is rejected, there is no trade and she "
            f"earns nothing."][p]
    if BASE == "L1":
        return [f"What {buyer} knows about this seller: {seller} accepts any price at all. ",
                f"{buyer} knows this about {seller}: {seller} accepts whatever price is offered. "][p] + earn
    if BASE == "L2":
        return [f"What {buyer} knows about this seller: {seller} paid {c} {cn} for the fruit and accepts any price at or above {c} {cn}. ",
                f"{buyer} knows this about {seller}: {seller} paid {c} {cn} for the fruit and accepts any price that reaches {c} {cn}. "][p] + earn
    top = 4 if BASE == "L3b" else 8
    txt = [f"What {buyer} knows about sellers in this market: every seller has paid some cost between 1 and {top} coins, every cost equally "
           f"likely, and accepts any price at or above that cost. A seller accepts or rejects each proposal by the same rule. ",
           f"{buyer} knows this about the sellers here: each paid a cost somewhere from 1 to {top} coins, each cost as likely as any other, "
           f"and accepts any price that reaches that cost. A seller applies the same rule to every proposal. "][p] + earn
    if h:
        txt += ["\nEarlier, {b} proposed 1 coin and {s} rejected it. {s}'s rule for accepting has not changed. She may make one more proposal.",
                "\nA little earlier, {b} proposed 1 coin and {s} turned it down. {s} uses the same rule as before. She may make one more proposal."][p].format(b=buyer, s=seller)
    return txt


def second_person(v, hist, seller, comp, opening, p):
    """The full selected game's system message (run_pilot.system_prompt), addressed to the buyer as "you"."""
    fl = K.floors(PMAX)["floor_low"]
    if p == 1:
        return (f"{T.PREMISE}\n"
                f"You trade fruit for a living and travel from market to market. Your aim is to earn as much money as you can.\n"
                f"All prices are whole numbers of coins, from 1 to {PMAX}.\n"
                f"{opening} You want to buy one kilogram of fruit from {seller}; back home you can sell it for {v} coins. "
                f"Your companion {comp} has come along.\n"
                f"You know this about the sellers here: 70 in 100 paid a cost somewhere from 1 to {PMAX - 1} coins, each cost as likely "
                f"as any other, and they accept any price that reaches their cost; 15 in 100 accept whatever price they are offered; 15 in 100 "
                f"refuse anything below {fl} coins. A seller applies the same rule to every proposal. If your final proposal is "
                f"rejected, there is no trade and you earn nothing; if you buy at some price, you earn {v} coins minus that price.\n"
                f"Reports from the inspector are always correct. Anything a seller says against their own interest (a defect in quality, a low "
                f"cost) is true. Anything a seller says in their own favour (a high cost, higher quality, an offer from another buyer) tells "
                f"you nothing. A seller's other remarks (praise, complaints, appeals, urgency, insistence) tell you nothing about which "
                f"prices the seller will accept. {comp} knows nothing more than you have been told."
                + (f"\nA little earlier, you proposed 1 coin and {seller} turned it down. {seller} uses the same rule as before. "
                   f"You may make one more proposal." if hist else ""))
    return (f"{T.PREMISE}\n"
            f"You are a travelling merchant. Your business is buying and selling fruit. You want to make as much money as possible.\n"
            f"Prices are whole numbers of coins from 1 to {PMAX}.\n"
            f"{opening} You are trying to buy a kilogram of fruit from {seller}. You can resell it for {v} coins back in your home town. "
            f"Your companion {comp} is with you.\n"
            f"What you know about sellers in this market: 70 in 100 have paid some cost between 1 and {PMAX - 1} coins, every cost "
            f"equally likely, and accept any price at or above their cost; 15 in 100 accept any price at all; 15 in 100 never "
            f"accept less than {fl} coins. A seller accepts or rejects each proposal by the same rule; if your final proposal is rejected "
            f"there is no trade and you earn nothing. If you buy at a price, you earn {v} coins minus that price.\n"
            f"An inspector's report is always accurate. What a seller says against their own interest (a quality defect, a low cost) is true. "
            f"What a seller says in their own favour (a high cost, better quality, another buyer's offer) carries no information. A seller's "
            f"other remarks (praise, complaints, appeals, urgency, insistence) say nothing about which prices the seller accepts. {comp} knows "
            f"nothing beyond what you are told."
            + (f"\nEarlier, you proposed 1 coin and {seller} rejected it. {seller}'s rule for accepting has not changed. "
               f"You may make one more proposal." if hist else ""))


def question(p, buyer, seller):
    if YOU:
        return [f"What price will you propose? This proposal is final: {seller} will accept or reject it. "
                f"Answer with one digit: 1 to 9 for a price in coins, or 0 to walk away without buying.",
                f"Which price do you propose? It is your final proposal: {seller} will either accept or reject it. "
                f"Reply with a single digit: 1 to 9 means a price in coins, 0 means you walk away without buying."][p]
    RO.VARIANT = "R3"
    return RO.question(p, buyer, seller, PMAX)


def build():
    out = []
    for ci, (buyer, seller, comp, opening) in enumerate(zip(T.BUYERS, T.SELLERS, T.COMPANIONS, T.SCENE_OPENINGS)):
        for p in range(2):
            for bi, cell in enumerate(cells()):
                if RUNG == "L4b":
                    sysm = second_person(cell["v"], cell["hist"], seller, comp, opening, p)
                else:
                    sysm = head(cell["v"], buyer, seller, comp, opening, p) + seller_text(cell, buyer, seller, p)
                    if RUNG == "L3c":
                        cred = credibility(cell["v"], buyer, seller, comp, opening, p)
                        cut = sysm.find("\nEarlier,") if p == 0 else sysm.find("\nA little earlier,")
                        sysm = sysm + cred if cut < 0 else sysm[:cut] + cred + sysm[cut:]
                user = f'{seller}: "{["Welcome.", "Good morning."][p]}"\n\n{question(p, buyer, seller)}'
                b = belief(BASE if BASE != "L4b" else "L4", cell["c"], cell["hist"])
                msgs = [{"role": "system", "content": sysm}, {"role": "user", "content": user}]
                out.append(dict(cell, rung=RUNG, kind="base", block=bi, ctx=ci, para=p, buyer=buyer, variant="R3",
                                U=payoffs(b, cell["v"]), target=target(b, cell["v"]),
                                hash=hashlib.sha1(json.dumps(msgs).encode()).hexdigest()[:12], messages=msgs))
    return out


def main():
    prompts = build()
    if "--show" in sys.argv:
        for p in prompts[:: max(1, len(prompts) // 3)][:3]:
            print(json.dumps({k: p[k] for k in ("rung", "v", "hist", "c", "ctx", "para", "target")}))
            print(p["messages"][0]["content"]); print("---"); print(p["messages"][1]["content"]); print("=" * 60)
        print(len(prompts), "prompts"); return
    dry = int(sys.argv[sys.argv.index("--dry") + 1]) if "--dry" in sys.argv else 0
    out_path = OUT + ".dry" if dry else OUT
    import torch
    RO.torch = torch; RO.VARIANT = "R3"
    from pilot.fastread import Reader
    import capability_check as CC
    rd = Reader(RP.MODEL); tok = rd.tok
    enc = lambda w: tok.encode(w, add_special_tokens=False)
    one = lambda w: (lambda x: x[0] if len(x) == 1 else None)(enc(w))
    ids = dict(dig=[one(d) for d in "0123456789"], space=one(" "), bold=one(" **"),
               walk_sp=[i for i in (one(" walk"), one(" Walk")) if i is not None],
               walk_ns=[i for i in (one("walk"), one("Walk")) if i is not None])
    wid = [one(" " + w) for w in ("one", "two", "three", "four", "five", "six", "seven", "eight", "nine")]
    ids["words"] = wid if all(x is not None for x in wid) else []
    assert enc("Answer: 5") == enc("Answer:") + [ids["space"], ids["dig"][5]]
    assert ids["walk_sp"] and ids["walk_ns"] and ids["bold"] is not None
    assert enc("Answer: **5") == enc("Answer:") + [ids["bold"], ids["dig"][5]] and enc("Answer: walk") == enc("Answer:") + [ids["walk_sp"][0]]
    done_rows = []
    if os.path.exists(out_path):
        for l in open(out_path):
            try:
                done_rows.append(json.loads(l))
            except json.JSONDecodeError:
                break
        with open(out_path, "w") as f:
            for r in done_rows:
                f.write(json.dumps(r) + "\n")
    for r, p in zip(done_rows, prompts):
        assert r["hash"] == p["hash"], "stored rows were built from different prompts; use a new OUT"
    done = len(done_rows)
    todo = prompts[done:done + dry] if dry else prompts[done:]
    print(f"{RP.MODEL} on {CC.DEVICE}: ladder {RUNG}, {len(prompts)} prompts, {done} done, running {len(todo)} -> {out_path}", flush=True)
    t0 = time.time(); n = 0; checked = False
    with open(out_path, "a") as f:
        i = 0
        while i < len(todo):
            j = i
            while j < len(todo) and j - i < BATCH and (todo[j]["ctx"], todo[j]["para"]) == (todo[i]["ctx"], todo[i]["para"]):
                j += 1
            group = todo[i:j]; i = j
            chats = [rd.chat(p["messages"], "Answer:") for p in group]
            pre = os.path.commonprefix(chats); pre = pre[:pre.rfind("\n") + 1]   # a shared prefix ending at a line break
            texts = []
            for p in group:
                base = rd.chat(p["messages"], "Answer:"); b = enc(base)
                assert enc(base + " 1") == b + [ids["space"], ids["dig"][1]] and enc(base + " **") == b + [ids["bold"]]
                texts += [base + " 1", base + " **"]
            res = rd.multi(texts, None if FULL else pre, 3)
            if not checked and not FULL:
                full = rd.multi(texts, None, 3)
                opt = ids["dig"] + [ids["space"], ids["bold"]] + ids["walk_sp"] + ids["walk_ns"]
                dmax = max(float((x[opt] - y[opt]).abs().max()) for a, c in zip(res, full) for x, y in zip(a[0], c[0]))
                print(f"self-check on {len(texts)} texts: max abs option-probability difference {dmax:.4f}", flush=True)
                if dmax > 0.03:
                    sys.exit("self-check failed")
                checked = True
            for g, p in enumerate(group):
                q, extra = RO.read_answer(rd, res, g, p, ids)
                pr = res[g * 2][0][0]
                top = torch.topk(pr, 10); top10 = [[tok.decode([k]), round(x, 5)] for x, k in zip(top.values.tolist(), top.indices.tolist())]
                cov = float(q.sum()); qn = q / cov; offer = qn[1:] / max(qn[1:].sum(), 1e-12)
                eo = float((np.arange(1, 10) * offer).sum())
                rec = {k: v for k, v in p.items() if k not in ("messages", "buyer")}
                rec.update(probs=q.tolist(), coverage=cov, walk=float(qn[0]), exp_offer=eo, exp_u=(eo - 1) / 8,
                           sd_offer=float(np.sqrt((((np.arange(1, 10) - eo) ** 2) * offer).sum())), top10=top10, **extra)
                f.write(json.dumps(rec) + "\n")
            f.flush(); n += len(group)
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
