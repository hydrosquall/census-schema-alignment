import re
import json
import argparse
import numpy as np
import pandas as pd

import sys
sys.path.append('wit')
from mmd import *

from munkres import Munkres

# --
# Alignment functions

def align(dist):
    '''
        Munkres alignment between a single pair of schemas
    '''
    if dist.shape[0] > dist.shape[1]:
        return None
    else:
        mmap = Munkres().compute(np.array(dist))
        mmap = [ (dist.index[x[0]], dist.columns[x[1]]) for x in mmap ]
        mmap = [ (x[0], x[1], np.round(dist[x[1]].loc[x[0]], 3)) for x in mmap ]
        
        algn         = pd.DataFrame(mmap)
        algn.columns = ('hash_1', 'hash_2', 'cost')
        
        algn['variable_1'] = algn['hash_1'].apply(lambda x: x.split('-')[-1])
        algn['variable_2'] = algn['hash_2'].apply(lambda x: x.split('-')[-1])
        
        return algn


def all_alignments(dist, uschemas, verbose = False):
    '''
        Iterate `align` over all pairs of schemas
    '''
    alignments = []
    for s1 in uschemas:
        if verbose:
            print s1
        
        for s2 in uschemas:
            if s1 != s2:
                
                dist_ = dist.copy()
                dist_ = dist_[filter(lambda x: s1 in x, dist_.columns)]
                dist_ = dist_.loc[filter(lambda x: s2 in x, dist_.index)]
                
                algn = align(dist_)
                if np.any(algn):
                    algn['schema_1'] = s1
                    algn['schema_2'] = s2
                    
                    alignments.append(algn)
    
    alignments = pd.concat(alignments).drop_duplicates().reset_index()
    return alignments


def resolve_set(sets):
    '''
        Parse the strings that are created by `merge_pair` into sets of equivalent hashes.
    '''
    sets = [f.group(0) for f in re.finditer(r'\[[^\[\]]*\]', sets)]
    sets = filter(lambda x: x != '[None]', sets)
    sets = map(lambda x: re.sub('\[|\]', '', x), sets)
    sets = map(lambda x: re.sub('(^\w*)__', r'\1-', x), sets)
    return sets


def merge_pair(dpreds, uschema):
    '''
        Merge pair of schemas that have the lowest total cost.
        Repeating this will merge all schemas to a single schema.
    '''
    dist = dfdist(dpreds, dist_dist = True)
    a    = all_alignments(dist, uschema)
    
    # Find pairwise merge with lowest total cost
    pair_costs = a.groupby(['schema_1', 'schema_2']).cost.apply(np.mean).reset_index()
    pair_costs.sort_values('cost', inplace = True)
    best_merge = list(pair_costs.iloc[0][['schema_1', 'schema_2']])
    
    # Construct map for corresponding hashes
    links = a[a.schema_1.isin(best_merge) & a.schema_2.isin(best_merge)][['hash_1', 'hash_2']]
    links = [(r[1], r[2]) for r in links.to_records()]
    dl    = dict(links + [(l[1], l[0]) for l in links])
    
    # Map hashes together
    sel   = dpreds.lab.apply(lambda x: x.split('-')[0]).isin(best_merge)
    uhash = dpreds.lab[sel].unique()
    for uh in uhash:
        tmp = tuple(sorted((uh, dl.get(uh, None))))
        dpreds.lab[dpreds.lab == uh] = '{' + str(N) + '}' + '-' + re.sub('-', '__', '[%s][%s]' % tmp)
    
    return dpreds


# --
# CLI
parser = argparse.ArgumentParser()
parser.add_argument('--infile', dest = 'infile', required = True)
parser.add_argument('--outfile', dest = 'outfile', required = True)
args = parser.parse_args()

config = {
    'infile'  : args.infile,
    'outfile' : args.outfile
}

# --
print '-- loading datasets --'
inp           = np.load(config['infile']).item()
dpreds        = pd.DataFrame(inp['preds'])
dpreds['lab'] = map(lambda x: re.sub('(^[^-]*)-', '\\1', x), np.array(inp['levs'])[inp['labs']])

# --
print '-- aligning schemas --'
N = 0
while True:
    uschema = dpreds.lab.apply(lambda x: x.split('-')[0]).unique()
    print 'number of schemas : %d' % (len(uschema) - 1)
    
    if len(uschema) == 1:
        break
    
    dpreds = merge_pair(dpreds, uschema)
    
    N += 1

resolved_sets = map(resolve_set, dpreds.lab.unique())
json.dump(resolved_sets, open(config['outfile'], 'w'), indent = 2)