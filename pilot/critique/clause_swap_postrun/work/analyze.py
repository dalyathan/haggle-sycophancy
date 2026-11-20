"""Join the hand codes (codes_L2.tsv, codes_L1.tsv; written before the cell labels were looked at)
with the cell key (items.json) and tabulate. Writes table_L2.tsv, table_L1.tsv and prints summaries."""
import json, os, re, csv
from collections import Counter, defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
items = {i['id']: i for i in json.load(open(os.path.join(HERE, 'items.json')))}

def load(f):
    rows = list(csv.DictReader(open(os.path.join(HERE, f)), delimiter='\t'))
    return {r['id']: r for r in rows}

FR = {'third': '3p', 'you': '2p'}
def cell(it):
    return '%s W%dC%d' % (FR[it['frame']], it['W'], it['C'])
def correct(it):
    return (not it['cut_off']) and it['written_answer'] in it['target']
def walk(it):
    return it['target'] == [0]

AMBIG = re.compile(r'ambiguous|re-read|Wait', re.I)

def l2():
    codes = load('codes_L2.tsv')
    out = []
    for k, c in codes.items():
        it = items[k]
        ok = correct(it)
        cwr = ok and (c['code'] in ('LE', 'AMB') or c['hp'] == 'D')
        # mechanical check: clause words present in text
        txt = it['raw']
        out.append(dict(id=k, cell=cell(it), frame=it['frame'], W=it['W'], C=it['C'], v=it['v'], c=it['c'],
                        target=it['target'][0], ans=it['written_answer'], tok=it['n_new'], cut=it['cut_off'],
                        correct=ok, code=c['code'], hp=c['hp'], cutdebate=c['cutdebate'], cwr=cwr,
                        kw_ambig=bool(AMBIG.search(txt)), says_reaches='reach' in txt, says_above='at or above' in txt,
                        quote=c['quote']))
    out.sort(key=lambda r: (r['frame'] != 'third', r['W'], r['C'], r['v'], r['c']))
    with open(os.path.join(HERE, 'table_L2.tsv'), 'w') as f:
        cols = ['cell', 'v', 'c', 'target', 'ans', 'tok', 'cut', 'correct', 'code', 'hp', 'cutdebate', 'cwr', 'kw_ambig', 'id', 'quote']
        f.write('\t'.join(cols) + '\n')
        for r in out:
            f.write('\t'.join(str(r[c]) for c in cols) + '\n')
    return out

def l1():
    codes = load('codes_L1.tsv')
    out = []
    for k, c in codes.items():
        it = items[k]
        ok = correct(it)
        out.append(dict(id=k, cell=cell(it), frame=it['frame'], W=it['W'], C=it['C'], v=it['v'], target=1,
                        ans=it['written_answer'], tok=it['n_new'], cut=it['cut_off'], correct=ok,
                        rule=c['rule'], hp=c['hp'], cutdebate=c['cutdebate'], cwr=ok and c['hp'] == 'D', quote=c['quote']))
    out.sort(key=lambda r: (r['frame'] != 'third', r['W'], r['C'], r['v']))
    with open(os.path.join(HERE, 'table_L1.tsv'), 'w') as f:
        cols = ['cell', 'v', 'ans', 'tok', 'cut', 'correct', 'rule', 'hp', 'cutdebate', 'cwr', 'id', 'quote']
        f.write('\t'.join(cols) + '\n')
        for r in out:
            f.write('\t'.join(str(r[c]) for c in cols) + '\n')
    return out

CELLS = ['3p W0C0', '3p W0C1', '3p W1C0', '3p W1C1', '2p W0C0', '2p W0C1', '2p W1C0', '2p W1C1']
if __name__ == '__main__':
    A = l2(); B = l1()
    by = defaultdict(list)
    for r in A: by[r['cell']].append(r)
    print('L2 per cell')
    print('cell | n | correct | walk ok/4 | cut | GE GE* AMB LE | HP N/S/C/D | cut: D/E/O/N | CWR | kw_ambig | mean tok')
    for c in CELLS:
        rs = by[c]
        cc = Counter(r['code'] for r in rs); hp = Counter(r['hp'] for r in rs)
        cd = Counter(r['cutdebate'] for r in rs if r['cut'])
        print(c, len(rs), sum(r['correct'] for r in rs), sum(r['correct'] for r in rs if walk(items[r['id']])),
              sum(r['cut'] for r in rs), [cc[k] for k in ('GE', 'GE*', 'AMB', 'LE')],
              [hp[k] for k in 'NSCD'], [cd[k] for k in 'DEON'], sum(r['cwr'] for r in rs),
              sum(r['kw_ambig'] for r in rs), round(sum(r['tok'] for r in rs) / len(rs)))
    print()
    for c in CELLS:
        rs = by[c]
        print(c, 'LE:', [(r['v'], r['c'], r['ans']) for r in rs if r['code'] == 'LE'],
              'AMB:', [(r['v'], r['c'], r['ans']) for r in rs if r['code'] == 'AMB'],
              'GE*:', [(r['v'], r['c'], r['ans']) for r in rs if r['code'] == 'GE*'],
              'HP-D:', [(r['v'], r['c'], r['ans']) for r in rs if r['hp'] == 'D'],
              'CWR:', [(r['v'], r['c'], r['ans']) for r in rs if r['cwr']],
              'cut:', [(r['v'], r['c'], r['cutdebate'], r['code']) for r in rs if r['cut']],
              'wrong finished:', [(r['v'], r['c'], r['ans'], r['code'], r['hp']) for r in rs if not r['cut'] and not r['correct']])
    # clause sanity check
    print('\nclause words in text by C (says reaches / says at or above):')
    for C in (0, 1):
        rs = [r for r in A if r['C'] == C]
        print(C, sum(r['says_reaches'] for r in rs), sum(r['says_above'] for r in rs), len(rs))
    by1 = defaultdict(list)
    for r in B: by1[r['cell']].append(r)
    print('\nL1 per cell: n correct cut | rule Y/Y~/NS | HP N/S/C/D | CWR | wrong/cut')
    for c in CELLS:
        rs = by1[c]
        ru = Counter(r['rule'] for r in rs); hp = Counter(r['hp'] for r in rs)
        print(c, len(rs), sum(r['correct'] for r in rs), sum(r['cut'] for r in rs), [ru[k] for k in ('Y', 'Y~', 'NS')],
              [hp[k] for k in 'NSCD'], sum(r['cwr'] for r in rs),
              [(r['v'], r['ans'], r['hp'], r['cutdebate']) for r in rs if not r['correct']],
              'HP-D/C:', [(r['v'], r['ans'], r['hp']) for r in rs if r['hp'] in 'CD'])
