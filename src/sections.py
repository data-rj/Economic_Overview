"""Renders dashboard sections (themes) as Streamlit content."""
from __future__ import annotations

import streamlit as st

from . import charts
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
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.caption(f"Source: FRED — {', '.join(spec.series.values())}")
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
