#!/bin/sh
#set -x
scrdir=`dirname "$0"`
type git-lfs >/dev/null 2>&1 || \
    (echo "No git-lfs installed, aborting!" ; exit 1)
if test \! -d bert-base-german-cased; then
    git clone https://huggingface.co/bert-base-german-cased
fi
if test \! -d adapters; then
    # Download adapters for intent and slot recognition
    wget https://cloud.dfki.de/owncloud/index.php/s/RW6f56AwiqgBKem/download/models.tar.gz
    tar xf models.tar.gz && rm models.tar.gz
fi
