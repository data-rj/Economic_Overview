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
