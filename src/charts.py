"""Plotly chart builders — palette, mark specs, recession shading, and timeframe filtering.

Colors and chrome follow the dashboard-design reference palette: fixed
categorical hue order (never cycled/reassigned by filter), hairline
gridlines, muted axis ink, and a single shared y-axis per chart — series on
very different scales use `index_to_100` instead of a second axis. The one
deliberate exception is `build_dual_axis_chart`, used only where indexing
genuinely doesn't work (a signed flow like the deficit can't be indexed
against an always-positive ratio like debt-to-GDP, since indexing assumes
a meaningful non-zero base).

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
VIEW_MOM_SAAR = "Monthly Annualized %"
VIEWS = [VIEW_LEVEL, VIEW_YOY, VIEW_ROC]
INFLATION_VIEWS = [VIEW_LEVEL, VIEW_YOY, VIEW_MOM_SAAR]

TIMEFRAME_OPTIONS = ["1Y", "5Y", "10Y", "20Y", "Max"]
_TIMEFRAME_YEARS = {"1Y": 1, "5Y": 5, "10Y": 10, "20Y": 20, "Max": None}


def _format_value(val: float, is_percent: bool) -> str:
    if is_percent:
        return f"{val:.1f}%"
    if abs(val) < 10:
        return f"{val:,.2f}"
    return f"{val:,.1f}"


def _format_last_point(series: pd.Series, is_percent: bool) -> str:
    clean = series.dropna()
    if clean.empty:
        return ""
    period = clean.index[-1].strftime("%b-%y")
    return f"{period}: {_format_value(clean.iloc[-1], is_percent)}"


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
    forecast_lookback: int = 4,
    forecast_horizon: int = 2,
    show_average: bool = False,
    percent_labels: tuple[str, ...] = (),
    forecast_from_level: pd.Series | None = None,
) -> go.Figure:
    """series_map: legend label -> level Series (already fetched from FRED).

    `forecast_from_level`, when given, derives the forecast from this LEVEL
    series (via transforms.derive_annualized_rate_forecast) instead of running
    linear_forecast directly on the chart's own series — for a rate chart whose
    forecast should stay consistent with a companion level chart's forecast
    (e.g. Real GDP Growth derived from the Real GDP level forecast).

    `percent_labels` overrides the unit-string percent detection on a per-series
    basis, for charts that legitimately mix a percent series with a non-percent
    one (e.g. Industrial Production Index + Capacity Utilization %) — without it,
    every series in the chart would share one percent/non-percent legend format.
    """
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
        is_pct_label = (label in percent_labels) if percent_labels else is_pct_unit

        if view == VIEW_YOY:
            plotted = transforms.yoy_pct_change(s)
            y_title = "YoY % change"
            name = _legend_name(label, plotted, is_percent=True)
            visible = _clip(plotted, start_date)
            fig.add_trace(go.Scatter(x=visible.index, y=visible.values, name=name, line=dict(color=color, width=2)))

            if forecast:
                fc_yoy = transforms.linear_forecast_yoy(s, lookback=forecast_lookback, horizon=forecast_horizon)
                if not fc_yoy.empty:
                    connector = pd.concat([plotted.iloc[[-1]], fc_yoy])
                    fig.add_trace(go.Scatter(
                        x=connector.index, y=connector.values,
                        name=_legend_name(f"{label} — Forecast", fc_yoy, is_percent=True),
                        line=dict(color=color, width=2, dash="dash"),
                    ))
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

        scale = (100 / s.iloc[0]) if (index_to_100 and len(s) > 0) else 1.0
        plotted = s * scale
        if index_to_100:
            y_title = "Index (start = 100)"
        name = _legend_name(label, plotted, is_percent=is_pct_label and not index_to_100)
        visible = _clip(plotted, start_date)
        fig.add_trace(go.Scatter(x=visible.index, y=visible.values, name=name, line=dict(color=color, width=2)))

        if forecast:
            if forecast_from_level is not None and not forecast_from_level.empty:
                fc = transforms.derive_annualized_rate_forecast(
                    forecast_from_level, lookback=forecast_lookback, horizon=forecast_horizon,
                )
            else:
                fc = transforms.linear_forecast(s, lookback=forecast_lookback, horizon=forecast_horizon) * scale
            if not fc.empty:
                connector = pd.concat([plotted.iloc[[-1]], fc])
                fig.add_trace(go.Scatter(
                    x=connector.index, y=connector.values,
                    name=_legend_name(f"{label} — Forecast", fc, is_percent=is_pct_label and not index_to_100),
                    line=dict(color=color, width=2, dash="dash"),
                ))

        if show_average:
            avg_val = s.mean() * scale
            if pd.notna(avg_val) and not visible.empty:
                avg_label = f"{label} — Historical Avg: {_format_value(avg_val, is_pct_label and not index_to_100)}"
                fig.add_trace(go.Scatter(
                    x=[visible.index.min(), visible.index.max()], y=[avg_val, avg_val],
                    name=avg_label, mode="lines", line=dict(color=MUTED, width=1.5, dash="dot"),
                ))

    display_start = start_date if start_date is not None else min(s.index.min() for s in non_empty.values())
    _add_recession_bands(fig, display_start, overall_end)

    if view == VIEW_ROC:
        fig.add_hline(y=0, line_color=AXIS, line_width=1)

    return _apply_layout(fig, y_title)


def build_share_chart(component_series: dict[str, pd.Series], timeframe: str = "Max") -> go.Figure:
    """100%-stacked area chart: each component's share of the combined total over time.

    Better than separate lines for a composition story (e.g. services' rising share of
    spending) since the categories are wildly different in absolute dollar size but the
    story is about the mix shifting, not the raw levels.
    """
    fig = go.Figure()
    non_empty = {label: s.dropna() for label, s in component_series.items() if not s.empty}
    if not non_empty:
        return fig

    df = pd.DataFrame(non_empty).dropna()
    if df.empty:
        return fig
    total = df.sum(axis=1)
    shares = df.div(total, axis=0) * 100

    overall_end = shares.index.max()
    start_date = _timeframe_start(overall_end, timeframe)

    for i, label in enumerate(shares.columns):
        color = CATEGORICAL[i % len(CATEGORICAL)]
        series = shares[label]
        visible = _clip(series, start_date)
        fig.add_trace(go.Scatter(
            x=visible.index, y=visible.values,
            name=_legend_name(label, series, is_percent=True),
            mode="lines", line=dict(width=1, color=SURFACE),
            stackgroup="one", fillcolor=color,
        ))

    display_start = start_date if start_date is not None else shares.index.min()
    _add_recession_bands(fig, display_start, overall_end)
    fig.update_yaxes(range=[0, 100])
    return _apply_layout(fig, "Share of total (%)")


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


def build_dual_axis_chart(
    primary: pd.Series,
    primary_label: str,
    primary_unit: str,
    secondary: pd.Series,
    secondary_label: str,
    secondary_unit: str,
    timeframe: str = "Max",
) -> go.Figure:
    """Two series on independent y-axes. Deliberate exception to the single-axis
    rule used everywhere else in this dashboard — see the module docstring.
    """
    fig = go.Figure()
    if primary.empty or secondary.empty:
        return fig

    overall_end = max(primary.index.max(), secondary.index.max())
    start_date = _timeframe_start(overall_end, timeframe)
    primary_visible = _clip(primary, start_date)
    secondary_visible = _clip(secondary, start_date)

    primary_color, secondary_color = CATEGORICAL[0], CATEGORICAL[1]

    fig.add_trace(go.Scatter(
        x=primary_visible.index, y=primary_visible.values,
        name=_legend_name(primary_label, primary, is_percent="%" in primary_unit),
        line=dict(color=primary_color, width=2), yaxis="y",
    ))
    fig.add_trace(go.Scatter(
        x=secondary_visible.index, y=secondary_visible.values,
        name=_legend_name(secondary_label, secondary, is_percent="%" in secondary_unit),
        line=dict(color=secondary_color, width=2), yaxis="y2",
    ))

    display_start = start_date if start_date is not None else min(primary.index.min(), secondary.index.min())
    _add_recession_bands(fig, display_start, overall_end)
    fig.add_hline(y=0, line_color=AXIS, line_width=1)

    fig.update_layout(
        template="plotly_white",
        plot_bgcolor=SURFACE,
        paper_bgcolor=SURFACE,
        font=dict(color=INK_PRIMARY, family="system-ui, -apple-system, Segoe UI, sans-serif"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(color=INK_SECONDARY)),
        margin=dict(l=10, r=10, t=10, b=10),
        hovermode="x unified",
        dragmode=False,
        xaxis=dict(showgrid=False, linecolor=AXIS, tickfont=dict(color=MUTED), fixedrange=True),
        yaxis=dict(
            title=primary_unit, tickfont=dict(color=primary_color), title_font=dict(color=primary_color),
            showgrid=True, gridcolor=GRIDLINE, zeroline=False, fixedrange=True,
        ),
        yaxis2=dict(
            title=secondary_unit, tickfont=dict(color=secondary_color), title_font=dict(color=secondary_color),
            overlaying="y", side="right", showgrid=False, zeroline=False, fixedrange=True,
        ),
    )
    return fig


def build_inflation_chart(
    index_series: dict[str, pd.Series],
    rate_series: dict[str, pd.Series],
    view: str,
    timeframe: str = "Max",
    rate_series_view: str = VIEW_MOM_SAAR,
) -> go.Figure:
    """CPI/PCE-style chart: index-level series (Headline, Core) that get transformed
    per the selected view, plus a companion "already a rate" series (e.g. a trimmed-
    mean measure published directly as a % change) that only appears in whichever
    single view matches the unit it's natively published in — it has no meaningful
    index level, and taking YoY/annualized change of an already-annualized rate
    isn't meaningful either, so it doesn't participate in the other views.
    """
    fig = go.Figure()
    non_empty_index = {label: s for label, s in index_series.items() if not s.empty}
    non_empty_rate = {label: s for label, s in rate_series.items() if not s.empty}
    if not non_empty_index and not non_empty_rate:
        return fig

    all_series = list(non_empty_index.values()) + list(non_empty_rate.values())
    overall_end = max(s.index.max() for s in all_series)
    start_date = _timeframe_start(overall_end, timeframe)

    y_title = "Index"
    i = 0
    for label, s in non_empty_index.items():
        color = CATEGORICAL[i % len(CATEGORICAL)]
        i += 1
        if view == VIEW_YOY:
            plotted = transforms.yoy_pct_change(s)
            y_title = "YoY % change"
        elif view == VIEW_MOM_SAAR:
            plotted = transforms.annualized_pct_change(s)
            y_title = "Monthly change, annualized (%)"
        else:
            plotted = s
            y_title = "Index"
        visible = _clip(plotted, start_date)
        fig.add_trace(go.Scatter(
            x=visible.index, y=visible.values,
            name=_legend_name(label, plotted, is_percent=view != VIEW_LEVEL),
            line=dict(color=color, width=2),
        ))

    if view == rate_series_view:
        for label, s in non_empty_rate.items():
            color = CATEGORICAL[i % len(CATEGORICAL)]
            i += 1
            visible = _clip(s, start_date)
            fig.add_trace(go.Scatter(
                x=visible.index, y=visible.values,
                name=_legend_name(label, s, is_percent=True),
                line=dict(color=color, width=2, dash="dot"),
            ))
        y_title = rate_series_view.replace(" %", "") + " (%)"

    display_start = start_date if start_date is not None else min(s.index.min() for s in all_series)
    _add_recession_bands(fig, display_start, overall_end)

    return _apply_layout(fig, y_title)
