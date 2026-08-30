"""Renders dashboard sections (themes) as Streamlit content."""
from __future__ import annotations

import streamlit as st

from . import charts, transforms
from .config import ChartSpec, Section
from .fred import fetch_series, fetch_series_error


def render_chart(spec: ChartSpec) -> None:
    st.subheader(spec.title)
    st.caption(spec.why)

    if spec.placeholder:
        st.info(f"Not yet wired up. {spec.placeholder_note}")
        st.divider()
        return

    if spec.kind == "gdp_contribution":
        render_gdp_contribution_chart(spec)
        return

    if spec.kind == "potential_gdp":
        render_potential_gdp_chart(spec)
        return

    if spec.kind == "share":
        render_share_chart(spec)
        return

    if spec.kind == "ratio":
        render_ratio_chart(spec)
        return

    if spec.kind == "deficit_debt":
        render_deficit_debt_chart(spec)
        return

    if spec.kind == "inflation":
        render_inflation_chart(spec)
        return

    series_map = {label: fetch_series(series_id) for label, series_id in spec.series.items()}
    if all(s.empty for s in series_map.values()):
        details = "; ".join(
            f"{series_id} — {fetch_series_error(series_id)}" for series_id in spec.series.values()
        )
        st.warning(f"No data returned. {details}")
        st.divider()
        return

    control_cols = st.columns([3, 1])
    view = charts.VIEW_LEVEL
    with control_cols[0]:
        if spec.roc_eligible:
            view = st.radio(
                "View",
                charts.VIEWS,
                horizontal=True,
                key=f"view_{spec.id}",
                label_visibility="collapsed",
            )
    with control_cols[1]:
        timeframe = st.selectbox(
            "Timeframe",
            charts.TIMEFRAME_OPTIONS,
            index=len(charts.TIMEFRAME_OPTIONS) - 1,
            key=f"timeframe_{spec.id}",
            label_visibility="collapsed",
        )

    fig = charts.build_chart(
        series_map, view, unit=spec.unit, index_to_100=spec.index_to_100, timeframe=timeframe,
        forecast=spec.forecast, forecast_lookback=spec.forecast_lookback, forecast_horizon=spec.forecast_horizon,
        show_average=spec.show_average, percent_labels=spec.percent_labels,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.caption(f"Source: FRED — {', '.join(spec.series.values())}")
    st.divider()


def render_ratio_chart(spec: ChartSpec) -> None:
    label, numerator_id = next(iter(spec.series.items()))
    numerator = fetch_series(numerator_id)
    denominator = fetch_series(spec.gdp_series_id)

    if numerator.empty or denominator.empty:
        all_ids = [numerator_id, spec.gdp_series_id]
        details = "; ".join(f"{series_id} — {fetch_series_error(series_id)}" for series_id in all_ids)
        st.warning(f"No data returned. {details}")
        st.divider()
        return

    num_aligned, den_aligned = numerator.align(denominator, join="inner")
    ratio = (num_aligned / den_aligned * 100).dropna()
    ratio.name = numerator_id

    _, timeframe_col = st.columns([3, 1])
    with timeframe_col:
        timeframe = st.selectbox(
            "Timeframe",
            charts.TIMEFRAME_OPTIONS,
            index=len(charts.TIMEFRAME_OPTIONS) - 1,
            key=f"timeframe_{spec.id}",
            label_visibility="collapsed",
        )

    fig = charts.build_chart({label: ratio}, charts.VIEW_LEVEL, unit=spec.unit, timeframe=timeframe)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.caption(f"Source: FRED — {numerator_id}, {spec.gdp_series_id}")
    st.divider()


def render_deficit_debt_chart(spec: ChartSpec) -> None:
    labels = list(spec.series.keys())
    series_ids = list(spec.series.values())
    deficit_label, debt_label = labels[0], labels[1]
    deficit_monthly = fetch_series(spec.series[deficit_label])
    debt_pct_gdp = fetch_series(spec.series[debt_label])

    if deficit_monthly.empty or debt_pct_gdp.empty:
        details = "; ".join(f"{series_id} — {fetch_series_error(series_id)}" for series_id in series_ids)
        st.warning(f"No data returned. {details}")
        st.divider()
        return

    deficit_ttm = transforms.trailing_sum(deficit_monthly, window=12).dropna()
    deficit_ttm.name = spec.series[deficit_label]

    _, timeframe_col = st.columns([3, 1])
    with timeframe_col:
        timeframe = st.selectbox(
            "Timeframe",
            charts.TIMEFRAME_OPTIONS,
            index=len(charts.TIMEFRAME_OPTIONS) - 1,
            key=f"timeframe_{spec.id}",
            label_visibility="collapsed",
        )

    fig = charts.build_dual_axis_chart(
        deficit_ttm, deficit_label, "$ millions",
        debt_pct_gdp, debt_label, "%",
        timeframe=timeframe,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.caption(f"Source: FRED — {', '.join(series_ids)}")
    st.divider()


def render_inflation_chart(spec: ChartSpec) -> None:
    index_map = {label: fetch_series(series_id) for label, series_id in spec.series.items()}
    rate_map = {label: fetch_series(series_id) for label, series_id in spec.rate_series.items()}
    all_ids = list(spec.series.values()) + list(spec.rate_series.values())

    if all(s.empty for s in index_map.values()) and all(s.empty for s in rate_map.values()):
        details = "; ".join(f"{series_id} — {fetch_series_error(series_id)}" for series_id in all_ids)
        st.warning(f"No data returned. {details}")
        st.divider()
        return

    control_cols = st.columns([3, 1])
    with control_cols[0]:
        view = st.radio(
            "View",
            charts.INFLATION_VIEWS,
            horizontal=True,
            key=f"view_{spec.id}",
            label_visibility="collapsed",
        )
    with control_cols[1]:
        timeframe = st.selectbox(
            "Timeframe",
            charts.TIMEFRAME_OPTIONS,
            index=len(charts.TIMEFRAME_OPTIONS) - 1,
            key=f"timeframe_{spec.id}",
            label_visibility="collapsed",
        )

    fig = charts.build_inflation_chart(
        index_map, rate_map, view, timeframe=timeframe, rate_series_view=spec.rate_series_view,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.caption(f"Source: FRED — {', '.join(all_ids)}")
    st.divider()


def render_share_chart(spec: ChartSpec) -> None:
    series_map = {label: fetch_series(series_id) for label, series_id in spec.series.items()}
    if all(s.empty for s in series_map.values()):
        details = "; ".join(
            f"{series_id} — {fetch_series_error(series_id)}" for series_id in spec.series.values()
        )
        st.warning(f"No data returned. {details}")
        st.divider()
        return

    _, timeframe_col = st.columns([3, 1])
    with timeframe_col:
        timeframe = st.selectbox(
            "Timeframe",
            charts.TIMEFRAME_OPTIONS,
            index=len(charts.TIMEFRAME_OPTIONS) - 1,
            key=f"timeframe_{spec.id}",
            label_visibility="collapsed",
        )

    fig = charts.build_share_chart(series_map, timeframe=timeframe)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.caption(f"Source: FRED — {', '.join(spec.series.values())}")
    st.divider()


def render_potential_gdp_chart(spec: ChartSpec) -> None:
    productivity = fetch_series(spec.series["Productivity"])
    labor_force_monthly = fetch_series(spec.series["Labor Force"])
    gdp_level = fetch_series(spec.gdp_series_id)
    # "QE" (quarter-end) to match fetch_series's quarter-end dating of GDPC1/OPHNFB —
    # otherwise this resample's quarter-start dates wouldn't align with them below.
    labor_force = labor_force_monthly.resample("QE").mean() if not labor_force_monthly.empty else labor_force_monthly

    if gdp_level.empty or productivity.empty or labor_force.empty:
        all_ids = list(spec.series.values()) + [spec.gdp_series_id]
        details = "; ".join(f"{series_id} — {fetch_series_error(series_id)}" for series_id in all_ids)
        st.warning(f"No data returned. {details}")
        st.divider()
        return

    _, timeframe_col = st.columns([3, 1])
    with timeframe_col:
        timeframe = st.selectbox(
            "Timeframe",
            charts.TIMEFRAME_OPTIONS,
            index=len(charts.TIMEFRAME_OPTIONS) - 1,
            key=f"timeframe_{spec.id}",
            label_visibility="collapsed",
        )

    fig = charts.build_potential_gdp_chart(gdp_level, productivity, labor_force, timeframe=timeframe)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    all_ids = list(spec.series.values()) + [spec.gdp_series_id]
    st.caption(f"Source: FRED — {', '.join(all_ids)}")
    st.divider()


def render_gdp_contribution_chart(spec: ChartSpec) -> None:
    series_map = {label: fetch_series(series_id) for label, series_id in spec.series.items()}
    gdp_level = fetch_series(spec.gdp_series_id)

    if gdp_level.empty or all(s.empty for s in series_map.values()):
        all_ids = list(spec.series.values()) + [spec.gdp_series_id]
        details = "; ".join(f"{series_id} — {fetch_series_error(series_id)}" for series_id in all_ids)
        st.warning(f"No data returned. {details}")
        st.divider()
        return

    exports = series_map.pop("Exports", None)
    imports = series_map.pop("Imports", None)
    if exports is not None and imports is not None and not exports.empty and not imports.empty:
        series_map["Net Exports"] = exports.subtract(imports, fill_value=0)

    # PCE (PCEC96) is monthly; the other components are quarterly and now
    # quarter-end dated by fetch_series — resample PCE to match, or its
    # month-start dates won't align with them in build_contribution_chart's
    # date-based alignment against gdp_level.
    if "PCE" in series_map and not series_map["PCE"].empty:
        series_map["PCE"] = series_map["PCE"].resample("QE").mean()

    ordered_labels = ["PCE", "Investment", "Net Exports", "Government"]
    series_map = {label: series_map[label] for label in ordered_labels if label in series_map}

    _, timeframe_col = st.columns([3, 1])
    with timeframe_col:
        timeframe = st.selectbox(
            "Timeframe",
            charts.TIMEFRAME_OPTIONS,
            index=len(charts.TIMEFRAME_OPTIONS) - 1,
            key=f"timeframe_{spec.id}",
            label_visibility="collapsed",
        )

    fig = charts.build_contribution_chart(series_map, gdp_level, timeframe=timeframe)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    all_ids = list(spec.series.values()) + [spec.gdp_series_id]
    st.caption(f"Source: FRED — {', '.join(all_ids)}")
    st.divider()


def render_section(section: Section) -> None:
    st.header(section.title)
    if section.intro:
        st.write(section.intro)
    for spec in section.charts:
        render_chart(spec)


def render_business_cycle(all_sections: list[Section]) -> None:
    st.header("Business Cycle / Rate of Change")
    st.write(
        "3-month vs. 12-month moving-average rate of change for the dashboard's trend "
        "indicators (ITR Economics-style). A 3MMA RoC crossing above its 12MMA RoC is an "
        "early signal of an accelerating trend; crossing below signals a slowing one."
    )

    candidates = [
        spec
        for section in all_sections
        for spec in section.charts
        if spec.roc_eligible and not spec.placeholder
    ]

    for spec in candidates:
        label, series_id = next(iter(spec.series.items()))
        s = fetch_series(series_id)
        if s.empty:
            continue
        st.subheader(spec.title)
        fig = charts.build_chart({label: s}, charts.VIEW_ROC, unit=spec.unit)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.divider()
