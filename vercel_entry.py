"""
Vercel FastAPI entrypoint.

Keeps local `uvicorn --app-dir server` imports working by putting
`server/` on sys.path, then re-exports `app`.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SERVER = Path(__file__).resolve().parent / "server"
if str(_SERVER) not in sys.path:
    sys.path.insert(0, str(_SERVER))

from app import app  # noqa: E402  (server/app.py)

__all__ = ["app"]
