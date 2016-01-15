'''

wex.py

    Given an example set of strings, find other strings that are similar.

    For instance, given an example of addresses in a single dataset, 
    find all address fields in all datasets

'''

import os
import argparse
import pandas as pd
import keras
import json
from glob import glob

import sys
sys.path.append('wit')
from wit import *
from mmd import *
from hackathon_functions import *

# --
# CLI

parser = argparse.ArgumentParser()
parser.add_argument('--config', dest = 'config', required = True)
args = parser.parse_args()

config = {
    "nb_epoch" : 3,
    "n_best"   : 5
}

config.update(json.load(open(args.config)))

nrows = 1000
ntest = 1000

# --
# Init
num_features = 75  # Character
max_len      = 350 # Character
formatter    = KerasFormatter(num_features, max_len)

# --
print '-- loading datasets --'
orig = {}
for f in glob(config['meta']['input']):
    key = f.split('/')[-1]
    orig[key] = pd.read_csv(f, nrows = nrows)
    orig[key].drop('Unnamed: 0', axis = 1, inplace = True)

# --
print '-- preprocessing --'
df  = pd.concat(map(lambda x: preprocess(x[0], x[1]), orig.iteritems()))

labeled_schemas = np.unique(np.hstack(map(lambda x: x.keys(), config['known_fields'].values())))
qdf = df[df.src.isin(labeled_schemas)]

# --
print '-- creating model --'

qdf.loc[:,'targetfield'] = qdf.variable.copy()
qdf.loc[:,'known_field'] = False

for k, v in config['known_fields'].iteritems():
    hashes = map(lambda x: '-'.join(x), v.items())
    sel    = qdf.hash.isin(hashes)
    qdf.targetfield[qdf.hash.isin(hashes)] = k
    qdf.known_field[qdf.hash.isin(hashes)] = True

qdf.targetfield[~qdf.known_field] = '_unknown'

trn, levs   = formatter.format(qdf, ['obj'], 'targetfield')
sclassifier = StringClassifier(trn, levs)
sclassifier.fit(batch_size = 100, nb_epoch = config['nb_epoch'])

# --
print '-- applying model --'
unq        = df.groupby('hash').apply(lambda x: x.sample(min(x.shape[0], ntest)))
awl, alevs = formatter.format(unq, ['obj'], 'hash')
labs       = awl['y'].argmax(1)

preds = sclassifier.predict(awl['x'][0], verbose = True, batch_size = 3 * 250)

# --
print '-- formatting for save --'
for i in range(preds.shape[1]):
    unq['pred_' + str(i)] = preds[:,i]

out = {}
for s in unq.src.unique():
    out[s] = {}
    for i in range(1, len(levs)):
        tmp = unq[unq.src == s].groupby('hash')['pred_%d' % i].apply(np.mean)
        tmp.sort_values(inplace = True, ascending = False)
        tmp   = tmp.head(config['n_best'])
        cands = map(lambda x: (x[0].split('-')[-1], x[1]), zip(tmp.index, tmp.tolist()))
        out[s][levs[i]] = cands

# --
print '-- writing --'
json.dump({
    "config" : config,
    "preds"  : out
}, open(config['meta']['output'], 'w'), indent = 2)

# -- END --