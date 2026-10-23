"""Security headers, including a Content-Security-Policy built for the real frontend build.

The built index.html has one small inline script (it applies dark mode before first paint). Instead
of allowing every inline script ('unsafe-inline'), we allow exactly that script by its SHA-256 hash,
computed from the file at startup, so the policy stays correct after every rebuild.
"""

from __future__ import annotations

import base64
import hashlib
import re
from pathlib import Path

FRAME_ANCESTORS = "'self' https://huggingface.co https://*.hf.space"
HSTS = "max-age=2592000"  # 30 days, no preload: modest on purpose for a demo domain

_INLINE_SCRIPT = re.compile(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", re.S | re.I)

# FastAPI's /docs and /redoc pages load Swagger/ReDoc from a CDN with inline bootstraps.
DOCS_PATHS = frozenset({"/docs", "/redoc", "/docs/oauth2-redirect"})


def inline_script_hashes(index_html: Path) -> list[str]:
    """CSP source expressions ('sha256-…') for each inline <script> in the built index.html."""
    if not index_html.is_file():
        return []
    text = index_html.read_text(encoding="utf-8")
    hashes = []
    for body in _INLINE_SCRIPT.findall(text):
        digest = hashlib.sha256(body.encode("utf-8")).digest()
        hashes.append(f"'sha256-{base64.b64encode(digest).decode()}'")
    return hashes


def app_csp(script_hashes: list[str]) -> str:
    """Policy for the app and the API: same-origin only, no inline script except the hashed ones."""
    script_src = " ".join(["'self'", *script_hashes])
    return "; ".join(
        [
            "default-src 'self'",
            f"script-src {script_src}",
            "style-src 'self'",
            "img-src 'self' data:",
            "font-src 'self'",
            "connect-src 'self'",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            f"frame-ancestors {FRAME_ANCESTORS}",
        ]
    )


def docs_csp() -> str:
    """Looser policy only for the interactive API docs pages (no user content there)."""
    cdn = "https://cdn.jsdelivr.net"
    return "; ".join(
        [
            "default-src 'self'",
            f"script-src 'self' 'unsafe-inline' {cdn}",
            f"style-src 'self' 'unsafe-inline' {cdn}",
            f"img-src 'self' data: https://fastapi.tiangolo.com {cdn}",
            "worker-src 'self' blob:",
            "connect-src 'self'",
            "base-uri 'self'",
            "form-action 'self'",
            f"frame-ancestors {FRAME_ANCESTORS}",
        ]
    )


def security_headers(csp: str) -> list[tuple[bytes, bytes]]:
    """Headers added to every response. No X-Frame-Options: Hugging Face shows Spaces in an iframe."""
    pairs = {
        "content-security-policy": csp,
        "x-content-type-options": "nosniff",
        "referrer-policy": "no-referrer",
        "permissions-policy": (
            "camera=(), microphone=(), geolocation=(), payment=(), usb=(), "
            "interest-cohort=(), browsing-topics=()"
        ),
        "strict-transport-security": HSTS,
        "cross-origin-opener-policy": "same-origin",
    }
    return [(k.encode(), v.encode()) for k, v in pairs.items()]
