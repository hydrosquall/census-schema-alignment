#!/usr/bin/env python

import sys
import json
import argparse
import pandas as pd

pd.set_option('display.max_rows', 200)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 200)

class ALGN_RESOLVE:
    def __init__(self, inp):
        self.config  = inp['config']
        self.preds   = inp['preds']

        # formating for our command prompt
        self.pmpt_fmt = '\n\nWhich of these is a match? ("n" if no match) \n\n {0}'

    def run(self, outfile):
        self.outfile = outfile
        for k in self.preds.keys():
            self.resolve(k)
    
    def _resolve(self, df, known_field, preds):
        i = 0
        while i < len(preds):
            cmd = self.pmpt_fmt.format(
                self.our_prmt,
                list(df[preds[i][0]]),
                known_field, 
                preds[i][0]
            )
            
            x = raw_input(cmd)
            print '--'
            
            if x is self.pos_cont:
                return i
            elif x is self.neg_cont:
                i += 1
            else:
                return None
    
    def resolve(self, key):
        print key
        path = '/'.join(self.config['meta']['input'].split('/')[:-1]) + '/' + key
        df   =  pd.read_csv(path, nrows = 5)
        
        for known, preds in self.preds[key].items():
            ths = df[[p[0] for p in preds]]
            print self.pmpt_fmt.format(ths)
            cmd = raw_input('\n' + known + '\t?\t')
            if cmd != 'n':
                try:
                    self.preds[key][known] = preds[int(cmd)]
                except:
                    self.preds[key][known] = []
                
                json.dump(self.preds, open(self.outfile, 'w'), indent = 2)
            

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--infile', dest = 'infile', required = True)
    parser.add_argument('--outfile', dest = 'outfile', required = True)
    args = parser.parse_args()
    ALGN_RESOLVE(json.load(open(args.infile))).run(args.outfile)

