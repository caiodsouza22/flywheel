FROM python:3.12-slim

WORKDIR /app

# Install pinned tooling first, then the library from the checked-out repo.
# The platform supplies the repository at /app for this build context.
COPY requirements.txt pyproject.toml README.md LICENSE ./
COPY src ./src

RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -e .
