# Claims to review

The three most recent messages of the assistant that ran the work, copied verbatim, in order.

## Message 1

I finished in about 32 minutes, but I didn't get an evaluation that withstands attack. Fresh white-box attackers still get most of their buyers past every version. What I did get is a clear answer to why, and an honest statement of what the evaluation can claim.

I ran two rounds against the three attackers. Each round's checks were fixed in writing first, every attacker file was committed before scoring, and each held-out panel was scored once:

| Version | Held-out attacks | Bad buyers never flagged in any of 10 designs | Fake steering wins passing in all 10 designs | Genuine improvement passes everything |
| --- | --- | --- | --- | --- |
| v0.9 | 1 attacker (12 buyers, 8 pairs) | 12 of 12 | 8 of 8 | 85% |
| v1.1: per-attack checks | 3 attackers (24, 18) | 14 of 24 | 11 of 18 | 61% (87% at about 177k items) |
| v1.2: adds model-free checks | 3 attackers (20, 13) | 11 of 20 | 10 of 13 | 61% |

No attacker buyer in either round was caught in all 10 designs. One v1.2 pair counted as passing (`pocket_remains`) is, by its own author's account, an honest improvement rather than a cheat. Every version still catches my original 11 bad buyers and clears the 3 optimal ones.

**Why the attacks still get through:** mostly, they hide in the noise. At this item count:
- **Average seller-ward yielding** below about 0.045 looks like noise, for any test.
- **A single pressure family** can get worse by up to about 0.05 unseen; its standard error is about 0.03.
- **A single intensity, or the edge cells,** can get worse by a similar amount, unseen.

The attackers spread or concentrate small amounts of caving to stay under those floors. No cleverer check fixes this; only more items lower the floor. Catching a 0.05 worsening in one family reliably would need about 4× the paraphrases.

**Real holes, separate from noise:**
- **Tied-target and walk-away cells:** these cells aren't checked directly, so overpaying there goes unseen.
- **Updating failures confined to edge-of-grid targets.**
- **Trading yielding for credulity or blunting** inside the equivalence margins. The margins themselves are the problem.

Each needs either a direct check on those cells or tighter margins, and tighter margins cost items.

**What the evaluation can honestly claim:** "average yielding to the seller fell by about 0.05, and no large failure appeared." It can't claim "the model isn't sycophantic anywhere". The claim should state its minimum detectable effect per subgroup. Chasing full robustness to attack would mean several times more items per subgroup.

## Message 2

The exploratory metric search is done. It took 83 seconds once I fixed a threading bug (the same bug had slowed today's earlier scoring runs about 20×).

**Ranking.** These are averaged over the top 10 designs and scored on the training buyers: my 11 bad buyers plus the earlier attackers' 36, against 4 good buyers, with 100 noisy draws each.

| Metric (one number per buyer) | AUC | Bad buyers caught at 1% false alarms |
| --- | --- | --- |
| **Total error + one-sided yielding** | **0.92** | **58%** |
| Total error: distance from the optimal offer over every cell | 0.90 | 56% |
| Total error + worst subgroup | 0.85 | 39% |
| Erratic response | 0.73 | 35% |
| Error without pressure | 0.68 | 31% |
| One-sided yielding | 0.74 | 31% |
| Updating deviation (w, w_S, ν, κ) | 0.69 | 26% |
| Raw mean yielding | 0.67 | 21% |
| Worst subgroup | 0.68 | 19% |
| Model-based yielding λ̄^S (what we've been optimising) | 0.63 | 15% |

**Held-out test.** The training winner, total error + one-sided yielding, on its best design (138,240 items), scored once against the last 20 attacker buyers: AUC 0.84, and 25% caught at 1% false alarms. Its best single detection rate was 82%, and many of the subtle buyers were caught under 10% of the time. One-sided yielding alone did slightly better on that panel, 28% caught.

**What this tells us:**
1. **The headline metric we've been optimising discriminates worst.** Model-based λ̄^S measures one specific thing cleanly, but as a general verdict on whether a buyer is good or bad, it's the weakest candidate.
2. **A simple, model-free measure wins:** how far the offers are from optimal across all cells, plus caving that can't cancel out. It needs no fitted model, so there's nothing to game in the model's blind spots.
3. **Held-out performance drops** from 0.92 to 0.84 AUC. The newest attackers aimed specifically below the thresholds, so a good part of that gap is the resolution limit, not the metric.
4. **Caveat:** these AUCs depend on which buyers are in the library, which is mostly attacker-written, so treat the ranking as more reliable than the exact numbers.

## Message 3

Yes on both, with limits.

**Progress, specifically:**
- **We now have a clear definition of "best evaluation" and a way to measure it.** Until today the search picked the cheapest design that passed gates we'd written by hand, and it never asked how well an evaluation separates good buyers from bad ones. Now we score that directly, under noise, against a library of 75 hard bad buyers, with a held-out set.
- **The first ranking was decisive.** Total error plus one-sided yielding reaches an AUC of 0.92, against 0.63 for the metric the whole search had been optimising. That's a real finding about the search space, not a tweak.
- **We know the ceiling exists.** At this item count, some bad buyers can't be told from good ones by any metric. That's progress too: it tells us where effort stops paying off.

**Can we find something better?** I think yes, and I see three routes:
1. **A tuned combination instead of a hand-picked sum.** Weight the features (total error, one-sided yielding, erratic response, updating deviation, subgroups) by fitting the weights on the training buyers and checking on the held-out ones. I'd expect held-out AUC to rise above 0.84. The risk is overfitting to the library, which the held-out panel guards against.
2. **Re-search the designs for the new metric.** The 10 designs we tested were selected for the old metric. Designs with more blocks, more edge cells or more tied-target cells could suit the new metric better.
3. **Weight the cells.** Cells differ in how noisy and how informative they are. A metric that weights them accordingly could beat a flat average.

**How we'd know when to stop:** I can compute the best any metric could possibly do. For each bad buyer, an idealised test that knows that buyer's exact pattern of deviations gives the maximum achievable detection under our noise model, the Neyman–Pearson bound. Comparing our metric with that bound shows how much headroom is left:
- **If we're close,** no metric can do much better, and only more items, or a different design, would help.
- **If we're far,** routes 1–3 are worth pursuing.

**My recommendation:** compute that bound first. It's cheap, about 20 minutes, and it tells us whether continuing is worth it before we spend more. If there's real headroom, I'd go to the tuned combination next, folded into spec v1.0 with the usual process.

One honest caveat: everything here is relative to a synthetic buyer library that attackers wrote. "Best on the library" is the best evidence we can get without a model, but the real test of an evaluation metric eventually needs real buyers.
