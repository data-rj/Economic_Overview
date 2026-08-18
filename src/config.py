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
                why="Headline size/trend of the economy.",
                series={"Real GDP": "GDPC1"},
                unit="$ billions (2017 chained)",
                roc_eligible=True,
            ),
            ChartSpec(
                id="gdp_growth",
                title="Real GDP Growth (Quarterly, Annualized)",
                why="The number everyone quotes each release.",
                series={"Real GDP Growth (Annualized)": "A191RL1Q225SBEA"},
                unit="%",
            ),
            ChartSpec(
                id="gdp_contributions",
                title="Contributions to GDP Growth by Component",
                why="Shows what is driving growth — PCE, Investment, Net Exports, Government.",
                placeholder=True,
                placeholder_note=(
                    "NIPA \"contribution to % change\" series (BEA Table 1.1.2, mirrored on FRED) — "
                    "confirm exact FRED series IDs before wiring up."
                ),
            ),
            ChartSpec(
                id="gdp_deflator",
                title="GDP Price Deflator",
                why="Separates real growth from inflation.",
                series={"GDP Deflator": "GDPDEF"},
                unit="Index (2017=100)",
                roc_eligible=True,
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
                why="Headline labor market slack.",
                series={"Unemployment Rate": "UNRATE"},
                unit="%",
            ),
            ChartSpec(
                id="payrolls",
                title="Nonfarm Payrolls",
                why="Job creation pace.",
                series={"Nonfarm Payrolls": "PAYEMS"},
                unit="thousands of jobs",
                roc_eligible=True,
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
                why="Core consumer spending.",
                series={"Real PCE": "PCEC96"},
                unit="$ billions (2017 chained)",
                roc_eligible=True,
            ),
            ChartSpec(
                id="pce_by_category",
                title="PCE by Category",
                why="Where consumers are spending: durables, nondurables, services.",
                series={"Durable Goods": "PCEDG", "Nondurable Goods": "PCEND", "Services": "PCES"},
                unit="$ billions (nominal)",
                roc_eligible=True,
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
                why="Higher-frequency read on consumer activity.",
                series={"Retail Sales": "RSAFS"},
                unit="$ millions",
                roc_eligible=True,
            ),
            ChartSpec(
                id="household_debt_service",
                title="Household Debt Service Ratio",
                why="Leverage / consumer health angle.",
                series={"Household Debt Service Ratio": "TDSP"},
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
                why="Bottom-line health of the corporate sector.",
                series={"Corporate Profits After Tax": "CP"},
                unit="$ billions",
                roc_eligible=True,
            ),
            ChartSpec(
                id="industrial_production",
                title="Industrial Production Index",
                why="Real output of the business sector.",
                series={"Industrial Production Index": "INDPRO"},
                unit="Index (2017=100)",
                roc_eligible=True,
            ),
            ChartSpec(
                id="capacity_utilization",
                title="Capacity Utilization",
                why="Slack vs tightness in production.",
                series={"Capacity Utilization": "TCU"},
                unit="%",
            ),
            ChartSpec(
                id="corp_bond_spread",
                title="Corporate Bond Spread",
                why="Market-based read on corporate stress / risk appetite.",
                series={"Baa − 10Y Treasury Spread": "BAA10Y"},
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
                title="Federal Deficit",
                why="The gap, and its trajectory.",
                series={"Federal Surplus/Deficit": "MTSDS133FMS"},
                unit="$ millions",
            ),
            ChartSpec(
                id="debt_to_gdp",
                title="Federal Debt Held by Public, % of GDP",
                why="Long-run fiscal sustainability.",
                series={"Federal Debt (% of GDP)": "GFDEGDQ188S"},
                unit="%",
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
                title="CPI: Headline vs Core",
                why="Most-watched inflation gauge.",
                series={"CPI (Headline)": "CPIAUCSL", "CPI (Core)": "CPILFESL"},
                unit="Index (1982-84=100)",
                roc_eligible=True,
            ),
            ChartSpec(
                id="pce_price_index",
                title="PCE Price Index: Headline vs Core",
                why="The Fed's preferred inflation measure.",
                series={"PCE Price Index (Headline)": "PCEPI", "PCE Price Index (Core)": "PCEPILFE"},
                unit="Index (2017=100)",
                roc_eligible=True,
            ),
            ChartSpec(
                id="rates",
                title="Fed Funds Rate vs 10Y Treasury",
                why="Policy stance and yield curve signal.",
                series={"Fed Funds Rate": "FEDFUNDS", "10Y Treasury": "DGS10", "10Y-2Y Spread": "T10Y2Y"},
                unit="%",
            ),
        ],
    ),
]
