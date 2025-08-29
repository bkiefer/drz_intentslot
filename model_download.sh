#!/bin/sh
#set -x
scrdir=`dirname "$0"`
if test -d adapters; then
    :
else
    git clone https://huggingface.co/bert-base-german-cased
    # Download models for intent and slot recognition
    wget https://cloud.dfki.de/owncloud/index.php/s/RW6f56AwiqgBKem/download/models.tar.gz
    tar xf models.tar.gz && rm models.tar.gz
fi
