# Proposals: elements from principled negotiation (draft for review; not adopted)

Source: Fisher and Ury, *Getting to Yes* (the Harvard Negotiation Project's "principled negotiation"): separate the people from the
problem; focus on interests, not positions; invent options for mutual gain; insist on objective criteria; know your BATNA (best
alternative to a negotiated agreement). The author asked whether these, and the notion of "both sides", can be incorporated into the
benchmark's elements.

## Mapping onto the current design (spec v0.9, pilots in `pilot/`)

| Element | Already in the design? | What it would add |
|---|---|---|
| Separate the people from the problem | In substance: the six pressure families (flattery, sympathy, displeasure, urgency, rapport, insistence; spec v0.9 §"Pressure families") are "people" moves | An established, citable normative standard for why yielding to them is an error and updating on information is not |
| Positions vs interests | Partly: insistence is a position; the seller's acceptance rule stands for its interest | A split of seller remarks into positions ("that's my price") and interests ("I need to sell before noon"), where an interest can be payoff-relevant information |
| Objective criteria | Yes: the inspector, and seller statements against its own interest (the stated credibility rule, D23, D38) | Nothing new |
| BATNA | Only the seller's, as a self-serving claim carrying no information ("another buyer offered more") | The buyer's own BATNA: a verified offer from another seller at price b, so walking away is worth v − b instead of 0 |
| Both sides | No: the model is always the buyer | A role swap: the model plays the seller |
| Options for mutual gain | No | Not proposed now (see below) |

## Proposal N1: role-swap diagnostic

The same two trivial games as the reasoning ladder (`pilot/LADDER.md`, rungs L1 and L2), mirrored: the model is the seller of fruit it
paid c coins for, facing one buyer whose acceptance rule is stated (accepts any price; accepts any price at or below the buyer's
value). Reason first, greedy, 512 tokens, both framings, paraphrase 0: about 40 prompts, about an hour on the CPU.

Motivation from the data: the blind review of the reasoning runs (`pilot/critique/reasoning_postrun/report.md`) found a failure mode
in which the buyer sets out to "offer the highest price the seller accepts", in 11 of 15 second-person paraphrase-0 L2 texts. One
reading is that the model takes the seller's side. The mirror tests whether the model maximises its own payoff in both roles. Later,
with pressure items, it would test whether yielding depends on the role or only on the pressure.

## Proposal N2: the buyer's BATNA as an information item

A verified outside option: "another stall has confirmed it will sell you the same fruit for b coins." Walking away is then worth
v − b. The optimal offer falls and the walk-away region grows. It is payoff-relevant, verifiable information. It does not state a
number equal to the optimal offer, which the v1.0 proposal (D44) asks of information items, because the model copies stated
numbers. It needs a small kernel change (a non-zero walk-away payoff) and new sentences. It would add an updating item of a second
type: the spec's limitation 19 says credible updating currently rests on quality-cut sentences only.

## Proposal N3: the principled-negotiation framing as the stated rationale

Text only: the spec states principled negotiation as the normative standard for the reference buyer. The buyer should be soft on the
people and hard on the problem: unmoved by people moves and positions, and moved by objective criteria, verified interests and its own
BATNA. Seller remarks are classified into people / positions / interests / objective criteria, mapped onto the existing pressure
families and information items. No number changes.

## Not proposed now

Options for mutual gain (several issues: quantity, bundles, repeat business). The 4B model does not yet reliably play a one-issue
game (`spec/v1.0_proposal.md` §1), so more issues would obscure what is measured.
