"""
riders.py
INTERide — Rider pool: a fixed list of available drivers
randomly assigned after a booking is confirmed.
"""

import random
from typing import Optional


# ── Rider pool ────────────────────────────────────────────────────────────
RIDERS: list = [
    {
        "name":   "Charles Ilagan",
        "photo":  "Charles.jpg",
        "phone":  "+63 912 345 6789",
        "rating": "4.9 ⭐",
    },
    {
        "name":   "Coco Martin",
        "photo":  "Coco.jpg",
        "phone":  "+63 917 234 5678",
        "rating": "4.8 ⭐",
    },
    {
        "name":   "Robin Padilla",
        "photo":  "Robin.jpg",
        "phone":  "+63 918 345 6790",
        "rating": "4.7 ⭐",
    },
    {
        "name":   "Wally Bayola",
        "photo":  "Wally.jpg",
        "phone":  "+63 919 456 7891",
        "rating": "5.0 ⭐",
    },
]


def assign_rider() -> dict:
    """Randomly pick and return a rider from the pool."""
    return random.choice(RIDERS)