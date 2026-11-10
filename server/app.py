"""
AppStore — standalone Play Store landing + publisher.

Run locally:
  cd server
  pip install -r ../requirements.txt
  uvicorn app:app --host 0.0.0.0 --port 8000

Deploy: Vercel (see ../README.md) — entrypoint vercel_entry:app
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from play_admin_auth import get_admin_path
from play_landing import ensure_seed_tesla, router as play_router

SERVER_DIR = Path(__file__).resolve().parent
WEB_DIR = SERVER_DIR / "web"

app = FastAPI(
    title="AppStore",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

# Seed demo Tesla share (icon only; APK optional)
try:
    ensure_seed_tesla()
except Exception:
    pass

app.include_router(play_router)

if WEB_DIR.is_dir():
    app.mount("/web", StaticFiles(directory=str(WEB_DIR)), name="web-static")


def _host_name() -> str:
    if os.getenv("VERCEL") or os.getenv("VERCEL_ENV"):
        return "vercel"
    if os.getenv("FLY_APP_NAME"):
        return "fly"
    if os.getenv("RENDER"):
        return "render"
    return "local"


@app.get("/health")
async def health():
    return {
        "ok": True,
        "service": "appstore",
        "admin": f"/{get_admin_path()}",
        "host": _host_name(),
    }


@app.get("/", response_class=HTMLResponse)
async def root():
    admin = get_admin_path()
    return HTMLResponse(
        f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex">
<title>AppStore</title>
<style>
body{{margin:0;min-height:100dvh;display:grid;place-items:center;font:15px/1.45 system-ui,sans-serif;
background:#0f1115;color:#e8eaed}}
.card{{max-width:420px;padding:28px;border:1px solid #2a2f3a;border-radius:16px;background:#171a21}}
a{{color:#8ab4f8}} h1{{margin:0 0 8px;font-size:22px}} p{{color:#9aa0a6;margin:0 0 16px}}
.btn{{display:inline-block;background:#01875f;color:#fff;text-decoration:none;padding:12px 18px;
border-radius:999px;font-weight:700}}
</style></head><body>
<div class="card">
<h1>AppStore</h1>
<p>Play-style APK share pages. Publish from the hidden console.</p>
<a class="btn" href="/{admin}">Open publisher</a>
<p style="margin-top:18px;font-size:12px">Public links look like <code>/s/&lt;slug&gt;</code></p>
</div></body></html>"""
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
