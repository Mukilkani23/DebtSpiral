"""
Server-side tier configuration: category -> tier (1/2/3), and the Tier 1/2/3
split ratios used by the extra-funds allocation engine.

Mirrors session_store.py's pattern: the JSON file is read-once seed data;
runtime mutations (POST /config/tiers) live in memory only and reset()
restores from the in-memory baseline captured at load time. This avoids
rewriting the checked-in seed file on every demo session, consistent with
how personas.json is never rewritten by transaction mutations.

Not on the PURE list (features.py/loop_detector.py/rules.py/simulator.py) —
I/O at load time is allowed here.
"""

import json
import copy
from pathlib import Path

DEFAULT_CATEGORY_TIERS: dict[str, int] = {
    "food_delivery": 3, "shopping": 3, "entertainment": 3,
    "travel": 2, "electronics": 2, "subscription": 2, "other": 2,
}
DEFAULT_EXTRA_FUNDS_RATIOS: dict[str, float] = {"1": 0.6, "2": 0.3, "3": 0.1}

_config: dict = {
    "category_tiers": dict(DEFAULT_CATEGORY_TIERS),
    "extra_funds_ratios": dict(DEFAULT_EXTRA_FUNDS_RATIOS),
}
_baseline: dict = copy.deepcopy(_config)


def load(path: str) -> None:
    global _config, _baseline
    p = Path(path)
    if p.exists():
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        seed = {
            "category_tiers": data.get("category_tiers", dict(DEFAULT_CATEGORY_TIERS)),
            "extra_funds_ratios": data.get("extra_funds_ratios", dict(DEFAULT_EXTRA_FUNDS_RATIOS)),
        }
    else:
        seed = {
            "category_tiers": dict(DEFAULT_CATEGORY_TIERS),
            "extra_funds_ratios": dict(DEFAULT_EXTRA_FUNDS_RATIOS),
        }
    _config = copy.deepcopy(seed)
    _baseline = copy.deepcopy(seed)


def get_config() -> dict:
    return copy.deepcopy(_config)


def get_tier(category: str) -> int:
    return _config["category_tiers"].get(category, 2)


def update_config(category_tiers: dict | None, extra_funds_ratios: dict | None) -> dict:
    if category_tiers is not None:
        for cat, tier in category_tiers.items():
            if tier not in (1, 2, 3):
                raise ValueError(f"Invalid tier {tier} for category '{cat}'; must be 1, 2, or 3")
        _config["category_tiers"] = {**_config["category_tiers"], **category_tiers}

    if extra_funds_ratios is not None:
        for tier_key in extra_funds_ratios:
            if tier_key not in ("1", "2", "3"):
                raise ValueError(f"Invalid tier key '{tier_key}'; must be '1', '2', or '3'")
        total = sum(extra_funds_ratios.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"extra_funds_ratios must sum to 1.0, got {total}")
        _config["extra_funds_ratios"] = dict(extra_funds_ratios)

    return get_config()


def reset() -> None:
    global _config
    _config = copy.deepcopy(_baseline)
