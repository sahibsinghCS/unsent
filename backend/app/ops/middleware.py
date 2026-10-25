"""One ASGI middleware that wraps every request: client identity, rate limit, body-size limit,
security headers and a single text-free JSON log line.

It is plain ASGI (not BaseHTTPMiddleware) so it adds almost no latency and can stop an oversized
body while it streams in, before the app ever parses it.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import secrets
import time
from datetime import date

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from backend.app.ops.headers import DOCS_PATHS, security_headers
from backend.app.ops.ratelimit import RateLimiter, retry_after_header

log = logging.getLogger("firstreply.request")

# A random secret per process: the client hash can't be reversed into an IP, even by us later.
_SALT = secrets.token_bytes(32)


def client_ip(scope: Scope, trust_proxy: bool, hops: int = 1) -> str:
    """Behind a trusted proxy, the address that proxy saw: the `hops`-th X-Forwarded-For entry from
    the right. Entries further left are written by the client and can be forged to dodge rate limits.
    Without a trusted proxy, the socket peer."""
    if trust_proxy:
        entries = [
            part.strip()
            for name, value in scope.get("headers", [])
            if name == b"x-forwarded-for"
            for part in value.decode("latin-1").split(",")
        ]
        entries = [entry for entry in entries if entry]
        if entries:
            return entries[-min(max(hops, 1), len(entries))]
    client = scope.get("client")
    return client[0] if client else "unknown"


def client_hash(ip: str, day: str | None = None) -> str:
    """Salted, daily-rotating pseudonym for logs (12 hex chars). The raw IP is never logged."""
    day = day or date.today().isoformat()
    return hmac.new(_SALT, f"{day}|{ip}".encode(), hashlib.sha256).hexdigest()[:12]


def route_template(scope: Scope) -> str:
    """'/api/sessions/{session_id}/messages', never the real ID; static files collapse to 'static'."""
    raw = scope.get("path", "")
    route = scope.get("route")
    path = getattr(route, "path", None)
    if isinstance(path, str) and path not in ("", "/"):
        # A route from include_router(prefix="/api") reports "/health": put the prefix back.
        raw_parts, tmpl_parts = raw.strip("/").split("/"), path.strip("/").split("/")
        prefix = raw_parts[: max(0, len(raw_parts) - len(tmpl_parts))]
        return "/" + "/".join([*prefix, *tmpl_parts])
    if raw.startswith("/api"):
        return "/api/<unmatched>"
    if raw in DOCS_PATHS or raw == "/openapi.json":
        return raw
    return "static"


async def _send_json(send: Send, status: int, body: dict, extra: list[tuple[bytes, bytes]]) -> None:
    payload = json.dumps(body).encode()
    headers = [
        (b"content-type", b"application/json"),
        (b"content-length", str(len(payload)).encode()),
        *extra,
    ]
    await send({"type": "http.response.start", "status": status, "headers": headers})
    await send({"type": "http.response.body", "body": payload})


class OpsMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        limiter: RateLimiter | None,
        max_body_bytes: int,
        app_csp: str,
        docs_csp: str,
        trust_proxy: bool,
        proxy_hops: int = 1,
        upload_paths: dict[str, int] | None = None,
    ) -> None:
        self.app = app
        self.limiter = limiter
        self.max_body = max_body_bytes
        self.trust_proxy = trust_proxy
        self.proxy_hops = proxy_hops
        self.upload_paths = upload_paths or {}  # endpoints that take screenshots get a bigger cap
        self.app_headers = security_headers(app_csp)
        self.docs_headers = security_headers(docs_csp)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        started = time.perf_counter()
        path = scope.get("path", "")
        method = scope.get("method", "GET")
        ip = client_ip(scope, self.trust_proxy, self.proxy_hops)
        extra = self.docs_headers if path in DOCS_PATHS else self.app_headers
        state = {"status": 500}

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                state["status"] = message["status"]
                headers = [h for h in message.get("headers", []) if h[0].lower() != b"server"]
                message = {**message, "headers": headers + extra}
            await send(message)

        try:
            if self.limiter is not None:
                wait = self.limiter.check(ip, method, path)
                if wait is not None:
                    retry = retry_after_header(wait)
                    await _send_json(
                        send_wrapper,
                        429,
                        {
                            "detail": "Too many requests. Please slow down.",
                            "retry_after": int(retry),
                        },
                        [(b"retry-after", retry.encode())],
                    )
                    return

            limit = self.upload_paths.get(path.rstrip("/"), self.max_body)
            length = _content_length(scope)
            if length is not None and length > limit:
                await _too_large(send_wrapper, limit)
                return
            if length is None and method in ("POST", "PUT", "PATCH"):
                # Chunked body with no declared length: read it here and cap it.
                body = await self._read_capped(receive, limit)
                if body is None:
                    await _too_large(send_wrapper, limit)
                    return
                receive = _replay(body, receive)

            await self.app(scope, receive, send_wrapper)
        finally:
            _log_request(method, scope, state["status"], started, ip)

    async def _read_capped(self, receive: Receive, limit: int) -> bytes | None:
        """The whole body, or None as soon as it passes the limit (a declared Content-Length
        is enforced by the HTTP server itself, so only chunked bodies need this)."""
        chunks: list[bytes] = []
        size = 0
        while True:
            message = await receive()
            if message["type"] != "http.request":
                break
            chunk = message.get("body", b"")
            size += len(chunk)
            if size > limit:
                return None
            chunks.append(chunk)
            if not message.get("more_body", False):
                break
        return b"".join(chunks)


def _replay(body: bytes, receive: Receive) -> Receive:
    """A receive() that hands the app the already-read body once, then defers to the server."""
    sent = False

    async def replay() -> Message:
        nonlocal sent
        if not sent:
            sent = True
            return {"type": "http.request", "body": body, "more_body": False}
        return await receive()

    return replay


def _content_length(scope: Scope) -> int | None:
    for name, value in scope.get("headers", []):
        if name == b"content-length":
            try:
                return int(value)
            except ValueError:
                return None
    return None


async def _too_large(send: Send, limit: int) -> None:
    await _send_json(send, 413, {"detail": f"Request body too large (limit {limit} bytes)."}, [])


def _log_request(method: str, scope: Scope, status: int, started: float, ip: str) -> None:
    """Method, route template, status, latency and client pseudonym. Never text or session IDs."""
    entry = {
        "evt": "request",
        "method": method,
        "route": route_template(scope),
        "status": status,
        "ms": round((time.perf_counter() - started) * 1000, 1),
        "client": client_hash(ip),
    }
    log.info(json.dumps(entry))
