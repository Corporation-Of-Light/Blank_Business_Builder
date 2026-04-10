# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

Better Business Builder (BBB) is a Python/FastAPI application for AI-powered business planning and marketing automation. The main package is `blank_business_builder` under `src/`. A duplicate `bbb` package also exists under `src/bbb/` (shares the same structure; the canonical package used by tests and the Dockerfile is `blank_business_builder`).

### Running tests

```bash
python3 -m pytest --tb=short
```

- Tests use **in-memory SQLite** via `tests/conftest.py` — no PostgreSQL or Redis needed.
- 170+ tests pass out of the box. Pre-existing failures include OWASP security tests (expect specific middleware/headers not yet implemented), migration tests (require PostgreSQL + Alembic), and some business-endpoint tests (fixture issues).
- The `bcrypt<4.1` pin is required because `passlib` is incompatible with `bcrypt>=4.1` on Python 3.12.

### Running the dev server

```bash
DATABASE_URL=sqlite:///./dev.db ENVIRONMENT=development DEBUG=true JWT_SECRET_KEY=dev-secret-key-for-testing \
  python3 -m uvicorn blank_business_builder.main:app --host 0.0.0.0 --port 8000 --reload
```

Before first run, initialize the SQLite database:

```bash
DATABASE_URL=sqlite:///./dev.db python3 -c "from blank_business_builder.database import init_db; init_db('sqlite:///./dev.db')"
```

- The `DATABASE_URL` env var controls the database. Default is PostgreSQL, but `sqlite:///./dev.db` works for local dev.
- API docs at `http://localhost:8000/docs` (Swagger) or `http://localhost:8000/redoc`.
- Health check: `GET /health`.

### Linting

```bash
python3 -m flake8 src/blank_business_builder/ --max-line-length=120
python3 -m black --check src/
python3 -m isort --check-only src/
```

Pre-existing lint warnings exist in the codebase; these are not regressions.

### Key gotchas

- `pydantic[email]` (provides `email-validator`) is required at runtime but not listed in `pyproject.toml` dependencies — install it explicitly.
- `bcrypt` must be pinned to `<4.1` due to `passlib` compatibility on Python 3.12+.
- The `create_engine` call in `database.py` uses `pool_size`/`max_overflow` kwargs that SQLite ignores silently — this is fine for dev.
- External service API keys (Stripe, OpenAI, SendGrid, etc.) are optional; the app degrades gracefully without them.
