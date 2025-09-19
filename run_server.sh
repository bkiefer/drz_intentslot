#!/bin/bash
scrdir=`dirname $0`
cd "$scrdir"
uv sync
uv run adapters_bio_tags_server.py "$@"
