"""The ops middleware on a real app: 429s, 413s, security headers, text-free logs, startup hook."""

from __future__ import annotations

import json
import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from backend.app import ops
from backend.app.main import mount_frontend
from backend.app.ops.headers import app_csp, inline_script_hashes
from backend.app.ops.middleware import client_hash, client_ip

SECRET = "my friend said she wants to disappear"


class Body(BaseModel):
    text: str


def make_app(monkeypatch, tmp_path=None, **env: str) -> FastAPI:
    monkeypatch.setenv("FR_RATE_LIMIT", "1")
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    app = FastAPI()

    @app.get("/api/health")
    def health() -> dict:
        return {"ok": True}

    @app.post("/api/sessions")
    def create() -> dict:
        return {"session_id": "s_1"}

    @app.post("/api/sessions/{session_id}/messages")
    def message(session_id: str, body: Body) -> dict:
        return {"echo_len": len(body.text)}

    ops.install(app)
    if tmp_path is not None:
        mount_frontend(app, tmp_path)
    return app


def test_rate_limit_returns_429_json_with_retry_after(monkeypatch):
    client = TestClient(make_app(monkeypatch, FR_RL_SESSIONS_PER_MIN="2"))
    assert client.post("/api/sessions").status_code == 200
    assert client.post("/api/sessions").status_code == 200
    refused = client.post("/api/sessions")
    assert refused.status_code == 429
    body = refused.json()
    assert set(body) == {"detail", "retry_after"}
    assert body["retry_after"] >= 1
    assert refused.headers["retry-after"] == str(body["retry_after"])
    assert "content-security-policy" in refused.headers


def test_health_is_never_rate_limited(monkeypatch):
    client = TestClient(make_app(monkeypatch, FR_RL_API_PER_MIN="1"))
    assert all(client.get("/api/health").status_code == 200 for _ in range(20))


def test_forwarded_for_only_trusted_when_configured(monkeypatch):
    client = TestClient(make_app(monkeypatch, FR_RL_SESSIONS_PER_MIN="1", FR_TRUST_PROXY="1"))
    assert client.post("/api/sessions", headers={"x-forwarded-for": "9.9.9.1, 10.0.0.1"}).is_success
    assert client.post("/api/sessions", headers={"x-forwarded-for": "9.9.9.2, 10.0.0.1"}).is_success
    assert client.post("/api/sessions", headers={"x-forwarded-for": "9.9.9.1"}).status_code == 429

    untrusted = TestClient(make_app(monkeypatch, FR_RL_SESSIONS_PER_MIN="1", FR_TRUST_PROXY="0"))
    assert untrusted.post("/api/sessions", headers={"x-forwarded-for": "1.1.1.1"}).is_success
    spoofed = untrusted.post("/api/sessions", headers={"x-forwarded-for": "2.2.2.2"})
    assert spoofed.status_code == 429  # a spoofed header can't buy a fresh bucket


def test_client_ip_parsing():
    scope = {"headers": [(b"x-forwarded-for", b" 7.7.7.7 , 10.0.0.1")], "client": ("10.0.0.9", 1)}
    assert client_ip(scope, trust_proxy=True) == "7.7.7.7"
    assert client_ip(scope, trust_proxy=False) == "10.0.0.9"
    assert client_ip({"headers": []}, trust_proxy=True) == "unknown"


def test_rate_limits_off_by_default_outside_prod(monkeypatch):
    monkeypatch.delenv("FR_RATE_LIMIT", raising=False)
    monkeypatch.setenv("FR_ENV", "dev")
    app = FastAPI()
    ops.install(app)
    assert app.state.rate_limiter is None
    monkeypatch.setenv("FR_ENV", "prod")
    ops.install(app2 := FastAPI())
    assert app2.state.rate_limiter is not None


def test_oversized_body_gets_413(monkeypatch):
    client = TestClient(make_app(monkeypatch, FR_MAX_BODY_BYTES="1000"))
    ok = client.post("/api/sessions/s_1/messages", json={"text": "hi"})
    assert ok.status_code == 200
    big = client.post("/api/sessions/s_1/messages", json={"text": "x" * 2000})
    assert big.status_code == 413
    assert "too large" in big.json()["detail"]


def test_streamed_body_without_length_is_also_capped(monkeypatch):
    client = TestClient(make_app(monkeypatch, FR_MAX_BODY_BYTES="1000"))

    def chunks():
        for _ in range(10):
            yield b'{"text": "' + b"y" * 300 + b'"}'

    response = client.post(
        "/api/sessions/s_1/messages", content=chunks(), headers={"content-type": "application/json"}
    )
    assert response.status_code == 413


def test_default_body_limit_is_32kb(monkeypatch):
    monkeypatch.delenv("FR_MAX_BODY_BYTES", raising=False)
    assert ops.max_body_bytes() == 32 * 1024


