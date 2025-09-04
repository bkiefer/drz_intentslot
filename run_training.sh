#!/bin/bash
#set -xe
scrdir=`dirname "$0"`
cd "$srcdir"
docker run -it --rm \
       -v "$(pwd)":/app \
       --gpus=all \
       --entrypoint=/bin/bash \
       drz_daslot
