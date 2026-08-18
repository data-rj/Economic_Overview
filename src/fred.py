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
def _fetch_series_raw(series_id: str, start: str = "1990-01-01") -> tuple[pd.Series, str]:
    """Fetch one FRED series. Returns (series, error_message) — error_message is '' on success."""
    empty = pd.Series(dtype=float, name=series_id)
    api_key = get_api_key()
    if not api_key:
        return empty, "No FRED_API_KEY configured."

    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": start,
    }
    try:
        resp = requests.get(FRED_BASE_URL, params=params, timeout=15)
        resp.raise_for_status()
    except requests.HTTPError as e:
        detail = ""
        if e.response is not None:
            try:
                detail = e.response.json().get("error_message", "")
            except ValueError:
                detail = e.response.text[:200]
        status = e.response.status_code if e.response is not None else "?"
        return empty, f"HTTP {status}: {detail or e}"
    except requests.RequestException as e:
        return empty, f"Request failed: {e}"

    try:
        payload = resp.json()
    except ValueError as e:
        return empty, f"Could not parse FRED response: {e}"

    obs = payload.get("observations", [])
    if not obs:
        return empty, "FRED returned zero observations for this series/date range."

    df = pd.DataFrame(obs)
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    series = df.set_index("date")["value"].rename(series_id).dropna()
    if series.empty:
        return empty, "All observations were missing/non-numeric (FRED uses '.' for missing values)."
    return series, ""


def fetch_series(series_id: str, start: str = "1990-01-01") -> pd.Series:
    return _fetch_series_raw(series_id, start)[0]


def fetch_series_error(series_id: str, start: str = "1990-01-01") -> str:
    """Reason the last fetch of this series returned no data. Empty string on success."""
    return _fetch_series_raw(series_id, start)[1]


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
