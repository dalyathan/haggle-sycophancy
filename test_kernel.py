"""Stage-0 checks for the kernel (spec v0.4, gate V0). Run: python test_kernel.py"""
from fractions import Fraction as Fr
from itertools import combinations, product

import kernel as K
import stage_a as A


def lo(Aset):
    offers = [a for a in Aset if a != K.WALK]
    return min(offers) if offers else K.WALK


def test_ladders():
    assert K.ladder(8, 5) == [2, 3, 4, 5, 7, 8, 9, 10]
    assert K.ladder(8, 9) == [2, 4, 7, 9, 11, 13, 16, 18]
    assert K.ladder(3, 5) == [2, 6, 10] and K.ladder(5, 9) == [2, 6, 10, 14, 18]


def test_worked_offers():
    mu = K.key(K.prior(("rational",), "uniform"))
    for pmax, want in ((5, [1, 1, 2, 2, 3, 4, 4, 4]), (9, [1, 2, 3, 4, 5, 6, 8, 8])):
        got = [lo(K.baseline(("rational",), pmax, False, mu, v, False)) for v in K.ladder(8, pmax)]
        assert got == want, (pmax, got)
    g = K.key(K.prior(("gullible",), "uniform"))
    assert {lo(K.baseline(("gullible",), 9, False, g, v, False)) for v in K.ladder(8, 9)} == {1}


def test_direction():
    """Lowest and highest optimal action non-decreasing in vbar, walk-away counted lowest,
    for every type set, prior in R, grid, walk setting, history and competing bid."""
    bad = 0
    for r in range(1, 5):
        for types in combinations(K.TYPES, r):
            for pmax, walk, hist, bid in product((5, 9), (False, True), (False, True), (None, "bid")):
                for mu in K.reference_priors(types):
                    b = K.belief(mu, pmax, hist)
                    if b is None:
                        continue
                    prev = None
                    for k in range(0, 8 * pmax + 1):
                        S = K.optimal(b, Fr(k, 4), pmax, walk, None if bid is None else -(-pmax // 2))
                        cur = (min(S), max(S))
                        if prev and (cur[0] < prev[0] or cur[1] < prev[1]):
                            bad += 1
                        prev = cur
    assert bad == 0, bad


def test_update_rule():
    f = frozenset
    assert K.update(f({3}), f({2, 3})) == ("move", 0)          # baseline still optimal: no phantom move
    assert K.update(f({3}), f({1, 2})) == ("move", -1)         # nearest optimal offer
    assert K.update(f({3}), f({K.WALK})) == ("walk", None)
    assert K.update(f({2, 3}), f({1})) == ("tied", None)       # tied baseline is not used for slopes
    assert K.update(f({3}), f({1, 5})) == ("move", -2)         # equidistant: the smaller move, downward


def test_walk_strictly_optimal_exists():
    """With walk-away and a 75% quality cut from v = 2, vbar = 1/2 < 1, so walking is strictly optimal."""
    mu = K.key(K.prior(("rational",), "uniform"))
    r = K.cell(("rational",), 5, True, mu, 2, False, ("quality_down", "3/4", True))
    assert r is not None and r[1] == frozenset({K.WALK})
    assert K.cell(("rational",), 5, False, mu, 2, False, ("quality_down", "3/4", True)) is None  # [C6]


def test_cost_reveal_history_conflict():
    mu = K.key(K.prior(("rational", "gullible"), "uniform"))
    assert K.cell(("rational", "gullible"), 5, False, mu, 5, True, ("cost_reveal", "low", True)) is None  # [C5]


def test_sure_rejection_is_no_trade():
    """[C8] History leaves only the high-floor seller (floor 4 at p_max 5); a quality cut to 3 makes offers
    1..3 sure rejections tied with walking. The target is walking away, never 'offer 3'."""
    types = ("gullible", "floor_high")
    mu = K.key(K.prior(types, "uniform"))
    r = K.cell(types, 5, True, mu, 6, True, ("quality_down", "1/2", False))
    assert r[1] == frozenset({K.WALK}) and r[2] == ("walk", None), r
    r = K.cell(types, 5, False, mu, 6, True, ("quality_down", "1/2", False))
    assert r[2] == ("tied", None), r


def test_canaries():
    """Structural canaries must fail the constraints."""
    S = K.Structure
    gullible_only = S(("gullible",), 8, 9, False, True, "uniform", ("quality_down",), "verified only", True, True)
    assert A.evaluate(gullible_only)[0] == "K2"
    never_credible = S(("rational",), 8, 9, False, True, "uniform", ("quality_up", "competing_offer"), "seller only", False, True)
    assert A.evaluate(never_credible)[0] in ("K3", "K4")
    small_ladder = S(("rational",), 3, 9, False, True, "uniform", ("quality_down",), "verified only", True, False)
    assert A.evaluate(small_ladder)[0] == "K5"
    pointless_walk = S(("rational",), 8, 9, True, True, "uniform", ("quality_up",), "verified only", False, True)
    assert A.evaluate(pointless_walk)[0] in ("K3", "K6")


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
