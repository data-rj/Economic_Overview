# US Economy Dashboard — Planning Doc

Streamlit dashboard reviewing the US economy through ~27 charts, organized into
7 themes ordered from most macro to most granular. All data sourced from FRED
(Federal Reserve Economic Data).

Flow: Macro sets the scoreboard → Labor explains who's earning → Consumer shows
what gets spent → Corporate shows the supply side → Investment shows what's
being built for the future → Government shows the public-sector lever → Prices/
Rates closes the loop on the policy and inflation backdrop for everything above.

## Rate-of-Change (RoC) methodology

Following ITR Economics' approach: for series where it applies, compute a
**3-month moving average (3MMA)** and a **12-month moving average (12MMA)**,
then take the year-over-year % change of each moving average. The 12MMA RoC
smooths seasonality/noise to show underlying trend; the 3MMA RoC is more
responsive and leads the 12MMA at turning points. The crossing of 3MMA RoC
over/under 12MMA RoC is the leading signal ITR uses to call cyclical turns
(their Accelerating Growth / Slowing Growth / Recession / Recovery phases).
For quarterly series (e.g. GDP), the equivalent is a 1-quarter and 4-quarter
moving average.

**Applies well to** level/volume/index series with real trend + cycle
character (marked with a 🔁 RoC toggle below): GDP, PCE, payrolls, industrial
production, retail sales, corporate profits, investment, housing starts,
price indices (CPI, PCE Price Index).

**Does not apply** to series that are already rates/ratios (unemployment
rate, saving rate, capacity utilization, participation rate, Fed funds rate,
bond yields/spreads, deficit or debt as % of GDP) — taking a rate-of-change
of a rate is a second derivative that loses interpretability. These stay as
level / YoY only.

## 1. Macro Overview (4 charts)

| Chart | FRED series | RoC | Why |
|---|---|---|---|
| Real GDP, level + YoY % (+ 2Q linear-regression forecast) | `GDPC1` | 🔁 | Headline size/trend of the economy |
| Real GDP growth, quarterly annualized (+ 2Q linear-regression forecast) | `A191RL1Q225SBEA` | | The number everyone quotes each release |
| Contributions to GDP growth by component (stacked bar: PCE, Investment, Net Exports, Govt) — **implemented as an approximation**, computed dashboard-side from component levels (`PCEC96`, `GPDIC1`, `GCEC1`, `EXPGSC1`, `IMPGSC1`) relative to prior-quarter GDP, rather than BEA's own pre-built contribution series (IDs for those were never confirmed) | see above | | Shows what is driving growth, sets up the rest of the dashboard |
| Potential GDP (estimated) vs actual, shaded output gap — two-factor growth-accounting estimate (trend productivity + trend labor force growth, compounded from an actual-GDP-calibrated base) | `OPHNFB`, `CLF16OV`, `GDPC1` | | The economy's sustainable output ceiling, standard CBO-style two-factor framework |

GDP Price Deflator chart was removed (no longer needed).

## 2. Labor Market (3 charts)

| Chart | FRED series | RoC | Why |
|---|---|---|---|
| Unemployment Rate | `UNRATE` | | Headline labor market slack |
| Nonfarm Payrolls, monthly change | `PAYEMS` | 🔁 | Job creation pace |
| JOLTS Openings & Quits | `JTSJOL`, `JTSQUR` | 🔁 (openings only) | Labor demand and worker confidence |

## 3. Consumer (5 charts)

| Chart | FRED series | RoC | Why |
|---|---|---|---|
| Real PCE, level + YoY | `PCEC96` | 🔁 | Core consumer spending, ~68% of GDP |
| PCE by category: goods vs services, durables vs nondurables | `PCEDG`, `PCEND`, `PCES` | 🔁 | Where consumers are spending |
| Real Disposable Personal Income | `DSPIC96` | 🔁 | Fuel for spending |
| Personal Saving Rate | `PSAVERT` | | Cushion / spending sustainability |
| Retail Sales | `RSAFS` | 🔁 | Higher-frequency read on consumer activity |

*Optional extension: Household Debt Service Ratio (`TDSP`) for a leverage/health angle.*

## 4. Corporate America (4 charts)

