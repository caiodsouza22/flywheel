# AfterQuery environment setup

Dependency image recipe: `environment/Dockerfile`.

## Important platform rule

You write **only** the dependency-setup Dockerfile. AfterQuery checks out
your repository at the base commit you pick and places it at `/app`.

Do **not** `COPY` / `ADD` the repo into the image. The Dockerfile must install
from files already present under `/app` (for this repo: `requirements.txt`,
`pyproject.toml`, `src/`).

## Publish an environment (UI)

1. Open **AfterQuery → Repositories → flywheel → Environments**.
2. Pick a **base commit on `main`** that includes at least:
   - `requirements.txt`
   - `pyproject.toml`
   - `src/`
   - this `environment/Dockerfile` (for your reference; paste its contents)
3. Paste the contents of `environment/Dockerfile` into the Environments UI.
4. Submit and wait until the version is **published**.
5. Refresh the repository page — language pending should clear to **Python**
   once the environment is accepted.

## What the Dockerfile does

- Single `FROM python:3.12-slim`
- `WORKDIR /app`
- `ENV PYTHONPATH=/app/src` so `flywheel` imports resolve without editable install
- Pinned installs via `pip` (`pytest`, `pytest-cov`, `setuptools`, `wheel`)
- No `COPY`, no `ADD` from URLs, no `git clone`, no `|| true`, no `pip install -e .`