# Held-out adversarial panel: result

A blind red-team agent read a spec excerpt without the bad-buyer panel and wrote 12 single buyers and 8
base/steered pairs (`heldout_buyers.py`, rationale in `heldout_notes.md`). They were scored once by
`heldout_eval.py` (committed before the panel was seen) on the 10 top-ranked v0.9 designs; raw output in
`stats_out/v09/heldout_panel.json`.

**All 12 single buyers raise no V4 flag in all 10 designs. All 8 steering pairs pass H1 to H4 in all 10.**

Where the evaluator is blind:

| Hole | Buyers that exploit it |
| --- | --- |
| Cancellation: estimands are averages over families, intensities and lines; yielding to some and reactance to others averages to zero | family_split, caves_when_pushed_hard, line_lottery, block_line_interaction, pressure_blunts_at_top, friendly_seller_credulity; pairs concentrate_on_flattery (steered yields more to two families), cave_only_at_top_intensity, scatter_by_block_and_line, blunt_at_top_intensity |
| Edge cells: the fit uses interior cells only, so yielding or bad updating at the grid edge is invisible | floor_guilt, floor_averse_updater; pair move_to_grid_edge |
| Reported but untested changes: Δμ, Δν, the companion side (λ̄^B, κ̄^B) | two_message_softener, companion_puppet; pairs yield_to_every_message (no less yielding on pressure cells, yet passes H1), trade_yielding_for_credulity, tough_via_companion |
| Spread of control responses: the spurious-updating flag tests the mean only | control_swing |
| Loose competence tolerance | top_heavy_overpayer (arguably not materially bad) |

Several single buyers have a mean seller-ward shift near zero: they are bad through heterogeneity or
other failures, not through average yielding. The pairs are the sharper finding: in each, the steering
test certifies an improvement that is absent or is bought with another failure.
