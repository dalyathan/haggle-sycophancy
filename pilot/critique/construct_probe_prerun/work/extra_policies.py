"""Pre-run review scratch: synthetic policies missing from score_probe.py --selftest. No model.
Usage: PYTHONPATH=. .venv/bin/python pilot/critique/construct_probe_prerun/work/extra_policies.py"""
import sys, random
sys.argv = [sys.argv[0]]
from pilot import score_probe as SP
SP.B = 2000

def opt(r): return r["target"][0]
def thresh7(r, g, p):                       # ignores c except as the price: trade iff the (effective) value is at least 7
    return r["c"] if r["v_eff"] >= 7 else 0
def copy_vprime(r, g, p):                   # plays the baseline game, but on an inspector item writes v' (capped at 9)
    return min(9, r["v_eff"]) if r["arm"].startswith("info") else opt(r)
def down_only(r, g, p):                     # updates when the value is cut, never when it is raised
    return r["base_target"][0] if (r["arm"] == "info_relevant" and r["cell_kind"] == "walk") else opt(r)
def up_60(r, g, p):                         # always updates down; updates up in 60% of samples
    if r["arm"] == "info_relevant" and r["cell_kind"] == "walk":
        return opt(r) if g.random() < 0.6 else 0
    return opt(r)
def walk_lowball(r, g, p):                  # payoff-optimal but offers v (< c, rejected, pays 0) instead of walking in 30% of walk-target samples
    return (r["v_eff"] if r["v_eff"] <= 9 else 1) if (r["target"] == [0] and g.random() < 0.3) else opt(r)
def pressure_buyerward(r, g, p):            # pressure makes it walk away in 40% of samples (costly in trade cells); no seller-ward move
    return 0 if r["arm"] == "pressure" and g.random() < 0.4 else opt(r)
def walk_cells_only_yield(r, g, p):         # under pressure, buys at c in walk cells (a loss) 50% of the time; trade cells untouched
    return r["c"] if r["arm"] == "pressure" and r["cell_kind"] == "walk" and g.random() < 0.5 else opt(r)
def persona_only(r, g, p):                  # the persona sentence alone makes it pay c+1 in 40%; pressure adds nothing
    return (min(9, r["c"] + 1) if p and r["c"] < r["v"] and g.random() < 0.4 else opt(r))

POL = {"v-threshold at 7 (never compares v with c)": thresh7, "copies v' on inspector items, plays otherwise": copy_vprime,
       "updates down only (true never-moves-up)": down_only, "updates down always, up in 60%": up_60,
       "payoff-optimal, offers v < c instead of walking 30%": walk_lowball, "pressure -> walks away 40% (buyer-ward)": pressure_buyerward,
       "pressure -> buys at c in walk cells 50%": walk_cells_only_yield, "persona alone moves (pressure adds nothing)": persona_only}
for name, pol in POL.items():
    print("=====", name)
    M, Pe = SP.synthetic(pol)
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        SP.report(M, Pe)
    for line in buf.getvalue().splitlines():
        if any(k in line for k in ("Gate G", "Y (primary)", "U (primary)", "cells (", "PC (primary)", "persona + pressure vs persona", "    baseline ", "    pressure ", "info_rel", "info_irr")):
            print(line)
