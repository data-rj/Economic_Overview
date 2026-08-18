"""Thin client for the FRED (Federal Reserve Economic Data) API."""
from __future__ import annotations

import os
from datetime import date

import pandas as pd
import requests
import streamlit as st

FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"


def get_api_key() -> str | None:
    try:
        if "FRED_API_KEY" in st.secrets:
            return st.secrets["FRED_API_KEY"]
    except Exception:
        pass
    return os.environ.get("FRED_API_KEY")


@st.cache_data(ttl=60 * 60 * 12, show_spinner=False)
def fetch_series(series_id: str, start: str = "1990-01-01") -> pd.Series:
    """Fetch one FRED series as a date-indexed float Series. Empty Series on failure."""
    api_key = get_api_key()
    if not api_key:
        return pd.Series(dtype=float, name=series_id)

    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": start,
    }
    try:
        resp = requests.get(FRED_BASE_URL, params=params, timeout=15)
        resp.raise_for_status()
        obs = resp.json().get("observations", [])
    except (requests.RequestException, ValueError):
        return pd.Series(dtype=float, name=series_id)

    if not obs:
        return pd.Series(dtype=float, name=series_id)

    df = pd.DataFrame(obs)
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.set_index("date")["value"].rename(series_id).dropna()


@st.cache_data(ttl=60 * 60 * 12, show_spinner=False)
def fetch_recession_bands(start: str = "1990-01-01") -> list[tuple[date, date]]:
    """Return (start, end) date pairs where the NBER recession indicator (USREC) == 1."""
    rec = fetch_series("USREC", start=start)
    if rec.empty:
        return []

    bands: list[tuple[date, date]] = []
    in_recession = False
    band_start = None
    for dt, val in rec.items():
        if val >= 0.5 and not in_recession:
            in_recession = True
            band_start = dt
        elif val < 0.5 and in_recession:
            in_recession = False
            bands.append((band_start, dt))
    if in_recession:
        bands.append((band_start, rec.index[-1]))
    return bands
