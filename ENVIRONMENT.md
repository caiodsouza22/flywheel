# AfterQuery environment setup

This repo’s dependency image lives at `environment/Dockerfile`.

## Why language was “pending”

GitHub already classifies this repository as **Python** only. AfterQuery’s
“language pending” state usually clears after it re-reads the repo and a
valid environment version publishes. `.gitattributes` marks docs/examples as
documentation so Linguist stays on Python.

## Publish an environment (UI)

1. Open **AfterQuery → Repositories → allot**.
2. Open **Environments** (or “Publish environment”).
3. Choose a **base commit** on `main` that includes:
   - `environment/Dockerfile`
   - `requirements.txt`
   - `pyproject.toml`
   - `src/`
4. Paste / upload the contents of `environment/Dockerfile` (or point the UI
   at that file if it accepts a path).
5. Submit and watch the live build.
6. Wait until the version status is **published** / available for new tasks.
7. Refresh the repository page — language should resolve to **Python** once
   the environment is accepted.

## Dockerfile contract (what this file does)

- Single `FROM python:3.12-slim`
- Pinned pip installs via `requirements.txt`
- Editable install of `allot` from `src/` (no tests copied into the image)
- No `curl | sh`, no `ADD` from URLs, no `git clone`, no `|| true`

## Local smoke check (optional)

```bash
docker build -f environment/Dockerfile -t allot-env .
docker run --rm allot-env python -c "import allot; print(allot.__version__)"
docker run --rm allot-env pytest -q
```
