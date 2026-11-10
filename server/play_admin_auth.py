"""Password + cookie auth for the hidden Play publish console."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
from pathlib import Path
from typing import Optional, Tuple

SERVER_DIR = Path(__file__).resolve().parent
COOKIE_NAME = "px_admin"
SESSION_TTL = 60 * 60 * 12  # 12 hours

DEFAULT_PATH = "px-console"
DEFAULT_PASS = "ssrg-play"


def _admin_cfg_path() -> Path:
    override = (os.getenv("PLAY_SHARES_DIR") or "").strip()
    base = Path(override) if override else (SERVER_DIR / "play_shares")
    base.mkdir(parents=True, exist_ok=True)
    return base / "_admin.json"


def _load_cfg() -> dict:
    cfg_path = _admin_cfg_path()
    if cfg_path.is_file():
        try:
            return json.loads(cfg_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    cfg = {
        "path": os.getenv("PLAY_ADMIN_PATH", DEFAULT_PATH).strip().strip("/") or DEFAULT_PATH,
        "password_salt": secrets.token_hex(16),
        "password_hash": "",
        "cookie_secret": secrets.token_hex(32),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    plain = os.getenv("PLAY_ADMIN_PASS", DEFAULT_PASS)
    cfg["password_hash"] = _hash_password(plain, cfg["password_salt"])
    _save_cfg(cfg)
    return cfg


def _save_cfg(cfg: dict) -> None:
    cfg_path = _admin_cfg_path()
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def get_admin_path() -> str:
    env = (os.getenv("PLAY_ADMIN_PATH") or "").strip().strip("/")
    if env:
        return env
    return (_load_cfg().get("path") or DEFAULT_PATH).strip().strip("/")


def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()


def verify_password(password: str) -> bool:
    cfg = _load_cfg()
    # Env override always wins (lab rotate without editing file)
    env_pass = os.getenv("PLAY_ADMIN_PASS")
    if env_pass is not None and env_pass != "":
        return hmac.compare_digest(password, env_pass)
    expected = cfg.get("password_hash") or ""
    salt = cfg.get("password_salt") or ""
    got = _hash_password(password, salt)
    return hmac.compare_digest(got, expected)


def set_password(password: str) -> None:
    cfg = _load_cfg()
    if not cfg.get("password_salt"):
        cfg["password_salt"] = secrets.token_hex(16)
    cfg["password_hash"] = _hash_password(password, cfg["password_salt"])
    _save_cfg(cfg)


def _cookie_secret() -> bytes:
    env = os.getenv("PLAY_ADMIN_SECRET", "").strip()
    if env:
        return env.encode("utf-8")
    cfg = _load_cfg()
    return (cfg.get("cookie_secret") or secrets.token_hex(32)).encode("utf-8")


def issue_session_cookie() -> Tuple[str, dict]:
    exp = int(time.time()) + SESSION_TTL
    payload = f"ok|{exp}"
    sig = hmac.new(_cookie_secret(), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    value = f"{payload}|{sig}"
    # Secure cookies on HTTPS hosts (Render / Cloudflare)
    secure_env = (
        os.getenv("PLAY_COOKIE_SECURE")
        or os.getenv("RENDER")
        or os.getenv("VERCEL")
        or ""
    ).strip().lower()
    secure = secure_env in ("1", "true", "yes", "on") or bool(
        os.getenv("RENDER") or os.getenv("VERCEL") or os.getenv("VERCEL_ENV")
    )
    headers = {
        "httponly": True,
        "samesite": "lax",
        "path": "/",
        "max_age": SESSION_TTL,
        "secure": secure,
    }
    return value, headers


def validate_session_cookie(value: Optional[str]) -> bool:
    if not value or value.count("|") != 2:
        return False
    try:
        status, exp_s, sig = value.split("|", 2)
        exp = int(exp_s)
    except Exception:
        return False
    if status != "ok" or exp < int(time.time()):
        return False
    payload = f"{status}|{exp}"
    expect = hmac.new(_cookie_secret(), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(sig, expect)


# Ensure config exists at import so password file is ready for the operator.
_load_cfg()
