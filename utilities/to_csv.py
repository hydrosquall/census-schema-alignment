import os
import json
import pandas as pd
import argparse
from glob import glob

def str_(x):
    try:
        return str(x)
    except:
        return 'nan'

def flatten_dict(d):
    for k,v in d.items():
        if isinstance(v, dict):
            for k0, v0 in flatten_dict(v):
                yield (k + '__' + k0, str_(v0))
        else:
            yield (k, str_(v))

# --
# CLI

parser = argparse.ArgumentParser()
parser.add_argument('--infile', dest = 'infile', required = True)
parser.add_argument('--outfile', dest = 'outfile', required = True)
args = parser.parse_args()


fs = glob(os.path.join(args.infile, '*.json'))
for f in fs:
    print f
    tmp = json.load(open(f))
    nm  = tmp.keys()[0]
    tmp = tmp[nm]
    tmp = map(lambda x: dict(list(flatten_dict(x))), tmp)
    pd.DataFrame(tmp).to_csv(os.path.join(args.outfile, nm + '.csv'), encoding = 'utf-8')