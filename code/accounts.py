"""
accounts.py
INTERide — Account persistence: load and save user accounts to JSON.
"""

import json
import os
from typing import List, Optional

FILE: str = "accounts.json"


def load_accounts() -> List[dict]:
    """Load all accounts from FILE. Returns [] if missing or corrupt."""
    if not os.path.exists(FILE):
        return []
    try:
        with open(FILE) as f:
            return json.load(f)
    except Exception:
        return []


def save_accounts(accounts: List[dict]) -> None:
    """Save all accounts to FILE."""
    with open(FILE, "w") as f:
        json.dump(accounts, f, indent=2)


def find_account(username: str, password: str) -> Optional[dict]:
    """Return the account dict if username and password match, else None."""
    for acc in load_accounts():
        if acc["username"] == username and acc["password"] == password:
            return acc
    return None


def username_exists(username: str) -> bool:
    """Check if a username is already taken."""
    return any(acc["username"] == username for acc in load_accounts())