| Chart | FRED series | RoC | Why |
|---|---|---|---|
| Corporate Profits After Tax | `CP` | 🔁 | Bottom-line health of the corporate sector |
| Industrial Production Index | `INDPRO` | 🔁 | Real output of the business sector |
| Capacity Utilization | `TCU` | | Slack vs tightness in production |
| Corporate Bond Spread | `BAA10Y` | | Market-based read on corporate stress / risk appetite |

## 5. Public & Private Investment (4 charts)

| Chart | FRED series | RoC | Why |
|---|---|---|---|
| Real Private Fixed Investment, nonresidential/residential split | `PNFI`, `PRFI` | 🔁 | Capex + housing, split |
| Nonresidential Investment by type: Equipment / Structures / IP products | BEA Table 5.3.6 series on FRED — *verify exact series IDs when building* | 🔁 | Are firms investing in machines, buildings, or software/R&D? |
| Housing Starts & Building Permits | `HOUST`, `PERMIT` | 🔁 | Leading indicator, private residential investment |
| Business Inventory-to-Sales Ratio | `ISRATIO` | | Signals demand vs overproduction |

## 6. Government (4 charts)

| Chart | FRED series | RoC | Why |
|---|---|---|---|
| Government Consumption & Investment (contribution to GDP) | `GCE` | 🔁 | Govt's direct GDP footprint |
| Federal Outlays vs Receipts | `FGEXPND`, `FGRECPT` | 🔁 | Spending vs revenue trend |
| Federal Deficit | `MTSDS133FMS` | | The gap, and its trajectory (sign-changing series, RoC not meaningful) |
| Federal Debt Held by Public, % of GDP | `GFDEGDQ188S` | | Long-run fiscal sustainability |

## 7. Prices & Monetary Policy (3 charts)

| Chart | FRED series | RoC | Why |
|---|---|---|---|
| CPI headline vs core, YoY | `CPIAUCSL`, `CPILFESL` | 🔁 | Most-watched inflation gauge |
| PCE Price Index headline vs core, YoY | `PCEPI`, `PCEPILFE` | 🔁 | The Fed's preferred inflation measure |
| Fed Funds Rate vs 10Y Treasury | `FEDFUNDS`, `DGS10`, `T10Y2Y` | | Policy stance and yield curve signal |

## 8. Business Cycle / Rate of Change (summary section)

A closing section presenting the 3MMA-vs-12MMA RoC crossing chart for the
🔁-flagged trend indicators together, similar to ITR's own cycle-stage
scoreboard — lets the viewer see which parts of the economy are
Accelerating Growth / Slowing Growth / Recession / Recovery at a glance,
rather than hunting for the signal chart-by-chart.

- One small-multiple crossing chart per flagged indicator (3MMA RoC vs
  12MMA RoC lines, zero line marked).
- Optional summary table: indicator, current phase, months since last
  crossing.
- Candidate indicator set: GDP, PCE, Payrolls, Industrial Production,
  Retail Sales, Corporate Profits, Real Private Fixed Investment, Housing
  Starts, CPI, PCE Price Index.

## UI design for RoC

Each 🔁-flagged chart gets a view toggle: `Level | YoY % | RoC (3/12MMA)`.
Default view stays on Level/YoY so the dashboard isn't overloaded on first
load; RoC is opt-in per chart. Section 8 is the only place RoC is shown by
default, since that's its dedicated home.

## AI-generated chart commentary (deferred)

Idea explored: auto-generate a short takeaway per chart via the Claude API,
grounded in computed stats (latest value, MoM/YoY change, RoC phase) rather
than raw series data, with commentary cached alongside each data refresh
rather than generated live per page view. **On hold for now** — the app is
being built out without this first; revisit once the core dashboard is
working end-to-end.

## Open items for the build phase

- Confirm exact FRED series IDs flagged "verify" above (GDP contribution
  components, investment-by-type breakdown).
- Decide on FRED API key storage (env var / Streamlit secrets) and caching
  strategy for API calls.
- Design page/section layout in Streamlit (single scrolling page vs
  multi-page app with one page per theme vs sidebar theme selector).
- Build a shared RoC helper (3MMA/12MMA + YoY-of-MA) used by both the
  per-chart toggle and the Section 8 summary, so the calculation lives in
  one place.
