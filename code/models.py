"""
models.py
INTERide — OOP models: Vehicle hierarchy + Booking data-class.
"""

from typing import Dict, List, Optional, Tuple
import uuid
from datetime import datetime


# ══════════════════════════════════════════════════════════════════════════
#  VEHICLE  — base + concrete subclasses
# ══════════════════════════════════════════════════════════════════════════
class Vehicle:
    def __init__(
        self,
        vtype:   str,
        cap:     int,
        rate:    float,
        emoji:   str,
        tagline: str,
    ) -> None:
        self._vtype:   str   = vtype
        self._cap:     int   = cap
        self._rate:    float = rate
        self._emoji:   str   = emoji
        self._tagline: str   = tagline

    # ── read-only properties ──────────────────────────────────────────────
    @property
    def vtype(self)   -> str:   return self._vtype
    @property
    def cap(self)     -> int:   return self._cap
    @property
    def rate(self)    -> float: return self._rate
    @property
    def emoji(self)   -> str:   return self._emoji
    @property
    def tagline(self) -> str:   return self._tagline

    def calculate_cost(self, km: float) -> float:
        return round(self._rate * km, 2)

    def rate_desc(self) -> str:
        return f"₱{self._rate}/km"


class Car(Vehicle):
    def __init__(self) -> None:
        super().__init__("Car", 4, 15.0, "🚗", "Comfortable · 4 seats")

    def calculate_cost(self, km: float) -> float:
        return round(self._rate * km * (0.90 if km > 10 else 1.0), 2)


class Van(Vehicle):
    def __init__(self) -> None:
        super().__init__("Van", 10, 25.0, "🚐", "Spacious · 10 seats")

    def calculate_cost(self, km: float) -> float:
        return round(self._rate * km * 1.15, 2)


class Bike(Vehicle):
    def __init__(self) -> None:
        super().__init__("Bike", 1, 8.0, "🛵", "Fast · 1 rider")

    def calculate_cost(self, km: float) -> float:
        return round(self._rate * km + (5.0 if km < 2 else 0.0), 2)


# ── registry ──────────────────────────────────────────────────────────────
VEHICLES: List[Vehicle]        = [Car(), Van(), Bike()]
V_MAP:    Dict[str, Vehicle]   = {v.vtype: v for v in VEHICLES}


# ══════════════════════════════════════════════════════════════════════════
#  BOOKING
# ══════════════════════════════════════════════════════════════════════════
class Booking:
    def __init__(
        self,
        user:    str,
        vtype:   str,
        pickup:  str,
        dropoff: str,
        pc:      Tuple[float, float],
        dc:      Tuple[float, float],
        km:      float,
        bid:     Optional[str ] = None,
        ts:      Optional[str ] = None,
        status:  str            = "confirmed",
    ) -> None:
        self._bid:    str                  = bid or str(uuid.uuid4())[:8].upper()
        self._user:   str                  = user
        self._v:      Vehicle              = V_MAP[vtype]
        self._pick:   str                  = pickup
        self._drop:   str                  = dropoff
        self._pc:     Tuple[float, float]  = pc
        self._dc:     Tuple[float, float]  = dc
        self._km:     float                = round(km, 2)
        self._cost:   float                = self._v.calculate_cost(km)
        self._ts:     str                  = ts or datetime.now().strftime("%Y-%m-%d %H:%M")
        self._status: str                  = status

    # ── read-only properties ──────────────────────────────────────────────
    bid    = property(lambda s: s._bid)
    user   = property(lambda s: s._user)
    vtype  = property(lambda s: s._v.vtype)
    emoji  = property(lambda s: s._v.emoji)
    pick   = property(lambda s: s._pick)
    drop   = property(lambda s: s._drop)
    pc     = property(lambda s: s._pc)
    dc     = property(lambda s: s._dc)
    km     = property(lambda s: s._km)
    cost   = property(lambda s: s._cost)
    ts     = property(lambda s: s._ts)
    status = property(lambda s: s._status)

    def cancel(self) -> None:
        self._status = "cancelled"

    # ── serialisation ─────────────────────────────────────────────────────
    def to_dict(self) -> dict:
        return dict(
            bid     = self._bid,
            user    = self._user,
            vtype   = self._v.vtype,
            pickup  = self._pick,
            dropoff = self._drop,
            pc      = list(self._pc),
            dc      = list(self._dc),
            km      = self._km,
            cost    = self._cost,
            ts      = self._ts,
            status  = self._status,
        )

    @classmethod
    def from_dict(cls, d: dict) -> "Booking":
        return cls(
            d["user"], d["vtype"],
            d["pickup"], d["dropoff"],
            tuple(d["pc"]), tuple(d["dc"]),
            d["km"], bid=d["bid"], ts=d["ts"],
            status=d.get("status", "confirmed"),  # default for old bookings
        )
