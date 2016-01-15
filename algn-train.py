# --
# Load deps

import os
import json
import keras
import argparse
import numpy as np
import pandas as pd

import sys
sys.path.append('wit')
from wit import *
from mmd import *
from helper_functions import *

# --
# CLI

parser = argparse.ArgumentParser()
parser.add_argument('--config', dest = 'config', required = True)
args = parser.parse_args()

config = json.load(open(args.config))

# --

num_features = 75  # Character
max_len      = 350 # Character
formatter    = KerasFormatter(num_features, max_len)

# --
print '-- loading datasets --'
orig = {}
_    = [orig.update(json.load(open(f))) for f in config['fs']]

# --
print '-- preprocessing --'
df        = pd.concat(map(lambda x: preprocess(x[0], x[1]), orig.iteritems()))
train     = make_triplet_train(df, N = 600)
trn, levs = formatter.format(train, ['obj'], 'hash')

# --
print '-- creating model --'
arch_path   = config['model_path'] + '__arch.json'
weight_path = config['model_path'] + '__weight.h5'

if config['train_model']:
    classifier = TripletClassifier(trn, levs)
    classifier.fit(batch_size = 250, nb_epoch = 3)
    
    json_string = classifier.model.to_json()
    open(arch_path, 'w').write(json_string)
    classifier.model.save_weights(weight_path, overwrite = True)
else:
    model = keras.models.model_from_json(open(arch_path).read())
    model.load_weights(weight_path)
    classifier = TripletClassifier(trn, levs, model)

# --
print '-- applying model --'
unq    = df.groupby('hash').apply(lambda x: x.sample(min(x.shape[0], 1000)))
awl, _ = formatter.format(unq, ['obj'], 'hash')
labs   = awl['y'].argmax(1)

preds = classifier.predict(awl['x'][0], verbose = True, batch_size = 3 * 250)

# --
print '-- writing --'
np.save(config['outfile'], {
    'preds' : preds,
    'labs'  : labs,
    'levs'  : levs
})
