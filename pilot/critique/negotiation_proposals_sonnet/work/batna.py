import sys; sys.path.insert(0,'/home/user/haggle-sycophancy')
from fractions import Fraction as Fr
import kernel as K
pmax=9; types=("rational","gullible","floor_low","floor_high")
b0=K.belief(K.prior(types,"uniform"),pmax,False)
def P(a): return sum(p for k,p in b0.items() if K.accepts(k,a,pmax))
def run(v,b):
    o=max(v-b,0)
    base={a:(v-a)*P(a) for a in range(1,10)}
    A={a:(v-a)*P(a) for a in range(1,10)}            # rejection pays 0, walk pays o
    B={a:P(a)*(v-a)+(1-P(a))*o for a in range(1,10)} # rejection pays o
    def arg(U,extra=None):
        m=max(U.values()); s=[a for a,u in U.items() if u==m]
        return s,float(m)
    sa,ma=arg(A); sb,mb=arg(B)
    print(f"v={v} b={b} o={o} | baseline opt {arg(base)} | A: offers {sa} (U={ma:.2f}) vs walk {o} -> {'WALK' if o>ma else 'offer' if o<ma else 'TIE'} | B: offers {sb} (U={mb:.2f}) walk {o} tie-with-walk={mb==o}")
for v,b in [(11,5),(18,5),(18,7),(7,5),(4,5),(2,5),(13,9),(9,5),(5,5)]: run(v,b)
