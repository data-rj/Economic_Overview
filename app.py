"""US Economy Dashboard — Streamlit entry point."""
import streamlit as st

from src.config import SECTIONS
from src.fred import get_api_key
from src.sections import render_business_cycle, render_section

st.set_page_config(page_title="US Economy Dashboard", layout="wide")

st.title("US Economy Dashboard")
st.caption("All data sourced from FRED (Federal Reserve Economic Data).")

if not get_api_key():
    st.warning(
        "No FRED API key found. Charts will be empty until you set one — see the README for setup instructions."
    )

nav_titles = [section.title for section in SECTIONS] + ["Business Cycle / Rate of Change"]
choice = st.sidebar.radio("Section", nav_titles)

st.sidebar.divider()
if st.sidebar.button("Refresh data"):
    st.cache_data.clear()
    st.rerun()
st.sidebar.caption("Clears cached FRED data (normally refreshed automatically every 30 min).")

if choice == "Business Cycle / Rate of Change":
    render_business_cycle(SECTIONS)
else:
    chosen_section = next(section for section in SECTIONS if section.title == choice)
    render_section(chosen_section)
