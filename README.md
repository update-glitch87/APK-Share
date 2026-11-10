# AppStore — Play-style APK share pages

Public `/s/<slug>` landings + hidden `/px-console` publisher.

## Hosting (important)

This app needs **FastAPI + APK upload disk**. It is **not** a good fit for **Vercel / Netlify / Cloudflare Pages** (serverless, no durable APK storage, body/time limits).

| Host | Like Vercel? | Fit for AppStore |
|------|--------------|------------------|
| **Render free** | Same idea: connect repo → HTTPS URL | **Yes** (best free ongoing). Sleeps ~15 min idle. |
| Vercel Hobby | Closest UX | **No** for APK publisher |
| Railway | Similar | Trial expired on your account |
| Fly.io | CLI deploy | Trial-only ($1) — dropped |
| aft.page | Drop zip | Temp ~60 min unless claimed — dropped |

**Use Render free** with Public Git Repository (no GitHub App required):

1. https://dashboard.render.com/web/new → **Public Git Repository**
2. URL: `https://github.com/update-glitch87/APK-Share`
3. Branch: `ppstore`
4. Build: `pip install -r requirements.txt`
5. Start: `uvicorn app:app --host 0.0.0.0 --port $PORT --app-dir server`
6. Health: `/health`
7. Env: `PLAY_ADMIN_PASS`, `PLAY_ADMIN_SECRET`, `PLAY_COOKIE_SECURE=1`, `PLAY_ADMIN_PATH=px-console`

Or use Blueprint from `render.yaml`.

## Local run

```bash
cd "D:\shopping store\PPstore"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
set PLAY_ADMIN_PASS=changeme
uvicorn app:app --host 0.0.0.0 --port 8000 --app-dir server
```

- Home: http://127.0.0.1:8000/
- Publisher: http://127.0.0.1:8000/px-console
