from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
VK_TOKEN = os.getenv("VK_TOKEN", "").strip()
GROUP_ID_RAW = os.getenv("GROUP_ID", "").strip()
DB_PATH = str((BASE_DIR / os.getenv("DB_PATH", "data/bot_data.sqlite3")).resolve())
DOCS_DIR = (BASE_DIR / os.getenv("DOCS_DIR", "data/generated_docs")).resolve()
MEDIA_DIR = (BASE_DIR / os.getenv("MEDIA_DIR", "data/media")).resolve()
ASSETS_DIR = (BASE_DIR / os.getenv("ASSETS_DIR", "assets")).resolve()
FONTS_DIR = (BASE_DIR / os.getenv("FONTS_DIR", "fonts")).resolve()
LOGO_PATH_RAW = os.getenv("LOGO_PATH", "").strip()
LOGO_PATH = Path(LOGO_PATH_RAW).resolve() if LOGO_PATH_RAW else (ASSETS_DIR / "tehnokom_placeholder.png")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

DOCS_DIR.mkdir(parents=True, exist_ok=True)
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
FONTS_DIR.mkdir(parents=True, exist_ok=True)

if not VK_TOKEN:
    raise RuntimeError("Не задан VK_TOKEN в .env")
if not GROUP_ID_RAW:
    raise RuntimeError("Не задан GROUP_ID в .env")
if not GROUP_ID_RAW.isdigit():
    raise RuntimeError(
        f"GROUP_ID должен быть числом, получено: {GROUP_ID_RAW!r}. "
        "Укажите только числовой ID группы VK."
    )
GROUP_ID = int(GROUP_ID_RAW)
