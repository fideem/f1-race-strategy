"""Minimal OpenF1 API client with an on-disk cache.

OpenF1 is rate-limited, and notebooks and tests often request the same data,
so every response is saved to data/raw/<endpoint>/<params-hash>.json and read
from disk on subsequent calls.

Uses requests rather than pd.read_json, which ran into SSL issues on macOS.
"""

import hashlib
import json
import time
from pathlib import Path

import pandas as pd
import requests

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

BASE_URL = "https://api.openf1.org/v1"
RAW_DIR = DATA_DIR / "raw"

# Endpoints used by this project (guards against typos in endpoint names).
ALLOWED_ENDPOINTS = {
    "meetings",
    "sessions",
    "drivers",
    "laps",
    "stints",
    "pit",
    "weather",
    "race_control",
    "position",
    "session_result",
}

_MIN_SECONDS_BETWEEN_CALLS = 2.1
_last_call = 0.0


def _cache_path(endpoint: str, params: dict) -> Path:
    key = json.dumps(params, sort_keys=True, default=str)
    digest = hashlib.sha1(key.encode()).hexdigest()[:16]
    return RAW_DIR / endpoint / f"{digest}.json"


def fetch(endpoint: str, use_cache: bool = True, **params) -> pd.DataFrame:
    """Fetch data from an OpenF1 endpoint and return it as a DataFrame.

    Example: fetch("laps", session_key=9693, driver_number=4)
    """
    global _last_call
    if endpoint not in ALLOWED_ENDPOINTS:
        raise ValueError(f"Unknown endpoint '{endpoint}'. Allowed: {sorted(ALLOWED_ENDPOINTS)}")

    path = _cache_path(endpoint, params)
    if use_cache and path.exists():
        return pd.DataFrame(json.loads(path.read_text()))

    for attempt in range(6):
        wait = _MIN_SECONDS_BETWEEN_CALLS - (time.monotonic() - _last_call)
        if wait > 0:
            time.sleep(wait)
        _last_call = time.monotonic()
        resp = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=30)
        if resp.status_code == 429:  # rate limited: back off and retry
            time.sleep(5*2 ** attempt)
            continue
        if resp.status_code == 404:  # OpenF1 returns 404 when nothing matches
            records = []
            break
        resp.raise_for_status()
        records = resp.json()
        break
    else:
        raise RuntimeError(f"OpenF1 still returning 429 for {endpoint} {params}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records))
    return pd.DataFrame(records)
