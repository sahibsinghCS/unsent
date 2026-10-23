"""Download the fastembed model into FASTEMBED_CACHE_PATH at image build time and check it works.

Run by the Dockerfile so the container starts fast and never needs the network for embeddings:
    FASTEMBED_CACHE_PATH=/app/.cache/fastembed python -m deploy.predownload
"""

from __future__ import annotations

import os
import sys
import time

os.environ["FR_EMBED"] = "fastembed"

from backend.app import embed  # noqa: E402


def main() -> int:
    started = time.time()
    vectors = embed.embed(["warm up", "¿estás bien?"])
    if vectors.shape != (2, 384):
        print(f"unexpected embedding shape {vectors.shape}", file=sys.stderr)
        return 1
    cache = os.getenv("FASTEMBED_CACHE_PATH", "(fastembed default)")
    print(
        f"fastembed model {embed.embed_model_name()} ready in {cache} ({time.time() - started:.1f}s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
