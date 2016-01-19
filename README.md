# census-schema-alignment
Census Schema Alignment (January 2016 XDATA Census Hackathon)

### Install

    # Install forked version of Keras
    git clone https://github.com/bkj/keras.git
    cd keras
    python setup.py install
  
    # Download `wit`
    cd census-schema-alignment
    git clone https://github.com/bkj/wit.git
  
### Data


    wget http://.../formatted-data.tar.gz
    tar -xzvf formatted-data.tar.gz    
    python utilities/to_csv.py \
        --infile /path/to/formatted-data \
        --outfile /path/to/csv-data

### Example


Alignment

    python algn-train.py --config algn-config.json
    python algn-merge.py --infile algn.npy --outfile output/algn-v0.json

Extraction

    python wex.py --config wex-config.json
    python algn-resolve.py \
        --infile output/wex-output.json \
        --outfile output/wex-output-resolved.json

(Some paths in the config files may need to be changed for examples to run cleanly.)
