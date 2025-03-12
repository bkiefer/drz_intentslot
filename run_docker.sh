#!/bin/bash
#set -xe
scrdir=`dirname "$0"`
cd "$srcdir"
docker run -d --rm \
       -p 5050:5050 \
       -v "$(pwd)/logs":/app/logs \
       -v "$(pwd)/adapters":/app/adapters \
       -v "$(pwd)/bert-base-german-cased":/app/bert-base-german-cased \
       --gpus=all \
       --entrypoint=/bin/bash \
       drz_daslot -c "python3 -u adapters_bio_tags_server.py 2>&1 | tee logs/server$(date -Iminutes).log"
