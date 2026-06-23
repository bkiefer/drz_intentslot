#!/bin/bash
#set -xe
scrdir=`dirname "$0"`
cd "$srcdir"
version=`grep version "$scrdir/pyproject.toml" | sed 's/version *= *"\([^"]*\)".*/\1/'`

if test -z "$DOCKER_ARGS"; then
    args=("-d", "--rm")
else
    readarray -t -d '' args < <(xargs printf '%s\0' <<<"$DOCKER_ARGS")
fi

docker run "${args[@]}" \
       -p 5050:5050 \
       -v "$(pwd)/logs":/app/logs \
       -v "$(pwd)/adapters":/app/adapters \
       -v "$(pwd)/bert-base-german-cased":/app/bert-base-german-cased \
       --gpus=all \
       --entrypoint=/bin/bash \
       drz_daslot:$version -c "uv run adapters_bio_tags_server.py 2>&1 | tee logs/server$(date -Iminutes).log"
