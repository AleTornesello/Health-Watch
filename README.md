# Health Watch

A small FastAPI service that reads a list of services from a YAML file and
exposes a dedicated health check REST endpoint for each one.

Each service is declared with a **name** (used as the API path key), a
**type** (the kind of probe to run — `http`, `tcp`, `postgres`, ...), and a
set of **settings** specific to that type (URL, host/port, credentials, ...).

## Features

- One endpoint per service: `GET /service/<name>/health`
- Pluggable checker types: `http`, `tcp`, `postgres` out of the box, more can
  be added with a single class
- Fails fast and loud: invalid or missing configuration exits the process at
  startup with a clear error, instead of failing silently at request time
- Secrets kept out of the YAML file via `${VAR}` / `${VAR:-default}`
  environment variable interpolation
- `/services` endpoint listing everything that's configured
- `/health` liveness endpoint for the app itself (separate from the services
  it monitors)

## Requirements

- Python >= 3.12
- [uv](https://docs.astral.sh/uv/) for dependency management

## Installation

```bash
uv sync
```

## Configuration

Health Watch looks for its services file in this order:

1. The path given by the `HEALTH_WATCH_SERVICES_FILE` environment variable.
2. `services.yaml` in the project root.

If neither resolves to a valid, readable file, the app logs an error and
exits with a non-zero status instead of starting.

### File format

```yaml
services:
  - name: example-api          # used in the URL: /service/example-api/health
    type: http
    settings:
      url: https://httpbin.org/status/200
      method: GET               # optional, default GET
      timeout: 5                # seconds, optional, default 5
      expected_status: 200      # optional, default 200
      headers: {}                # optional

  - name: redis-cache
    type: tcp
    settings:
      host: localhost
      port: 6379
      timeout: 3                # seconds, optional, default 5

  - name: primary-db
    type: postgres
    settings:
      host: localhost
      port: 5432                # optional, default 5432
      username: postgres
      password: ${PRIMARY_DB_PASSWORD:-postgres}
      database: app_db
      timeout: 5                # seconds, optional, default 5
```

Any string value in the file can reference an environment variable:

- `${VAR_NAME}` — resolves to the value of `VAR_NAME`, or fails startup if it
  isn't set
- `${VAR_NAME:-default}` — resolves to `VAR_NAME` if set, otherwise falls
  back to `default`

Service names must be unique, and `type` must match a registered checker
(see [Adding a new checker type](#adding-a-new-checker-type)).

## Running

```bash
uv run uvicorn app.main:app --reload
```

Or point at a specific configuration file:

```bash
HEALTH_WATCH_SERVICES_FILE=/path/to/services.yaml uv run uvicorn app.main:app
```

Interactive API docs are then available at `http://127.0.0.1:8000/docs`.

## API

| Endpoint                      | Description                                   |
| ------------------------------ | ---------------------------------------------- |
| `GET /health`                  | Liveness check for the Health Watch app itself |
| `GET /services`                | Lists all configured services and their types  |
| `GET /service/{name}/health`   | Runs the health check for `name` on demand     |

Each `/service/{name}/health` response:

```json
{
  "name": "example-api",
  "type": "http",
  "status": "healthy",
  "latency_ms": 42.17,
  "detail": "HTTP 200 from https://httpbin.org/status/200"
}
```

`status` is `healthy` or `unhealthy`. The HTTP status code mirrors this:
`200` when healthy, `503` when unhealthy — a checker failure never crashes
the endpoint, it's reported as `unhealthy` with the error in `detail`.

## Project structure

```
app/
  main.py                    FastAPI app: startup, route registration
  config.py                  Locates, reads, and validates the services file
  models.py                  Pydantic schemas (config + API responses)
  registry.py                Builds the name -> checker map
  exceptions.py               ConfigurationError
  checkers/
    base.py                  Abstract BaseChecker (timing + error handling)
    http_checker.py          type: http
    tcp_checker.py           type: tcp
    postgres_checker.py      type: postgres
    __init__.py               Checker type registry / factory
services.yaml                 Example / default configuration
```

## Adding a new checker type

1. Create `app/checkers/<name>_checker.py` with a Pydantic `Settings` model
   for its config and a `Checker(BaseChecker)` class implementing
   `async def _probe(self) -> str | None`, raising an exception on failure.
2. Register it in `CHECKER_TYPES` in `app/checkers/__init__.py`.
3. Reference the new `type` in `services.yaml`.

No other file needs to change — routes are generated automatically from
whatever is registered.
