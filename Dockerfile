FROM mypy:3.11

WORKDIR /app
COPY pyproject.toml /app
RUN uv sync

COPY adapters_bio_tags_server.py /app
COPY adapters_bio_tags.py /app
COPY adapters_classifier.py /app
