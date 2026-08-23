"""Plotly chart builders — palette, mark specs, recession shading, and timeframe filtering.

Colors and chrome follow the dashboard-design reference palette: fixed
categorical hue order (never cycled/reassigned by filter), hairline
gridlines, muted axis ink, and a single shared y-axis per chart (no
dual-axis charts — series on very different scales use `index_to_100`
instead).

Timeframe is controlled by a Streamlit dropdown (`TIMEFRAME_OPTIONS`) rather
than Plotly's native range slider/selector. Two reasons: the native slider's
drag/pinch zoom proved too easy to trigger by accident and hard to reset,
and — more fundamentally — Plotly's client-side zoom never reaches this
Python code, so the y-axis stays fixed to the full-history min/max no
matter what window you zoom into. Because the dropdown is a real Streamlit
widget, selecting a timeframe reruns this code with the data already
sliced, so the y-axis autoranges to fit whatever window is selected. Charts
have no drag-zoom, pinch-zoom, or range slider — hover tooltips still work.
Legend entries carry the latest period and value for each series, e.g.
"Real GDP · Jun-26: 23,512.4" — always the true latest point, regardless of
the selected timeframe.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from . import transforms
from .fred import fetch_recession_bands

CATEGORICAL = [
    "#2a78d6",  # blue
    "#eb6834",  # orange
    "#1baf7a",  # aqua
    "#eda100",  # yellow
    "#e87ba4",  # magenta
    "#008300",  # green
    "#4a3aa7",  # violet
    "#e34948",  # red
]
GRIDLINE = "#e1e0d9"
AXIS = "#c3c2b7"
MUTED = "#898781"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
SURFACE = "#fcfcfb"
RECESSION_BAND = "rgba(11, 11, 11, 0.06)"

VIEW_LEVEL = "Level"
VIEW_YOY = "YoY %"
VIEW_ROC = "RoC (3/12 MMA)"
VIEWS = [VIEW_LEVEL, VIEW_YOY, VIEW_ROC]

TIMEFRAME_OPTIONS = ["1Y", "5Y", "10Y", "20Y", "Max"]
_TIMEFRAME_YEARS = {"1Y": 1, "5Y": 5, "10Y": 10, "20Y": 20, "Max": None}


def _format_last_point(series: pd.Series, is_percent: bool) -> str:
    clean = series.dropna()
    if clean.empty:
        return ""
    period = clean.index[-1].strftime("%b-%y")
    val = clean.iloc[-1]
    if is_percent:
        val_str = f"{val:.1f}%"
    elif abs(val) < 10:
        val_str = f"{val:,.2f}"
    else:
        val_str = f"{val:,.1f}"
    return f"{period}: {val_str}"


def _legend_name(label: str, series: pd.Series, is_percent: bool) -> str:
    suffix = _format_last_point(series, is_percent)
    return f"{label} · {suffix}" if suffix else label


def _clip(series: pd.Series, start_date: pd.Timestamp | None) -> pd.Series:
    return series[series.index >= start_date] if start_date is not None else series


def _timeframe_start(overall_end: pd.Timestamp, timeframe: str) -> pd.Timestamp | None:
    years = _TIMEFRAME_YEARS.get(timeframe)
    return (overall_end - pd.DateOffset(years=years)) if years else None


def _apply_layout(fig: go.Figure, y_title: str) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        plot_bgcolor=SURFACE,
        paper_bgcolor=SURFACE,
        font=dict(color=INK_PRIMARY, family="system-ui, -apple-system, Segoe UI, sans-serif"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(color=INK_SECONDARY)),
        margin=dict(l=10, r=10, t=10, b=10),
        hovermode="x unified",
        dragmode=False,
    )
    fig.update_xaxes(showgrid=False, linecolor=AXIS, tickfont=dict(color=MUTED), fixedrange=True)
    fig.update_yaxes(
        showgrid=True,
        gridcolor=GRIDLINE,
        zeroline=False,
        title=y_title,
        tickfont=dict(color=MUTED),
        title_font=dict(color=MUTED),
        fixedrange=True,
    )
    return fig


def _add_recession_bands(fig: go.Figure, start: pd.Timestamp, end: pd.Timestamp) -> None:
    for band_start, band_end in fetch_recession_bands(start=str(start.date())):
        if band_end < start or band_start > end:
            continue
        fig.add_vrect(x0=band_start, x1=band_end, fillcolor=RECESSION_BAND, line_width=0, layer="below")


def build_chart(
    series_map: dict[str, pd.Series],
    view: str,
    unit: str = "",
    index_to_100: bool = False,
    timeframe: str = "Max",
    forecast: bool = False,
) -> go.Figure:
    """series_map: legend label -> level Series (already fetched from FRED)."""
    fig = go.Figure()
    non_empty = {label: s for label, s in series_map.items() if not s.empty}
    if not non_empty:
        return fig

    overall_end = max(s.index.max() for s in non_empty.values())
    start_date = _timeframe_start(overall_end, timeframe)

    is_pct_unit = "%" in unit
    y_title = unit
    for i, (label, s) in enumerate(non_empty.items()):
        color = CATEGORICAL[i % len(CATEGORICAL)]

        if view == VIEW_YOY:
            plotted = transforms.yoy_pct_change(s)
            y_title = "YoY % change"
            name = _legend_name(label, plotted, is_percent=True)
            visible = _clip(plotted, start_date)
            fig.add_trace(go.Scatter(x=visible.index, y=visible.values, name=name, line=dict(color=color, width=2)))
            continue

        if view == VIEW_ROC:
            short, long = transforms.roc_pair(s)
            y_title = "YoY % change of moving average"
            short_name = _legend_name(f"{label} — 3MMA RoC", short, is_percent=True)
            long_name = _legend_name(f"{label} — 12MMA RoC", long, is_percent=True)
            short_visible, long_visible = _clip(short, start_date), _clip(long, start_date)
            fig.add_trace(go.Scatter(
                x=short_visible.index, y=short_visible.values, name=short_name, line=dict(color=color, width=2),
            ))
            fig.add_trace(go.Scatter(
                x=long_visible.index, y=long_visible.values, name=long_name,
                line=dict(color=color, width=2, dash="dot"),
            ))
            continue

        plotted = s
        if index_to_100 and len(s) > 0:
            plotted = s / s.iloc[0] * 100
            y_title = "Index (start = 100)"
        name = _legend_name(label, plotted, is_percent=is_pct_unit and not index_to_100)
        visible = _clip(plotted, start_date)
        fig.add_trace(go.Scatter(x=visible.index, y=visible.values, name=name, line=dict(color=color, width=2)))

        if forecast and not index_to_100:
            fc = transforms.linear_forecast(s, lookback=4, horizon=2)
            if not fc.empty:
                connector = pd.concat([s.iloc[[-1]], fc])
                fig.add_trace(go.Scatter(
                    x=connector.index, y=connector.values,
                    name=_legend_name(f"{label} — Forecast", fc, is_percent=is_pct_unit),
                    line=dict(color=color, width=2, dash="dash"),
                ))

    display_start = start_date if start_date is not None else min(s.index.min() for s in non_empty.values())
    _add_recession_bands(fig, display_start, overall_end)

    if view == VIEW_ROC:
        fig.add_hline(y=0, line_color=AXIS, line_width=1)

    return _apply_layout(fig, y_title)


def build_contribution_chart(
    component_series: dict[str, pd.Series],
    gdp_level: pd.Series,
    timeframe: str = "Max",
) -> go.Figure:
    """Stacked-bar approximation of each component's contribution to real GDP growth.

    contribution_i(t) ≈ (component_i(t) - component_i(t-1)) / GDP(t-1) * 400 — a
    first-order approximation of BEA's official chain-weighted methodology, computed
    from already-fetched level series rather than a separate pre-built NIPA series.
    """
    fig = go.Figure()
    if gdp_level.empty:
        return fig
    gdp_prior = gdp_level.shift(1)

    contributions: dict[str, pd.Series] = {}
    for label, s in component_series.items():
        if s.empty:
            continue
        s_aligned, gdp_aligned = s.align(gdp_prior, join="inner")
        contributions[label] = ((s_aligned - s_aligned.shift(1)) / gdp_aligned * 400).dropna()

    non_empty = {label: c for label, c in contributions.items() if not c.empty}
    if not non_empty:
        return fig

    overall_end = max(c.index.max() for c in non_empty.values())
    start_date = _timeframe_start(overall_end, timeframe)

    total = None
    for i, (label, c) in enumerate(non_empty.items()):
        color = CATEGORICAL[i % len(CATEGORICAL)]
        name = _legend_name(label, c, is_percent=True)
        visible = _clip(c, start_date)
        fig.add_trace(go.Bar(x=visible.index, y=visible.values, name=name, marker_color=color))
        total = c if total is None else total.add(c, fill_value=0)

    if total is not None:
        total_name = _legend_name("Total (approx.)", total, is_percent=True)
        visible_total = _clip(total, start_date)
        fig.add_trace(go.Scatter(
            x=visible_total.index, y=visible_total.values, name=total_name,
            mode="lines", line=dict(color=INK_PRIMARY, width=2),
        ))
        display_start = start_date if start_date is not None else total.index.min()
        _add_recession_bands(fig, display_start, overall_end)

    fig.add_hline(y=0, line_color=AXIS, line_width=1)
    fig.update_layout(barmode="relative")
    return _apply_layout(fig, "Percentage points (annualized)")


def build_potential_gdp_chart(
    actual_gdp: pd.Series,
    productivity: pd.Series,
    labor_force: pd.Series,
    timeframe: str = "Max",
) -> go.Figure:
    """Potential GDP, estimated via the standard two-factor growth-accounting
    identity: since GDP = Labor Productivity x Labor Input, g(GDP) ~= g(Productivity)
    + g(Labor Input). Substituting an 8-quarter trailing-average ("trend") growth
    rate for each factor in place of the noisy actual quarterly growth rate turns
    this from an actual-GDP identity into a potential-GDP estimate — the same
    simplified two-factor framework CBO and standard macro texts describe (capital
    deepening and TFP are folded into the productivity trend here rather than
    modeled separately). The result is compounded forward from a base level equal
    to actual GDP at the first date the trend is computable, so it starts calibrated
    to actual GDP and then diverges — the shaded band is the implied output gap.
    """
    fig = go.Figure()
    if actual_gdp.empty or productivity.empty or labor_force.empty:
        return fig

    prod_trend = productivity.pct_change(1).rolling(8, min_periods=8).mean()
    labor_trend = labor_force.pct_change(1).rolling(8, min_periods=8).mean()

    combined = pd.DataFrame({"prod": prod_trend, "labor": labor_trend, "gdp": actual_gdp}).dropna()
    if combined.empty:
        return fig

    potential_growth = combined["prod"] + combined["labor"]
    growth_factors = 1 + potential_growth
    cum = growth_factors.cumprod()
    potential = combined["gdp"].iloc[0] * cum / cum.iloc[0]
    potential.name = "Potential GDP"

    overall_end = max(actual_gdp.index.max(), potential.index.max())
    start_date = _timeframe_start(overall_end, timeframe)

    potential_visible = _clip(potential, start_date)
    actual_visible = _clip(actual_gdp, start_date)

    fig.add_trace(go.Scatter(
        x=potential_visible.index, y=potential_visible.values,
        name=_legend_name("Potential GDP (est.)", potential, is_percent=False),
        line=dict(color=CATEGORICAL[1], width=2, dash="dash"),
    ))
    fig.add_trace(go.Scatter(
        x=actual_visible.index, y=actual_visible.values,
        name=_legend_name("Real GDP (actual)", actual_gdp, is_percent=False),
        line=dict(color=CATEGORICAL[0], width=2),
        fill="tonexty", fillcolor="rgba(11, 11, 11, 0.05)",
    ))

    display_start = start_date if start_date is not None else min(actual_gdp.index.min(), potential.index.min())
    _add_recession_bands(fig, display_start, overall_end)

    return _apply_layout(fig, "$ billions (2017 chained)")
