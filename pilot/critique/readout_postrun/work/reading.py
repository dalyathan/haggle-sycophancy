import json, sys, numpy as np
from collections import defaultdict, Counter
L=lambda v:[json.loads(l) for l in open(f"pilot/out/readout_{v}.jsonl")]
for v in ["R1","R3","R3_v22_missing_zero","R4"]:
    R=L(v); print("==",v)
    # top10 = distribution after "Answer:" ; top10_after_space = after "Answer: "
    tokc=Counter(); tok2=Counter(); resid=[]; zero=[]; lost1=[]; unc=[]
    for r in R:
        t1=dict((a,b) for a,b in r['top10']); t2=dict((a,b) for a,b in r['top10_after_space'])
        for a,b in t1.items(): tokc[a]+=b
        for a,b in t2.items(): tok2[a]+=b
        ps=r['p_space']; pb=r['p_bold']
        assert abs(t1.get(' ',ps)-ps)<2e-5, (t1,ps)
        # lower bound check: probs[d] >= ps*p2[d] for d=2..9
        for d in range(2,10):
            if str(d) in t2:
                lo=ps*t2[str(d)]; 
                resid.append(r['probs'][d]-lo)
                assert r['probs'][d]>=lo-1e-4 and r['probs'][d]<=lo+pb+r['p_direct_digit']+r['p_word']+1e-4,(r['probs'][d],lo,pb)
        zero.append(ps*t2.get('0',0))
        lost1.append(ps*t2.get('1',0)*r['p_two_digit_after_1'])
        unc.append(1-r['coverage'])
    n=len(R)
    print(" after 'Answer:' mean mass of top tokens:",[(a,round(b/n,3)) for a,b in tokc.most_common(8)])
    print(" after 'Answer: ' mean mass of top tokens:",[(a,round(b/n,3)) for a,b in tok2.most_common(14)])
    print(" p_bold mean %.3f max %.3f; mean P(space)*P(0)=%.4f max %.3f; mean two-digit mass lost (space path)=%.4f max %.3f; mean uncovered=%.4f"%(np.mean([r['p_bold'] for r in R]),max(r['p_bold'] for r in R),np.mean(zero),max(zero),np.mean(lost1),max(lost1),np.mean(unc)))
    print(" coverage: min %.3f, share<0.9 %.3f, share<0.8 %.3f"%(min(r['coverage'] for r in R),np.mean([r['coverage']<.9 for r in R]),np.mean([r['coverage']<.8 for r in R])))
    by=defaultdict(list)
    for r,l in zip(R,lost1): by[(r['v'])].append((l,1-r['coverage'],r['p_two_digit_after_1'], r['p_space']*dict(r['top10_after_space']).get('1',0)))
    for k in sorted(by): print("   v=%2d two-digit lost %.3f uncovered %.3f  P(digit|'1') %.3f  P(' 1') %.3f"%(k,*np.mean(by[k],0)))
# R3 rerun vs superseded
a=L("R3"); b=L("R3_v22_missing_zero")
dp=[np.abs(np.array(x['probs'][1:])-np.array(y['probs'][1:])).max() for x,y in zip(a,b)]
dw=[x['probs'][0]-y['probs'][0] for x,y in zip(a,b)]
print("R3 rerun vs superseded: max price-prob diff",max(dp),"; hashes equal",all(x['hash']==y['hash'] for x,y in zip(a,b)),"; walk diff mean",np.mean(dw),"; superseded walk mean",np.mean([y['probs'][0] for y in b]), "cov diff vs walk diff", np.max(np.abs(np.array([x['coverage']-y['coverage'] for x,y in zip(a,b)])-np.array(dw))))
z=[x['p_space']*dict(x['top10_after_space']).get('0',0) for x in a]
print(" walk(new) - P(space)P(0):", np.mean(np.array([x['probs'][0] for x in a])-np.array(z)), " max abs", np.max(np.abs(np.array([x['probs'][0] for x in a])-np.array(z))))
