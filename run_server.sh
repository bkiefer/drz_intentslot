#!/bin/bash
uv sync
uv run adapters_bio_tags_server.py "$@"
