# PPstore — Play-style APK share pages (free hosting)

Standalone publisher: public `/s/<slug>` landings + hidden `/px-console`.

## Host chosen: **Render (free)**

| Option | Why not / why yes |
|--------|-------------------|
| **Render** ✅ | Free **Python web service** — this app needs FastAPI + APK upload (not static) |
| Netlify / Cloudflare Pages / GitHub Pages / Static.app | Static / Jamstack only — no durable FastAPI + multipart APK store |
| Coolify | Needs your own VPS (not free hosting by itself) |

Render free sleeps after idle (~15 min). First hit may take ~30–60s to wake.  
**Disk is ephemeral** on free: after sleep/redeploy, re-publish APKs from `/px-console`.

---

## Deploy (Render) — ~5 minutes

1. Push this folder to a **GitHub** repo (public or private).
2. Go to [https://dashboard.render.com](https://dashboard.render.com) → **New** → **Blueprint**  
   (or **Web Service** → connect repo).
3. Use included `render.yaml`, or manual settings:
   - **Root:** repo root  
   - **Runtime:** Python 3  
   - **Build:** `pip install -r requirements.txt`  
   - **Start:** `uvicorn app:app --host 0.0.0.0 --port $PORT --app-dir server`  
   - **Health:** `/health`
4. In **Environment**, set:
   - `PLAY_ADMIN_PASS` = strong password (required)
   - `PLAY_ADMIN_SECRET` = long random string  
   - `PLAY_ADMIN_PATH` = `px-console` (or rename the hidden path)  
   - `PLAY_COOKIE_SECURE` = `1`
5. Deploy → open `https://YOUR-APP.onrender.com/px-console` → publish APK → copy `/s/...` link.

---

## Local run

```bash
cd "D:\shopping store\PPstore"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
set PLAY_ADMIN_PASS=ssrg-play
uvicorn app:app --host 0.0.0.0 --port 8000 --app-dir server
```

- Home: http://127.0.0.1:8000/  
- Publisher: http://127.0.0.1:8000/px-console  
- Example share: http://127.0.0.1:8000/s/&lt;slug&gt;

---

## URLs

| Path | Purpose |
|------|---------|
| `/s/<slug>` | Play listing |
| `/s/<slug>/dl` | APK download |
| `/s/<slug>/icon` | Icon |
| `/px-console` | Password publisher (templates: Bloop, BingX, Amazon, Flipkart, …) |
| `/health` | Render health check |

---

## Env vars

| Var | Default | Notes |
|-----|---------|--------|
| `PLAY_ADMIN_PASS` | `ssrg-play` | **Change on Render** |
| `PLAY_ADMIN_SECRET` | auto file | Cookie HMAC secret |
| `PLAY_ADMIN_PATH` | `px-console` | Hidden admin URL |
| `PLAY_COOKIE_SECURE` | auto on Render | HTTPS cookies |
| `PLAY_SHARES_DIR` | `server/play_shares` | Optional custom data path |
