# US Economy Dashboard — Planning Doc

Streamlit dashboard reviewing the US economy through ~27 charts, organized into
7 themes ordered from most macro to most granular. All data sourced from FRED
(Federal Reserve Economic Data).

Flow: Macro sets the scoreboard → Labor explains who's earning → Consumer shows
what gets spent → Corporate shows the supply side → Investment shows what's
being built for the future → Government shows the public-sector lever → Prices/
Rates closes the loop on the policy and inflation backdrop for everything above.

## 1. Macro Overview (4 charts)

| Chart | FRED series | Why |
|---|---|---|
| Real GDP, level + YoY % | `GDPC1` | Headline size/trend of the economy |
| Real GDP growth, quarterly annualized | `A191RL1Q225SBEA` | The number everyone quotes each release |
| Contributions to GDP growth by component (stacked bar: PCE, Investment, Net Exports, Govt) | NIPA "contribution to % change" series (BEA Table 1.1.2, mirrored on FRED) — *verify exact series IDs when building* | Shows what is driving growth, sets up the rest of the dashboard |
| GDP Price Deflator / Nominal vs Real GDP | `GDP`, `GDPC1`, `GDPDEF` | Separates real growth from inflation |

## 2. Labor Market (3 charts)

| Chart | FRED series | Why |
|---|---|---|
| Unemployment Rate | `UNRATE` | Headline labor market slack |
| Nonfarm Payrolls, monthly change | `PAYEMS` | Job creation pace |
| JOLTS Openings & Quits | `JTSJOL`, `JTSQUR` | Labor demand and worker confidence |

## 3. Consumer (5 charts)

| Chart | FRED series | Why |
|---|---|---|
| Real PCE, level + YoY | `PCEC96` | Core consumer spending, ~68% of GDP |
| PCE by category: goods vs services, durables vs nondurables | `PCEDG`, `PCEND`, `PCES` | Where consumers are spending |
| Real Disposable Personal Income | `DSPIC96` | Fuel for spending |
| Personal Saving Rate | `PSAVERT` | Cushion / spending sustainability |
| Retail Sales | `RSAFS` | Higher-frequency read on consumer activity |

*Optional extension: Household Debt Service Ratio (`TDSP`) for a leverage/health angle.*

## 4. Corporate America (4 charts)

| Chart | FRED series | Why |
|---|---|---|
| Corporate Profits After Tax | `CP` | Bottom-line health of the corporate sector |
| Industrial Production Index | `INDPRO` | Real output of the business sector |
| Capacity Utilization | `TCU` | Slack vs tightness in production |
| Corporate Bond Spread | `BAA10Y` | Market-based read on corporate stress / risk appetite |

## 5. Public & Private Investment (4 charts)

| Chart | FRED series | Why |
|---|---|---|
| Real Private Fixed Investment, nonresidential/residential split | `PNFI`, `PRFI` | Capex + housing, split |
| Nonresidential Investment by type: Equipment / Structures / IP products | BEA Table 5.3.6 series on FRED — *verify exact series IDs when building* | Are firms investing in machines, buildings, or software/R&D? |
| Housing Starts & Building Permits | `HOUST`, `PERMIT` | Leading indicator, private residential investment |
| Business Inventory-to-Sales Ratio | `ISRATIO` | Signals demand vs overproduction |

## 6. Government (4 charts)

| Chart | FRED series | Why |
|---|---|---|
| Government Consumption & Investment (contribution to GDP) | `GCE` | Govt's direct GDP footprint |
| Federal Outlays vs Receipts | `FGEXPND`, `FGRECPT` | Spending vs revenue trend |
| Federal Deficit | `MTSDS133FMS` | The gap, and its trajectory |
| Federal Debt Held by Public, % of GDP | `GFDEGDQ188S` | Long-run fiscal sustainability |

## 7. Prices & Monetary Policy (3 charts)

| Chart | FRED series | Why |
|---|---|---|
| CPI headline vs core, YoY | `CPIAUCSL`, `CPILFESL` | Most-watched inflation gauge |
| PCE Price Index headline vs core, YoY | `PCEPI`, `PCEPILFE` | The Fed's preferred inflation measure |
| Fed Funds Rate vs 10Y Treasury | `FEDFUNDS`, `DGS10`, `T10Y2Y` | Policy stance and yield curve signal |

## Open items for the build phase

- Confirm exact FRED series IDs flagged "verify" above (GDP contribution
  components, investment-by-type breakdown).
- Decide on FRED API key storage (env var / Streamlit secrets) and caching
  strategy for API calls.
- Design page/section layout in Streamlit (single scrolling page vs
  multi-page app with one page per theme vs sidebar theme selector).
