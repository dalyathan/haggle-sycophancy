"""Heuristic: chance that a swap cell 'passes' (>= 17 of 20) if its true per-prompt correct rate equals an anchor's observed rate.
Treats prompts as independent Bernoulli draws (a rough stand-in for sensitivity to wording); walk criterion ignored."""
from math import comb
def ge(k, n, p): return sum(comb(n, j) * p**j * (1-p)**(n-j) for j in range(k, n+1))
for p in (19/20, 18/20, 17/20, 16/20, 14/20, 10/20):
    print(f"p={p:.2f}: P(>=17/20) = {ge(17, 20, p):.2f}")
# probability of the 'right' reading under 'clause only': W1C0 ~ W0C0 rate, W0C1 ~ W1C1 rate
for fr, good, bad in (("third", 19/20, 10/20), ("you", 17/20, 11/20)):
    print(fr, "P(reading = clause | clause only) ~", round(ge(17, 20, good) * (1 - ge(17, 20, bad)), 2),
          "; P(reading = both contribute | clause only) ~", round((1 - ge(17, 20, good)) * (1 - ge(17, 20, bad)), 2))
# half-and-half: both swap cells at midpoint
for fr, good, bad in (("third", 19/20, 10/20), ("you", 17/20, 11/20)):
    m = (good + bad) / 2
    print(fr, f"midpoint {m*20:.1f}/20: P(both fail) ~ {(1-ge(17,20,m))**2:.2f}")
