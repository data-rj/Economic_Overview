"""Level / YoY / Rate-of-Change (ITR Economics-style 3MMA & 12MMA) transforms."""
from __future__ import annotations

import pandas as pd


def infer_periods_per_year(series: pd.Series) -> int:
    """Guess 12 (monthly) or 4 (quarterly) from the median spacing of the index."""
    if len(series) < 2:
        return 12
    median_days = series.index.to_series().diff().dropna().dt.days.median()
    return 4 if median_days > 60 else 12


def yoy_pct_change(series: pd.Series) -> pd.Series:
    periods = infer_periods_per_year(series)
    return series.pct_change(periods=periods) * 100


def moving_average(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window, min_periods=window).mean()


def rate_of_change(series: pd.Series, short: bool) -> pd.Series:
    """ITR-style RoC: the YoY % change of a trailing moving average.

    `short=True` -> 3-period MA (3MMA monthly, 1-quarter MA quarterly).
    `short=False` -> 12-period MA (12MMA monthly, 4-quarter MA quarterly).
    """
    periods = infer_periods_per_year(series)
    window = (1 if periods == 4 else 3) if short else (4 if periods == 4 else 12)
    ma = moving_average(series, window)
    return ma.pct_change(periods=periods) * 100


def roc_pair(series: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Return (short RoC, long RoC) — the 3MMA/12MMA (or 1Q/4Q) pair."""
    return rate_of_change(series, short=True), rate_of_change(series, short=False)
