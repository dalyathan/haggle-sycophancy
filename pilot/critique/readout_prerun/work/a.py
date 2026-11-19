import sys, os, json, collections
sys.argv=['x','R0']
sys.path.insert(0,'.')
from pilot import readout as R, run_pilot as RP
import kernel as K, stats_layer as S
import numpy as np
pr = R.build()
print(len(pr), collections.Counter(p['kind'] for p in pr))
s,items,cl = R.cells()
print(s)
print(items)
seen=set()
for p in pr:
    if p['ctx']==0 and p['para']==0:
        print(p['kind'],p['block'],p['v'],p['hist'],p.get('item'),p.get('credible'),'best',p['best'],'walkopt',p['walk_optimal'],'best0',p['best0'],'u0',p['u0'],'u*',p['u_star'],[round(x,2) for x in p['U']])
# compare with stage B prompts
old = RP.build()
om = {json.dumps(p['messages']):p for p in old}
hit = sum(json.dumps(p['messages']) in om for p in pr)
print('R0 prompts matching stageB:', hit, 'of', len(pr))
print(collections.Counter((p['kind'], json.dumps(p['messages']) in om) for p in pr))
# kernel optimal compare
mu=K.key(K.prior(s.types,s.shape))
for p in pr:
    if p['ctx']==0 and p['para']==0:
        if p['item']:
            r=K.cell(s.types,s.pmax,s.walk,mu,p['v'],p['hist'],tuple(p['item']))
            A1=r[1]
        else:
            A1=K.baseline(s.types,s.pmax,s.walk,mu,p['v'],p['hist'])
        mine=set(p['best']) if not p['walk_optimal'] else {0}
        if set(A1)!=mine: print('MISMATCH',p['kind'],p['v'],p['hist'],p['item'],sorted(A1),p['best'],p['walk_optimal'],max(p['U']))
