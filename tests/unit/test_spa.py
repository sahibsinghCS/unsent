"""Deep links load the single-page app with status 200; unknown API paths stay 404."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.main import mount_frontend


def test_deep_links_serve_index_and_api_stays_404(tmp_path):
    (tmp_path / "index.html").write_text("<html>app</html>")
    (tmp_path / "404.html").write_text("<html>not found</html>")
    (tmp_path / "app.js").write_text("console.log(1)")
    app = FastAPI()

    @app.get("/api/ping")
    def ping() -> dict:
        return {"ok": True}

    mount_frontend(app, tmp_path)
    client = TestClient(app)
    assert client.get("/api/ping").json() == {"ok": True}
    assert client.get("/app.js").text == "console.log(1)"
    for path in ("/", "/chat/abc", "/feedback/s_123", "/how"):
        response = client.get(path)
        assert response.status_code == 200, path
        assert "app" in response.text
    assert client.get("/api/does-not-exist").status_code == 404
