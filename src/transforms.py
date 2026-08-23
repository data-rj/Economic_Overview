"""Level / YoY / Rate-of-Change (ITR Economics-style 3MMA & 12MMA) transforms."""
from __future__ import annotations

import numpy as np
import pandas as pd


def infer_periods_per_year(series: pd.Series) -> int:
    """Guess 52 (weekly), 12 (monthly), or 4 (quarterly) from the median index spacing."""
    if len(series) < 2:
        return 12
    median_days = series.index.to_series().diff().dropna().dt.days.median()
    if median_days > 60:
        return 4
    if median_days <= 10:
        return 52
    return 12


def yoy_pct_change(series: pd.Series) -> pd.Series:
    periods = infer_periods_per_year(series)
    return series.pct_change(periods=periods) * 100


def moving_average(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window, min_periods=window).mean()


def trailing_sum(series: pd.Series, window: int = 12) -> pd.Series:
    return series.rolling(window=window, min_periods=window).sum()


def annualized_pct_change(series: pd.Series) -> pd.Series:
    """Single-period % change compounded to an annual rate (SAAR-style) — e.g. for
    monthly index data: ((v_t / v_t-1) ** 12 - 1) * 100. Same convention BEA/BLS use
    for headline "monthly annualized" / quarterly-annualized inflation and growth
    figures."""
    periods = infer_periods_per_year(series)
    return ((series / series.shift(1)) ** periods - 1) * 100


def rate_of_change(series: pd.Series, short: bool) -> pd.Series:
    """ITR-style RoC: the YoY % change of a trailing moving average.

    `short=True` -> 3-period MA (3MMA monthly, 1-quarter MA quarterly, 13-week MA weekly).
    `short=False` -> 12-period MA (12MMA monthly, 4-quarter MA quarterly, 52-week MA weekly).
    """
    periods = infer_periods_per_year(series)
    if periods == 4:
        window = 1 if short else 4
    elif periods == 52:
        window = 13 if short else 52
    else:
        window = 3 if short else 12
    ma = moving_average(series, window)
    return ma.pct_change(periods=periods) * 100


def roc_pair(series: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Return (short RoC, long RoC) — the 3MMA/12MMA (or 1Q/4Q) pair."""
    return rate_of_change(series, short=True), rate_of_change(series, short=False)


def linear_forecast(series: pd.Series, lookback: int = 4, horizon: int = 2) -> pd.Series:
    """Extrapolate `horizon` future points via a least-squares line fit over the
    trailing `lookback` actual points. Index frequency (monthly/quarterly) is
    inferred from the series and extended forward accordingly."""
    clean = series.dropna()
    if len(clean) < lookback:
        return pd.Series(dtype=float)

    recent = clean.iloc[-lookback:]
    x = np.arange(lookback)
    slope, intercept = np.polyfit(x, recent.values, 1)
    future_x = np.arange(lookback, lookback + horizon)
    future_vals = slope * future_x + intercept

    periods = infer_periods_per_year(clean)
    step_months = 3 if periods == 4 else 1
    last_date = clean.index[-1]
    future_dates = [last_date + pd.DateOffset(months=step_months * (i + 1)) for i in range(horizon)]
    return pd.Series(future_vals, index=pd.DatetimeIndex(future_dates), name=series.name)
