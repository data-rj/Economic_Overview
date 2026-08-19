"""Plotly chart builders — palette, mark specs, recession shading, and timeframe controls.

Colors and chrome follow the dashboard-design reference palette: fixed
categorical hue order (never cycled/reassigned by filter), hairline
gridlines, muted axis ink, and a single shared y-axis per chart (no
dual-axis charts — series on very different scales use `index_to_100`
instead). Each chart ships Plotly's native range-selector buttons (1Y/5Y/
10Y/20Y/Max) plus a range slider so the timeframe is adjustable per chart
without extra Streamlit widgets. Legend entries carry the latest period and
value for each series, e.g. "Real GDP · Jun-26: 23,512.4".
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
SELECTOR_ACTIVE = "#cde2fb"
RECESSION_BAND = "rgba(11, 11, 11, 0.06)"

VIEW_LEVEL = "Level"
VIEW_YOY = "YoY %"
VIEW_ROC = "RoC (3/12 MMA)"
VIEWS = [VIEW_LEVEL, VIEW_YOY, VIEW_ROC]


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
    )
    fig.update_xaxes(
        showgrid=False,
        linecolor=AXIS,
        tickfont=dict(color=MUTED),
        rangeslider=dict(visible=True, thickness=0.08, bgcolor=SURFACE, bordercolor=GRIDLINE, borderwidth=1),
        rangeselector=dict(
            buttons=[
                dict(count=1, label="1Y", step="year", stepmode="backward"),
                dict(count=5, label="5Y", step="year", stepmode="backward"),
                dict(count=10, label="10Y", step="year", stepmode="backward"),
                dict(count=20, label="20Y", step="year", stepmode="backward"),
                dict(step="all", label="Max"),
            ],
            bgcolor=SURFACE,
            activecolor=SELECTOR_ACTIVE,
            bordercolor=GRIDLINE,
            borderwidth=1,
            font=dict(color=INK_SECONDARY),
        ),
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=GRIDLINE,
        zeroline=False,
        title=y_title,
        tickfont=dict(color=MUTED),
        title_font=dict(color=MUTED),
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
) -> go.Figure:
    """series_map: legend label -> level Series (already fetched from FRED)."""
    fig = go.Figure()
    non_empty = {label: s for label, s in series_map.items() if not s.empty}
    if not non_empty:
        return fig

    is_pct_unit = "%" in unit
    y_title = unit
    for i, (label, s) in enumerate(non_empty.items()):
        color = CATEGORICAL[i % len(CATEGORICAL)]

        if view == VIEW_YOY:
            plotted = transforms.yoy_pct_change(s)
            y_title = "YoY % change"
            fig.add_trace(go.Scatter(
                x=plotted.index, y=plotted.values, name=_legend_name(label, plotted, is_percent=True),
                line=dict(color=color, width=2),
            ))
            continue

        if view == VIEW_ROC:
            short, long = transforms.roc_pair(s)
            y_title = "YoY % change of moving average"
            fig.add_trace(go.Scatter(
                x=short.index, y=short.values,
                name=_legend_name(f"{label} — 3MMA RoC", short, is_percent=True),
                line=dict(color=color, width=2),
            ))
            fig.add_trace(go.Scatter(
                x=long.index, y=long.values,
                name=_legend_name(f"{label} — 12MMA RoC", long, is_percent=True),
                line=dict(color=color, width=2, dash="dot"),
            ))
            continue

        plotted = s
        if index_to_100 and len(s) > 0:
            plotted = s / s.iloc[0] * 100
            y_title = "Index (start = 100)"
        fig.add_trace(go.Scatter(
            x=plotted.index, y=plotted.values,
            name=_legend_name(label, plotted, is_percent=is_pct_unit and not index_to_100),
            line=dict(color=color, width=2),
        ))

    all_x = [s.index for s in non_empty.values() if not s.empty]
    if all_x:
        start = min(idx.min() for idx in all_x)
        end = max(idx.max() for idx in all_x)
        _add_recession_bands(fig, start, end)

    if view == VIEW_ROC:
        fig.add_hline(y=0, line_color=AXIS, line_width=1)

    return _apply_layout(fig, y_title)


def build_contribution_chart(component_series: dict[str, pd.Series], gdp_level: pd.Series) -> go.Figure:
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

    total = None
    for i, (label, c) in enumerate(non_empty.items()):
        color = CATEGORICAL[i % len(CATEGORICAL)]
        fig.add_trace(go.Bar(x=c.index, y=c.values, name=_legend_name(label, c, is_percent=True), marker_color=color))
        total = c if total is None else total.add(c, fill_value=0)

    if total is not None:
        fig.add_trace(go.Scatter(
            x=total.index, y=total.values, name=_legend_name("Total (approx.)", total, is_percent=True),
            mode="lines", line=dict(color=INK_PRIMARY, width=2),
        ))
        _add_recession_bands(fig, total.index.min(), total.index.max())

    fig.add_hline(y=0, line_color=AXIS, line_width=1)
    fig.update_layout(barmode="relative")
    return _apply_layout(fig, "Percentage points (annualized)")
