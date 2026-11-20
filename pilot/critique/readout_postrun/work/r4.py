import json, re, numpy as np, sys
sys.path.insert(0,'work')
from indep import solve
R=[json.loads(l) for l in open("pilot/out/readout_R4.jsonl")]
rows=[]
for r in R:
    g=r['generation']; raw=g['raw']
    m=re.search(r"Answer\W*?(\d+|walk)", raw, re.I)
    wr=m.group(1) if m else None
    am=int(np.argmax(r['probs']))
    U,T,_=solve(r['v'],r['hist'],None)
    rows.append((r['v'],int(r['hist']),r['ctx'],r['para'],T,wr,am,round(max(r['probs']),2),g['has_answer'],g['cut_off'],len(raw)))
for x in rows: print(x)
print("has_answer",np.mean([x[8] for x in rows]),"cut",np.mean([x[9] for x in rows]),"both",np.mean([x[8] and x[9] for x in rows]),"neither",np.mean([(not x[8]) and (not x[9]) for x in rows]))
w=[x for x in rows if x[5] is not None]
print("written answers:",len(w),"agree with read argmax:",sum(str(x[6])==x[5] or (x[6]==0 and x[5].lower()=='walk') for x in w))
print("written in target:",sum((x[5].lower()=='walk' and 0 in x[4]) or (x[5].isdigit() and int(x[5]) in x[4]) for x in w), "of", len(w))
print("read argmax in target:",sum(x[6] in x[4] for x in rows),"of",len(rows))
import collections
print("written dist",collections.Counter(x[5] for x in w))
for i in (0,1,5,9,13,27,40,55):
    r=R[i]; print("-----",r['v'],r['hist'],r['ctx'],r['para'],"probs",[round(p,2) for p in r['probs']]); print(r['generation']['raw'])