def test_security_headers_on_api_and_spa(monkeypatch, tmp_path):
    (tmp_path / "index.html").write_text("<html><script>var a=1;</script>app</html>")
    client = TestClient(make_app(monkeypatch, tmp_path))
    for path in ("/api/health", "/", "/chat/abc"):
        headers = client.get(path).headers
        csp = headers["content-security-policy"]
        assert "default-src 'self'" in csp
        assert "frame-ancestors 'self' https://huggingface.co https://*.hf.space" in csp
        assert "'unsafe-inline'" not in csp
        assert headers["x-content-type-options"] == "nosniff"
        assert headers["referrer-policy"] == "no-referrer"
        assert "camera=()" in headers["permissions-policy"]
        assert headers["strict-transport-security"].startswith("max-age=")
        assert "x-frame-options" not in headers  # Hugging Face embeds Spaces in an iframe
        assert "server" not in headers


def test_csp_allows_exactly_the_inline_scripts_by_hash(tmp_path):
    index = tmp_path / "index.html"
    index.write_text('<script src="/a.js"></script><script>\n  hello();\n</script>')
    hashes = inline_script_hashes(index)
    assert len(hashes) == 1 and hashes[0].startswith("'sha256-")
    csp = app_csp(hashes)
    assert f"script-src 'self' {hashes[0]}" in csp
    assert "img-src 'self' data:" in csp and "connect-src 'self'" in csp
    assert "base-uri 'self'" in csp and "form-action 'self'" in csp
    assert inline_script_hashes(tmp_path / "missing.html") == []


def test_docs_pages_get_their_own_policy(monkeypatch):
    client = TestClient(make_app(monkeypatch))
    csp = client.get("/docs").headers["content-security-policy"]
    assert "cdn.jsdelivr.net" in csp
    assert "cdn.jsdelivr.net" not in client.get("/api/health").headers["content-security-policy"]


def test_one_log_line_per_request_without_text_or_ids(monkeypatch, caplog):
    client = TestClient(make_app(monkeypatch))
    with caplog.at_level(logging.INFO, logger="firstreply.request"):
        client.post("/api/sessions/s_secret123/messages", json={"text": SECRET})
    lines = [r.getMessage() for r in caplog.records if r.name == "firstreply.request"]
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert set(entry) == {"evt", "method", "route", "status", "ms", "client"}
    assert entry["route"] == "/api/sessions/{session_id}/messages"
    assert entry["status"] == 200 and entry["method"] == "POST"
    assert SECRET not in lines[0] and "s_secret123" not in lines[0]
    assert "testclient" not in lines[0]  # the raw client address is hashed


def test_client_hash_is_salted_and_rotates_daily():
    assert client_hash("1.2.3.4", "2026-10-24") == client_hash("1.2.3.4", "2026-10-24")
    assert client_hash("1.2.3.4", "2026-10-24") != client_hash("1.2.3.4", "2026-10-25")
    assert client_hash("1.2.3.4", "2026-10-24") != client_hash("1.2.3.5", "2026-10-24")
    assert "1.2.3.4" not in client_hash("1.2.3.4")


def test_static_requests_log_as_static(monkeypatch, tmp_path, caplog):
    (tmp_path / "index.html").write_text("<html>app</html>")
    client = TestClient(make_app(monkeypatch, tmp_path))
    with caplog.at_level(logging.INFO, logger="firstreply.request"):
        client.get("/feedback/s_private")
    entry = json.loads(caplog.records[-1].getMessage())
    assert entry["route"] == "static"


def test_on_startup_starts_purge_and_logs_ready(monkeypatch, caplog):
    monkeypatch.setattr(ops.purger, "interval", 3600.0)
    with caplog.at_level(logging.INFO, logger="firstreply.ops"):
        ops.on_startup()
    assert ops.purger.running
    ready = [json.loads(r.getMessage()) for r in caplog.records if '"ready"' in r.getMessage()]
    assert ready and ready[0]["components"]["guardian"] in {"real", "stub"}
    assert "OPENAI_API_KEY" not in caplog.text and "sk-" not in caplog.text
    ops.purger.stop()


def test_main_app_has_ops_installed():
    from backend.app.main import app

    assert any(m.cls.__name__ == "OpsMiddleware" for m in app.user_middleware)


def test_route_template_keeps_router_prefix(caplog):
    from backend.app.main import app

    client = TestClient(app)
    with caplog.at_level(logging.INFO, logger="firstreply.request"):
        client.get("/api/sessions/s_nothere")
    entry = json.loads(caplog.records[-1].getMessage())
    assert entry["route"] == "/api/sessions/{session_id}"
    assert entry["status"] == 404
