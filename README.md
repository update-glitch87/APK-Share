# AppStore — Play-style APK share pages

Public `/s/<slug>` landings + hidden `/px-console` publisher.

## Host on **Vercel** (recommended path)

Import this repo at [https://vercel.com/new](https://vercel.com/new).

| Setting | Value |
|---------|--------|
| Repo | `update-glitch87/APK-Share` |
| Branch | `ppstore` |
| Framework | FastAPI (auto) |
| Entrypoint | `vercel_entry:app` (in `pyproject.toml`) |
| Root | repo root (`.`) |

### Environment variables (Vercel → Settings → Environment Variables)

| Key | Value |
|-----|--------|
| `PLAY_ADMIN_PASS` | your publisher password |
| `PLAY_ADMIN_SECRET` | long random string |
| `PLAY_ADMIN_PATH` | `px-console` |
| `PLAY_COOKIE_SECURE` | `1` |

Optional: `PLAY_SHARES_DIR=/tmp/appstore_shares` (default on Vercel anyway).

### Limits (important)

- Vercel functions are **serverless**. Uploaded APKs live under `/tmp` and can **reset on cold starts**.
- Very large APK uploads may hit request body limits — keep APKs smaller when possible.
- After idle, first request may be slower (cold start).

### CLI deploy (optional)

```bash
npm i -g vercel
vercel login
vercel --prod
```

---

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

---

## Also works on Render

See `render.yaml` if you prefer a free always-ish Python web service (sleeps after idle).
