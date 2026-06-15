from typing import Dict, Optional
"""
config.py
INTERide — Palette, font, and optional-dependency flags.
Import C and F anywhere you need colours or the base font.
"""

# ── Optional deps ──────────────────────────────────────────────────────────
try:
    import tkintermapview as mapview          # noqa: F401
    HAS_MAP = True
except ImportError:
    HAS_MAP = False

try:
    import requests                            # noqa: F401
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from geopy.geocoders import Nominatim
    _gc = Nominatim(user_agent="interide_v2")
    HAS_GEO = True
except ImportError:
    HAS_GEO  = False
    _gc      = None

try:
    from docx import Document as DocxDoc      # noqa: F401
    from docx.shared import Pt, RGBColor, Cm  # noqa: F401
    from docx.enum.text import WD_ALIGN_PARAGRAPH   # noqa: F401
    from docx.enum.table import WD_TABLE_ALIGNMENT  # noqa: F401
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

# ══════════════════════════════════════════════════════════════════════════
#  PALETTE  — blue / white gradient feel
# ══════════════════════════════════════════════════════════════════════════
C: Dict[str, str] = {
    "bg"        : "#F0F4FF",   # soft blue-white background
    "surface"   : "#FFFFFF",
    "primary"   : "#2563EB",   # vivid blue
    "primary2"  : "#1D4ED8",   # darker blue
    "primary_lt": "#DBEAFE",   # light blue tint
    "accent"    : "#3B82F6",
    "text"      : "#0F172A",
    "muted"     : "#94A3B8",
    "border"    : "#E2E8F0",
    "white"     : "#FFFFFF",
    "danger"    : "#EF4444",
    "success"   : "#22C55E",
    "dark"      : "#0F172A",
    "card"      : "#F8FAFF",
    "grad_top"  : "#1E40AF",   # splash gradient top
    "grad_bot"  : "#2563EB",
}

F: str = "Helvetica"   # base font; swap to "Poppins" if installed
