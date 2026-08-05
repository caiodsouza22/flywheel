FROM python:3.12-slim

WORKDIR /app

# Platform checks out the repository at /app before dependency setup runs.
# Install pinned tooling, then the library in editable mode.
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -e .
