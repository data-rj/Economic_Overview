"""Dashboard content: sections and chart specs, mirroring docs/dashboard_plan.md.

Each ChartSpec maps display labels to FRED series IDs. `roc_eligible` flags
the level/index/volume series where the ITR-style 3MMA/12MMA rate-of-change
view makes sense (see docs/dashboard_plan.md for the full rationale) — rate
and ratio series (unemployment rate, saving rate, spreads, etc.) stay level
or YoY only.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ChartSpec:
    id: str
    title: str
    why: str
    series: dict[str, str] = field(default_factory=dict)  # legend label -> FRED series id
    unit: str = ""
    roc_eligible: bool = False
    index_to_100: bool = False
    placeholder: bool = False
    placeholder_note: str = ""
    kind: str = "line"  # "line", "share", "ratio", "yoy_pair", "gdp_contribution", "deficit_debt", "inflation"
    gdp_series_id: str = ""  # denominator series for kind="gdp_contribution"/"ratio"
    ratio_offset: float = 0.0  # kind="ratio": subtracted from the computed ratio (100 turns "% of X" into "% above/below X")
    forecast: bool = False  # overlay a linear-regression forecast (Level view only)
    forecast_lookback: int = 4  # number of trailing actual periods to fit the forecast line to
    forecast_horizon: int = 2  # number of future periods to forecast
    show_average: bool = False  # overlay a flat full-history-average reference line (Level view only)
    percent_labels: tuple[str, ...] = ()  # series labels to legend-format as % when a chart mixes units
    rate_series: dict[str, str] = field(default_factory=dict)  # kind="inflation": already-a-rate companion series
    rate_series_view: str = "Monthly Annualized %"  # kind="inflation": the one view rate_series appears in
    forecast_from_level_series_id: str = ""  # derive this chart's forecast from another (level) series instead
    forecast_method: str = "linear"  # "linear" or "log_linear" (fits log-level, assumes constant % growth)


@dataclass
class Section:
    id: str
    title: str
    intro: str
    charts: list[ChartSpec] = field(default_factory=list)


SECTIONS: list[Section] = [
    Section(
        id="macro",
        title="Macro Overview",
        intro="The headline scoreboard: how big the economy is, how fast it's growing, and what's driving that growth.",
        charts=[
            ChartSpec(
                id="gdp_real",
                title="Real GDP",
                why=(
                    "Headline size/trend of the economy. Dashed line is a 2-quarter forecast from "
                    "a log-linear regression (fit to log-level, assumes constant % growth rather "
                    "than constant $ growth — a plain linear fit understates growth during "
                    "expansions since it can't capture compounding) fit to the prior 8 quarters."
                ),
                series={"Real GDP": "GDPC1"},
                unit="$ billions (2017 chained)",
                roc_eligible=True,
                forecast=True,
                forecast_lookback=8,
                forecast_method="log_linear",
            ),
            ChartSpec(
                id="gdp_growth",
                title="Real GDP Growth (Quarterly, Annualized)",
                why=(
                    "The number everyone quotes each release. Dashed line is a 2-quarter forecast "
                    "derived from the Real GDP level forecast above (the implied quarterly "
                    "annualized rate between forecasted levels, same log-linear method), rather "
                    "than a separate regression fit directly to this rate series — keeps the two "
                    "charts' forecasts consistent with each other."
                ),
                series={"Real GDP Growth (Annualized)": "A191RL1Q225SBEA"},
                unit="%",
                forecast=True,
                forecast_lookback=8,
                forecast_method="log_linear",
                forecast_from_level_series_id="GDPC1",
            ),
            ChartSpec(
                id="gdp_contributions",
                title="Contributions to GDP Growth by Component (Approximate)",
                why=(
                    "Shows what is driving growth — PCE, Investment, Net Exports, Government. "
                    "Computed here as each component's quarterly change relative to prior-quarter "
                    "real GDP, annualized — a first-order approximation of BEA's official "
                    "chain-weighted contribution figures (BEA Table 1.1.2), not an exact match."
                ),
                kind="gdp_contribution",
                series={
                    "PCE": "PCEC96",
                    "Investment": "GPDIC1",
                    "Government": "GCEC1",
                    "Exports": "EXPGSC1",
                    "Imports": "IMPGSC1",
                },
                gdp_series_id="GDPC1",
                unit="Percentage points (annualized)",
            ),
            ChartSpec(
                id="output_gap",
                title="Output Gap (% of Potential GDP)",
                why=(
                    "Actual real GDP vs. CBO's official Real Potential GDP estimate, expressed as "
                    "the % gap between them — positive means the economy is running above its "
                    "sustainable capacity (overheating risk, inflationary pressure); negative "
                    "means below it (slack, disinflationary/recessionary)."
                ),
                kind="ratio",
                series={"Output Gap": "GDPC1"},
                gdp_series_id="GDPPOT",
                ratio_offset=100.0,
                unit="%",
            ),
            ChartSpec(
                id="potential_gdp_levels",
                title="Real GDP: Actual vs. Potential (CBO)",
                why="The economy's sustainable output ceiling — actual real GDP against CBO's official Real Potential GDP estimate, in level terms.",
                series={"Real GDP (Actual)": "GDPC1", "Real Potential GDP (CBO)": "GDPPOT"},
                unit="$ billions (2017 chained)",
            ),
            ChartSpec(
                id="potential_gdp_yoy",
                title="Real GDP Growth: Actual vs. Potential (CBO), YoY",
                why="Same comparison as above, in growth-rate terms — how actual growth compares to CBO's estimate of sustainable trend growth.",
                kind="yoy_pair",
                series={"Real GDP (Actual)": "GDPC1", "Real Potential GDP (CBO)": "GDPPOT"},
            ),
        ],
    ),
    Section(
        id="labor",
        title="Labor Market",
        intro="Who's earning — the labor market feeds directly into consumer income and spending.",
        charts=[
            ChartSpec(
                id="unemployment_rate",
                title="Unemployment Rate",
                why=(
                    "Headline labor market slack (U-3), alongside U-6 — total unemployed plus "
                    "marginally attached and part-time-for-economic-reasons workers. The gap "
                    "between the two shows how much slack is hidden beneath the headline number."
                ),
                series={"Unemployment Rate (U-3)": "UNRATE", "Underemployment Rate (U-6)": "U6RATE"},
                unit="%",
            ),
            ChartSpec(
                id="payrolls",
                title="Nonfarm Payrolls",
                why=(
                    "Job creation pace alongside Average Hourly Earnings — shows whether wage "
                    "growth is keeping pace with (or outrunning) job growth. Indexed to a common "
                    "start since payrolls (a level) and hourly earnings ($/hr) aren't the same unit."
                ),
                series={"Nonfarm Payrolls": "PAYEMS", "Average Hourly Earnings": "CES0500000003"},
                unit="Index (start = 100)",
                roc_eligible=True,
                index_to_100=True,
            ),
            ChartSpec(
                id="jobless_claims",
                title="Initial Jobless Claims",
                why=(
                    "Weekly leading indicator of labor-market turning points — moves before "
                    "payrolls and the unemployment rate do, since it captures new layoffs as "
                    "they happen rather than a monthly snapshot."
                ),
                series={"Initial Jobless Claims": "ICSA"},
                unit="Level (weekly, SA)",
            ),
            ChartSpec(
                id="jolts",
                title="JOLTS Openings & Quits",
                why="Labor demand and worker confidence.",
                series={"Job Openings": "JTSJOL", "Quits Rate": "JTSQUR"},
                unit="Index (start = 100)",
                roc_eligible=True,
                index_to_100=True,
            ),
            ChartSpec(
                id="labor_force_participation",
                title="Labor Force Participation Rate by Age Group",
                why=(
                    "Overall participation rate plus by age band — distinguishes cyclical labor "
                    "market softness from structural/demographic shifts (e.g. an aging workforce "
                    "pulling the overall rate down even as prime-age participation holds up). "
                    "FRED's youngest measured cohort starts at 16, so \"24 and under\" is the "
                    "16-24 age band."
                ),
                series={
                    "Overall": "CIVPART",
                    "16-24": "LNS11300012",
                    "25-54": "LNS11300060",
                    "55+": "LNS11324230",
                },
                unit="%",
            ),
        ],
    ),
    Section(
        id="consumer",
        title="Consumer",
        intro="What gets spent — the consumer is roughly 68% of GDP.",
        charts=[
            ChartSpec(
                id="pce_real",
                title="Real Personal Consumption Expenditures",
                why=(
                    "Core consumer spending, alongside Personal Income and Personal Savings "
                    "(dollar level, not the savings rate — see the Saving Rate chart below for "
                    "that) — shows whether spending is being fueled by income growth or drawing "
                    "down savings. Indexed to a common start since the three are on very "
                    "different dollar scales. Dashed line is a 2-quarter forecast from a simple "
                    "linear regression fit to the prior 12 months."
                ),
                series={"Real PCE": "PCEC96", "Personal Income": "PI", "Personal Savings": "PMSAVE"},
                unit="Index (start = 100)",
                roc_eligible=True,
                index_to_100=True,
                forecast=True,
                forecast_lookback=12,
                forecast_horizon=6,
            ),
            ChartSpec(
                id="pce_by_category",
                title="PCE by Category — Share of Total",
                why=(
                    "Where consumers are spending, as a share of total PCE rather than raw "
                    "dollars — durables, nondurables, and services are wildly different in "
                    "absolute size, so a share-of-total view shows the composition story (e.g. "
                    "services' rising share of spending) more clearly than three lines at "
                    "different scales would."
                ),
                kind="share",
                series={"Durable Goods": "PCEDG", "Nondurable Goods": "PCEND", "Services": "PCES"},
            ),
            ChartSpec(
                id="disposable_income",
                title="Real Disposable Personal Income",
                why="Fuel for spending.",
                series={"Real Disposable Personal Income": "DSPIC96"},
                unit="$ billions (2017 chained)",
                roc_eligible=True,
            ),
            ChartSpec(
                id="saving_rate",
                title="Personal Saving Rate",
                why="Cushion / spending sustainability.",
                series={"Personal Saving Rate": "PSAVERT"},
                unit="%",
            ),
            ChartSpec(
                id="retail_sales",
                title="Retail Sales",
                why=(
                    "Higher-frequency read on consumer activity, alongside Retail Sales Ex Autos "
                    "(strips out volatile auto sales) and PCE Services — retail sales alone "
                    "misses most services spending (rent, healthcare, haircuts), so PCE Services "
                    "fills that gap. Indexed to a common start since the three are on different "
                    "dollar scales."
                ),
                series={
                    "Retail Sales": "RSAFS",
                    "Retail Sales Ex Autos": "RSFSXMV",
                    "PCE Services": "PCES",
                },
                unit="Index (start = 100)",
                roc_eligible=True,
                index_to_100=True,
            ),
            ChartSpec(
                id="household_debt_service",
                title="Household Debt Service Ratio",
                why=(
                    "Leverage / consumer health angle, decomposed into Mortgage and Consumer "
                    "(non-mortgage) debt service — shows which type of debt is driving the "
                    "overall trend."
                ),
                series={
                    "Total": "TDSP",
                    "Mortgage": "MDSP",
                    "Consumer": "CDSP",
                },
                unit="%",
            ),
            ChartSpec(
                id="consumer_credit",
                title="Consumer Credit Outstanding",
                why=(
                    "Pairs with the Household Debt Service Ratio above — shows whether rising "
                    "debt service burden is being driven by the debt stock growing or by rates/"
                    "payments rising on existing debt."
                ),
                series={"Consumer Credit Outstanding": "TOTALSL"},
                unit="$ billions",
                roc_eligible=True,
            ),
            ChartSpec(
                id="consumer_delinquencies",
                title="Consumer Debt Delinquency Rates",
                why=(
                    "Share of loan balances 30+ days past due, by loan type — a direct read on "
                    "household financial stress and actual default risk, distinct from the debt "
                    "service ratio above (which measures payment burden, not delinquency)."
                ),
                series={
                    "Credit Cards": "DRCCLACBS",
                    "Consumer Loans (Broad)": "DRCLACBS",
                    "Mortgages": "DRSFRMACBS",
                },
                unit="%",
            ),
        ],
    ),
    Section(
        id="corporate",
        title="Corporate America",
        intro="The supply side — how businesses are producing and performing.",
        charts=[
            ChartSpec(
                id="corp_profits",
                title="Corporate Profits After Tax",
                why=(
                    "Bottom-line health of the corporate sector, with a dashed line marking the "
                    "full-history average — shows whether current profits are running above or "
                    "below their long-run norm."
                ),
                series={"Corporate Profits After Tax": "CP"},
                unit="$ billions",
                roc_eligible=True,
                show_average=True,
            ),
            ChartSpec(
                id="corp_profits_gdp_share",
                title="Corporate Profits as % of GDP",
                why=(
                    "Companion to the chart above — separates \"profits growing because the "
                    "economy is growing\" from \"profits growing faster than the economy\" "
                    "(rising profit share / margin expansion). Nominal profits over nominal GDP, "
                    "so the ratio isn't distorted by differing real/nominal deflators."
                ),
                kind="ratio",
                series={"Corporate Profits (% of GDP)": "CP"},
                gdp_series_id="GDP",
                unit="%",
            ),
            ChartSpec(
                id="industrial_production",
                title="Industrial Production Index",
                why=(
                    "Real output of the business sector, alongside Capacity Utilization — shows "
                    "whether output is growing because of new capacity coming online or existing "
                    "capacity running hotter."
                ),
                series={"Industrial Production Index": "INDPRO", "Capacity Utilization": "TCU"},
                unit="Index (2017=100) / %",
                roc_eligible=True,
                percent_labels=("Capacity Utilization",),
            ),
            ChartSpec(
                id="corp_bond_spread",
                title="Corporate Bond Spreads",
                why=(
                    "Market-based read on corporate stress / risk appetite across the credit "
                    "spectrum — investment-grade (Baa) plus high-yield by rating (BB, B, CCC). "
                    "CCC spreads can spike far wider than the others during stress (2008, 2020), "
                    "which will dominate the scale in those periods — use the Timeframe control "
                    "to zoom into calmer periods for a closer look at the tighter-spread lines."
                ),
                series={
                    "Baa − 10Y Treasury": "BAA10Y",
                    "BB High-Yield OAS": "BAMLH0A1HYBB",
                    "B High-Yield OAS": "BAMLH0A2HYB",
                    "CCC & Below OAS": "BAMLH0A3HYC",
                },
                unit="%",
            ),
            ChartSpec(
                id="corporate_delinquencies",
                title="Corporate Loan Delinquencies & Charge-Offs",
                why=(
                    "Business loan credit quality at all commercial banks — delinquency rate "
                    "(30+ days past due) and charge-off rate (loans written off as uncollectible) "
                    "show actual corporate credit stress, distinct from the market-priced bond "
                    "spreads above."
                ),
                series={
                    "Delinquency Rate": "DRBLACBS",
                    "Charge-Off Rate": "CORBLACBS",
                },
                unit="%",
            ),
        ],
    ),
    Section(
        id="investment",
        title="Public & Private Investment",
        intro="What's being built for the future — capex, housing, and inventories.",
        charts=[
            ChartSpec(
                id="private_investment",
                title="Real Private Fixed Investment",
                why="Capex + housing, split nonresidential vs residential.",
                series={"Nonresidential Fixed Investment": "PNFI", "Residential Fixed Investment": "PRFI"},
                unit="$ billions",
                roc_eligible=True,
            ),
            ChartSpec(
                id="investment_by_type",
                title="Nonresidential Investment by Type",
                why="Are firms investing in machines, buildings, or software/R&D?",
                placeholder=True,
                placeholder_note=(
                    "BEA Table 5.3.6 (Equipment / Structures / Intellectual Property Products) — "
                    "confirm exact FRED series IDs before wiring up."
                ),
            ),
            ChartSpec(
                id="housing",
                title="Housing Starts & Building Permits",
                why="Leading indicator for private residential investment.",
                series={"Housing Starts": "HOUST", "Building Permits": "PERMIT"},
                unit="thousands (SAAR)",
                roc_eligible=True,
            ),
            ChartSpec(
                id="inventory_sales_ratio",
                title="Business Inventory-to-Sales Ratio",
                why="Signals demand vs overproduction.",
                series={"Inventory-to-Sales Ratio": "ISRATIO"},
                unit="ratio",
            ),
            ChartSpec(
                id="business_inventories",
                title="Total Business Inventories",
                why=(
                    "Companion to the ratio above — decomposes whether the ratio is moving "
                    "because inventories are building up (this chart) or sales are changing."
                ),
                series={"Total Business Inventories": "BUSINV"},
                unit="$ millions",
                roc_eligible=True,
            ),
        ],
    ),
    Section(
        id="government",
        title="Government",
        intro="The public-sector lever — spending, revenue, and fiscal sustainability.",
        charts=[
            ChartSpec(
                id="gov_consumption",
                title="Government Consumption & Investment",
                why="Government's direct GDP footprint.",
                series={"Govt Consumption & Investment": "GCE"},
                unit="$ billions",
                roc_eligible=True,
            ),
            ChartSpec(
                id="outlays_receipts",
                title="Federal Outlays vs Receipts",
                why="Spending vs revenue trend.",
                series={"Federal Outlays": "FGEXPND", "Federal Receipts": "FGRECPT"},
                unit="$ billions",
                roc_eligible=True,
            ),
            ChartSpec(
                id="federal_deficit",
                title="Federal Deficit (TTM) vs. Federal Debt (% of GDP)",
                why=(
                    "Trailing 12-month sum of the deficit, which smooths out the extreme "
                    "month-to-month seasonality in the raw Treasury data (tax-season months vs. "
                    "others), shown against Federal Debt as % of GDP on a second axis. This is a "
                    "deliberate exception to this dashboard's usual single-axis rule: the "
                    "deficit is a signed flow that crosses zero, so it can't be indexed to a "
                    "common base alongside an always-positive ratio like debt-to-GDP."
                ),
                kind="deficit_debt",
                series={
                    "Federal Deficit (TTM)": "MTSDS133FMS",
                    "Federal Debt (% of GDP)": "GFDEGDQ188S",
                },
            ),
        ],
    ),
    Section(
        id="prices",
        title="Prices & Monetary Policy",
        intro="Closes the loop — the inflation and policy backdrop for everything above.",
        charts=[
            ChartSpec(
                id="cpi",
                title="CPI: Headline, Core & Trimmed Mean",
                why=(
                    "Most-watched inflation gauge. Trimmed Mean CPI (Cleveland Fed) strips out "
                    "each month's most extreme price moves entirely, rather than just excluding "
                    "food & energy like Core — often a cleaner read on underlying inflation "
                    "momentum. It only appears in the Monthly Annualized view since that's the "
                    "rate the Cleveland Fed publishes it in natively (it has no meaningful index "
                    "level, and RoC has been dropped from this chart in favor of that direct "
                    "monthly-annualized comparison)."
                ),
                kind="inflation",
                series={"CPI (Headline)": "CPIAUCSL", "CPI (Core)": "CPILFESL"},
                rate_series={"CPI (Trimmed Mean)": "TRMMEANCPIM159SFRBCLE"},
                rate_series_view="Monthly Annualized %",
                unit="Index (1982-84=100)",
            ),
            ChartSpec(
                id="pce_price_index",
                title="PCE Price Index: Headline, Core & Trimmed Mean",
                why=(
                    "The Fed's preferred inflation measure. Trimmed Mean PCE (Dallas Fed) strips "
                    "out each period's most extreme price moves entirely, rather than just "
                    "excluding food & energy like Core. It only appears in the YoY view since "
                    "that's the rate the Dallas Fed publishes it in natively (a 12-month change, "
                    "not monthly-annualized like the CPI chart's trimmed mean above) — RoC has "
                    "been dropped from this chart in favor of the Monthly Annualized view for "
                    "Headline/Core."
                ),
                kind="inflation",
                series={"PCE Price Index (Headline)": "PCEPI", "PCE Price Index (Core)": "PCEPILFE"},
                rate_series={"PCE (Trimmed Mean)": "PCETRIM12M159SFRBDAL"},
                rate_series_view="YoY %",
                unit="Index (2017=100)",
            ),
            ChartSpec(
                id="rates",
                title="Fed Funds Rate vs 10Y Treasury",
                why="Policy stance and yield curve signal.",
                series={"Fed Funds Rate": "FEDFUNDS", "10Y Treasury": "DGS10", "10Y-2Y Spread": "T10Y2Y"},
                unit="%",
            ),
            ChartSpec(
                id="m2_money_supply",
                title="M2 Money Supply",
                why=(
                    "Broad money supply, alongside M2 Velocity (nominal GDP / M2, published "
                    "directly by FRED) — the classic companion question: is money supply growth "
                    "translating into economic activity, or just accumulating? Velocity is a "
                    "different scale (a ratio near 1, vs. M2's trillions), so it's indexed to a "
                    "common start alongside M2."
                ),
                series={"M2 Money Supply": "M2SL", "M2 Velocity": "M2V"},
                unit="Index (start = 100)",
                roc_eligible=True,
                index_to_100=True,
            ),
            ChartSpec(
                id="fed_balance_sheet",
                title="Federal Reserve Balance Sheet",
                why=(
                    "Total assets held by the Fed (Treasuries, MBS, and other holdings from "
                    "QE/QT) — the balance-sheet counterpart to interest-rate policy above, and "
                    "closely tied to the M2 growth story: QE-era asset purchases were a major "
                    "driver of M2 expansion."
                ),
                series={"Fed Balance Sheet (Total Assets)": "WALCL"},
                unit="$ millions",
                roc_eligible=True,
            ),
        ],
    ),
]
