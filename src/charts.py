"""Plotly chart builders — palette, mark specs, recession shading, and timeframe filtering.

Colors and chrome follow the dashboard-design reference palette: fixed
categorical hue order (never cycled/reassigned by filter), hairline
gridlines, muted axis ink, and a single shared y-axis per chart (no
dual-axis charts — series on very different scales use `index_to_100`
instead). Timeframe is controlled by a Streamlit dropdown (see
`TIMEFRAME_OPTIONS`) that slices the data server-side; charts have no
drag-zoom, pinch-zoom, or range slider — those were removed because
touch/trackpad zoom proved too easy to trigger by accident and hard to
reset. Legend entries carry the latest period and value for each series,
e.g. "Real GDP · Jun-26: 23,512.4".
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


def _clip(series: pd.Series, start_date: pd.Timestamp | None) -> pd.Series:
    return series[series.index >= start_date] if start_date is not None else series


def build_chart(
    series_map: dict[str, pd.Series],
    view: str,
    unit: str = "",
    index_to_100: bool = False,
    timeframe: str = "Max",
) -> go.Figure:
    """series_map: legend label -> level Series (already fetched from FRED)."""
    fig = go.Figure()
    non_empty = {label: s for label, s in series_map.items() if not s.empty}
    if not non_empty:
        return fig

    overall_end = max(s.index.max() for s in non_empty.values())
    years = _TIMEFRAME_YEARS.get(timeframe)
    start_date = (overall_end - pd.DateOffset(years=years)) if years else None

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

    display_start = start_date if start_date is not None else min(s.index.min() for s in non_empty.values())
    _add_recession_bands(fig, display_start, overall_end)

    if view == VIEW_ROC:
        fig.add_hline(y=0, line_color=AXIS, line_width=1)

    return _apply_layout(fig, y_title)
