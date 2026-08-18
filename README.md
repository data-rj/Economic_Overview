# Economic_Overview

A Streamlit dashboard reviewing the US economy through FRED-sourced charts, organized into themes from macro (GDP) down through Labor, Consumer, Corporate, Investment, Government, and Prices/Monetary Policy. See `docs/dashboard_plan.md` for the full chart list and design rationale.

## Setup

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Get a free FRED API key at https://fred.stlouisfed.org/docs/api/api_key.html

3. Provide the key one of two ways:

   - Environment variable: `export FRED_API_KEY=your_key_here`
   - Streamlit secrets: create `.streamlit/secrets.toml` with:

     ```toml
     FRED_API_KEY = "your_key_here"
     ```

## Run

```bash
streamlit run app.py
```

Without a FRED API key, the app still loads but charts show a "no data" warning until one is set.
