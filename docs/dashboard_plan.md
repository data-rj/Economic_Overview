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

## 1. Macro Overview (5 charts)

| Chart | FRED series | RoC | Why |
|---|---|---|---|
| Real GDP Growth: YoY % and Quarterly Annualized, combined (+ 2Q forecast, log-linear, 8Q window) | `GDPC1`, `A191RL1Q225SBEA` | | Two standard ways to read GDP growth on one % scale — YoY (smoother) and BEA's quarterly annualized rate (the number everyone quotes) — both forecasts derived from the same log-linear regression on the GDP level so they stay consistent. No separate dollar-level chart (GDP's level doesn't share a scale with either growth measure), and no RoC view (RoC of a growth rate is a second derivative) |
| Contributions to GDP growth by component (stacked bar: PCE, Investment, Net Exports, Govt) — **implemented as an approximation**, computed dashboard-side from component levels (`PCEC96`, `GPDIC1`, `GCEC1`, `EXPGSC1`, `IMPGSC1`) relative to prior-quarter GDP, rather than BEA's own pre-built contribution series (IDs for those were never confirmed) | see above | | Shows what is driving growth, sets up the rest of the dashboard |
| Output Gap (% of Potential GDP) | `GDPC1`, `GDPPOT` | | Above/below sustainable capacity — overheating vs. slack |
| Real GDP: Actual vs. Potential (CBO), levels | `GDPC1`, `GDPPOT` | | The economy's sustainable output ceiling, in dollar terms |
| Real GDP Growth: Actual vs. Potential (CBO), YoY | `GDPC1`, `GDPPOT` | | Same comparison in growth-rate terms |

Real GDP's separate level chart and quarterly-annualized growth chart were
consolidated into one combined chart (above); as a result Real GDP no longer
appears in the Business Cycle / RoC summary section (a 🔁 toggle on a chart
that already only shows growth-rate views would be a second derivative).

The three Potential GDP charts use CBO's official Real Potential GDP series
(`GDPPOT`) directly, replacing an earlier dashboard-side two-factor
growth-accounting estimate.

GDP Price Deflator chart was removed (no longer needed).

## 2. Labor Market (5 charts)

| Chart | FRED series | RoC | Why |
|---|---|---|---|
| Unemployment Rate (U-3) + Underemployment Rate (U-6) | `UNRATE`, `U6RATE` | | Headline slack vs. total slack including marginally attached/part-time-for-economic-reasons workers |
| Nonfarm Payrolls | `PAYEMS` | 🔁 | Job creation pace |
| Average Hourly Earnings | `CES0500000003` | 🔁 | Wage growth pace — split from Payrolls into its own chart since indexing them together flattened one against the other (different long-run growth trajectories, and opposite short-run behavior during COVID) |
| Initial Jobless Claims | `ICSA` | | Weekly leading indicator, moves before payrolls/UNRATE |
| JOLTS Openings & Quits | `JTSJOL`, `JTSQUR` | 🔁 (openings only) | Labor demand and worker confidence |
| Labor Force Participation Rate by age (Overall, 16-24, 25-54, 55+) | `CIVPART`, `LNS11300012`, `LNS11300060`, `LNS11324230` | | Cyclical softness vs. structural/demographic shifts |

## 3. Consumer (8 charts)

