"""Botim Growth Platform — thin API gateway (edge).

This is a **thin edge**: it does ONLY cross-cutting concerns (authentication,
rate limiting, health/discovery) and contains **no business logic**. All domain
work lives in the independent services in :mod:`services`.

Deployment model
----------------
In **production** the gateway is a reverse proxy: each service in
``services.SERVICES`` is deployed and scaled **independently** behind its own
host/port, and the gateway forwards ``/api/<name>/*`` to the right upstream.

For this **in-process demo / test harness** we instead **mount** each service's
FastAPI ``app`` under its prefix using Starlette's ``app.mount(prefix, app)``,
so the whole platform is runnable in a single process::

    uvicorn api_gateway:app

The mounting is purely a convenience for a single-process demo — it does not
change the fact that each service is independently deployable (it can still be
run on its own via ``uvicorn services.<name>:app``).

Cross-cutting behaviors
-----------------------
* **Auth** — every ``/api/*`` request must carry a non-empty ``MOE-APPKEY``
  header; otherwise ``401``. ``/health`` is unauthenticated.
* **Rate limiting** — a simple per-APPKEY token bucket; over the limit -> ``429``.
  The limit is configurable (``rate_limit`` arg / ``GATEWAY_RATE_LIMIT`` env),
  defaulting high so normal traffic passes.
* **Discovery** — ``GET /health`` reports gateway status + mounted services.
"""
from __future__ import annotations

import os
import time
from typing import Dict, Tuple

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from services import SERVICES

APPKEY_HEADER = "MOE-APPKEY"
_DEFAULT_RATE_LIMIT = int(os.environ.get("GATEWAY_RATE_LIMIT", "10000"))


class _TokenBucket:
    """Minimal per-key token bucket: ``rate`` tokens refilled per ``per`` seconds."""

    def __init__(self, rate: int, per: float = 1.0) -> None:
        self.rate = rate
        self.per = per
        # key -> (tokens, last_refill_ts)
        self._state: Dict[str, Tuple[float, float]] = {}

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        tokens, last = self._state.get(key, (float(self.rate), now))
        # refill proportional to elapsed time, capped at capacity
        tokens = min(float(self.rate), tokens + (now - last) * (self.rate / self.per))
        if tokens < 1.0:
            self._state[key] = (tokens, now)
            return False
        self._state[key] = (tokens - 1.0, now)
        return True


def create_gateway(rate_limit: int = _DEFAULT_RATE_LIMIT) -> FastAPI:
    """Build the gateway app: mount services + apply auth & rate-limit middleware."""
    app = FastAPI(title="Botim Growth API Gateway", version="0.1.0")
    bucket = _TokenBucket(rate=rate_limit)

    # mount each independent service under its prefix (single-process demo only)
    for _name, (prefix, service_app) in SERVICES.items():
        app.mount(prefix, service_app)

    @app.middleware("http")
    async def _edge(request: Request, call_next):
        path = request.url.path
        # /health (and anything not under /api) is unauthenticated
        if path.startswith("/api/"):
            appkey = request.headers.get(APPKEY_HEADER, "")
            if not appkey:
                return JSONResponse(
                    status_code=401,
                    content={"detail": f"missing or empty {APPKEY_HEADER} header"},
                )
            if not bucket.allow(appkey):
                return JSONResponse(
                    status_code=429,
                    content={"detail": "rate limit exceeded"},
                )
        return await call_next(request)

    @app.get("/health")
    def health() -> Dict[str, object]:
        return {
            "status": "ok",
            "gateway": "Botim Growth API Gateway",
            "services": {name: prefix for name, (prefix, _a) in SERVICES.items()},
        }

    return app


# default app for `uvicorn api_gateway:app`
app = create_gateway()