| Chart | FRED series | RoC | Why |
|---|---|---|---|
| Real PCE + Personal Income + Personal Savings, indexed (+ 2Q forecast, 12mo regression) | `PCEC96`, `PI`, `PMSAVE` | 🔁 | Core consumer spending vs. the income/savings fueling it |
| PCE by category — share of total (100% stacked area) | `PCEDG`, `PCEND`, `PCES` | | Composition of spending (e.g. services' rising share), not just raw dollars |
| Real Disposable Personal Income | `DSPIC96` | 🔁 | Fuel for spending |
| Personal Saving Rate | `PSAVERT` | | Cushion / spending sustainability |
| Retail Sales + Retail Sales Ex Autos + PCE Services, indexed | `RSAFS`, `RSFSXMV`, `PCES` | 🔁 | Higher-frequency consumer activity; PCE Services fills the services-spending gap retail sales misses |
| Household Debt Service Ratio: Total, Mortgage, Consumer | `TDSP`, `MDSP`, `CDSP` | | Leverage/health angle, by debt type |
| Consumer Credit Outstanding | `TOTALSL` | 🔁 | Is rising debt service driven by debt stock growth or rates? |
| Consumer Debt Delinquency Rates: Credit Cards, Consumer Loans, Mortgages | `DRCCLACBS`, `DRCLACBS`, `DRSFRMACBS` | | Actual default risk, distinct from payment-burden ratios above |

## 4. Corporate America (5 charts)

| Chart | FRED series | RoC | Why |
|---|---|---|---|
| Corporate Profits After Tax, + historical average line | `CP` | 🔁 | Bottom-line health of the corporate sector vs. its long-run norm |
| Corporate Profits as % of GDP | `CP`, `GDP` | | Profit growth vs. economy growth — rising share = margin expansion |
| Industrial Production Index + Capacity Utilization | `INDPRO`, `TCU` | 🔁 (INDPRO only) | Output growth from new capacity vs. existing capacity running hotter |
| Corporate Bond Spreads: Baa, BB, B, CCC & Below | `BAA10Y`, `BAMLH0A1HYBB`, `BAMLH0A2HYB`, `BAMLH0A3HYC` | | Risk appetite across the full credit spectrum |
| Corporate Loan Delinquencies & Charge-Offs | `DRBLACBS`, `CORBLACBS` | | Actual bank-reported corporate credit stress |

## 5. Public & Private Investment (5 charts)

| Chart | FRED series | RoC | Why |
|---|---|---|---|
| Real Private Fixed Investment, nonresidential/residential split | `PNFI`, `PRFI` | 🔁 | Capex + housing, split |
| Nonresidential Investment by type: Equipment / Structures / IP products | BEA Table 5.3.6 series on FRED — *still unverified, left as placeholder; user declined the construction/capex proxy alternative* | 🔁 | Are firms investing in machines, buildings, or software/R&D? |
| Housing Starts & Building Permits | `HOUST`, `PERMIT` | 🔁 | Leading indicator, private residential investment |
| Business Inventory-to-Sales Ratio | `ISRATIO` | | Signals demand vs overproduction |
| Total Business Inventories | `BUSINV` | 🔁 | Decomposes the ratio above — inventory buildup vs. sales change |

## 6. Government (3 charts)

| Chart | FRED series | RoC | Why |
|---|---|---|---|
| Government Consumption & Investment (contribution to GDP) | `GCE` | 🔁 | Govt's direct GDP footprint |
| Federal Outlays vs Receipts | `FGEXPND`, `FGRECPT` | 🔁 | Spending vs revenue trend |
| Federal Deficit (trailing 12-month) vs. Federal Debt (% of GDP), dual axis | `MTSDS133FMS`, `GFDEGDQ188S` | | TTM smooths Treasury seasonality; dual axis is a deliberate exception since the deficit crosses zero and can't be indexed against an always-positive ratio |

Major Federal Budget Components chart (Defense/Social Security/Medicare/etc.) — skipped for now; needs OMB/Treasury budget-function series this session couldn't verify with confidence.

## 7. Prices & Monetary Policy (5 charts)

Kept as its own section rather than merging into Macro Overview — preserves
the deliberate "closes the loop" placement (inflation/policy context for
every section above it) and keeps Macro Overview from growing to ~10 charts.

| Chart | FRED series | View | Why |
|---|---|---|---|
| CPI: Headline, Core & Trimmed Mean | `CPIAUCSL`, `CPILFESL`, `TRMMEANCPIM159SFRBCLE` | Level / YoY / Monthly Annualized (RoC removed) | Most-watched inflation gauge; Trimmed Mean (Cleveland Fed) only shows in Monthly Annualized view, its native unit |
| PCE Price Index: Headline, Core & Trimmed Mean | `PCEPI`, `PCEPILFE`, `PCETRIM12M159SFRBDAL` | Level / YoY / Monthly Annualized (RoC removed) | The Fed's preferred measure; Trimmed Mean (Dallas Fed) only shows in YoY view, its native unit |
| Fed Funds Rate vs 10Y Treasury | `FEDFUNDS`, `DGS10`, `T10Y2Y` | | Policy stance and yield curve signal |
| M2 Money Supply + M2 Velocity, indexed | `M2SL`, `M2V` | 🔁 | Is money supply growth translating into activity, or just accumulating? |
| Federal Reserve Balance Sheet | `WALCL` | 🔁 | QE/QT counterpart to rate policy; tied to the M2 growth story |

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

## Timeframe default

Every chart's Timeframe dropdown (`1Y | 5Y | 10Y | 20Y | Max`) defaults to
**5Y** on first load, rather than Max — keeps the initial view focused on the
recent cycle; users can widen it per chart as needed.

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
