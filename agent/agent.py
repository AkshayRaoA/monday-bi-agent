import re
from difflib import get_close_matches

import pandas as pd

from services.cleaner import clean_sector

from analytics.deals import (
    active_pipeline,
    pipeline_for_sector,
    pipeline_by_sector,
    deal_data_summary
)

from analytics.work_orders import (
    execution_summary,
    financial_summary,
    delayed_work_orders,
    work_order_quality_report,
    work_orders_by_sector
)


# ============================================================
# MONEY FORMATTER
# ============================================================

def format_money(value):

    if value is None:
        return "₹0"

    try:
        value = float(value)
    except (TypeError, ValueError):
        return "Unknown"

    # Crore
    if abs(value) >= 10_000_000:
        return f"₹{value / 10_000_000:.2f} Cr"

    # Lakh
    if abs(value) >= 100_000:
        return f"₹{value / 100_000:.2f} Lakh"

    return f"₹{value:,.2f}"


# ============================================================
# NORMALIZE USER QUESTION
# ============================================================

def normalize_question(question):

    if question is None:
        return ""

    q = str(question).lower().strip()

    phrase_aliases = {

        # ----------------------------------------------------
        # PIPELINE
        # ----------------------------------------------------

        "sales funnel":
            "pipeline",

        "sales pipeline":
            "pipeline",

        "deal funnel":
            "pipeline",

        "opportunity pipeline":
            "pipeline",

        "sales opportunities":
            "pipeline",

        # ----------------------------------------------------
        # COLLECTIONS
        # ----------------------------------------------------

        "cash received":
            "collected",

        "money received":
            "collected",

        "customers paid":
            "collected",

        "customer paid":
            "collected",

        "customer payments":
            "collected",

        "amount collected":
            "collected",

        "cash collected":
            "collected",

        # ----------------------------------------------------
        # RECEIVABLES
        # ----------------------------------------------------

        "outstanding payments":
            "receivable",

        "outstanding payment":
            "receivable",

        "pending payments":
            "receivable",

        "pending payment":
            "receivable",

        "amount due":
            "receivable",

        "money due":
            "receivable",

        "yet to collect":
            "receivable",

        "still due":
            "receivable",

        # ----------------------------------------------------
        # BILLING
        # ----------------------------------------------------

        "invoiced":
            "billed",

        "invoice amount":
            "billed",

        "billing amount":
            "billed",

        "amount billed":
            "billed",

        # ----------------------------------------------------
        # DELAYS
        # ----------------------------------------------------

        "behind schedule":
            "delayed work orders",

        "late projects":
            "delayed work orders",

        "late project":
            "delayed work orders",

        "late work orders":
            "delayed work orders",

        "late work order":
            "delayed work orders",

        "overdue projects":
            "delayed work orders",

        "overdue project":
            "delayed work orders",

        # ----------------------------------------------------
        # WORK ORDERS / OPERATIONS
        # ----------------------------------------------------

        "project status":
            "work order",

        "project execution":
            "work order",

        "operations status":
            "work order",

        "operational status":
            "work order",

        # ----------------------------------------------------
        # DATA QUALITY
        # ----------------------------------------------------

        "incomplete data":
            "data quality",

        "bad data":
            "data quality",

        "data problems":
            "data quality",

        "data issues":
            "data quality",

        "missing records":
            "data quality",

        # ----------------------------------------------------
        # LEADERSHIP
        # ----------------------------------------------------

        "executive summary":
            "leadership update",

        "executive update":
            "leadership update",

        "management summary":
            "leadership update",

        "management update":
            "leadership update",

        "weekly update":
            "leadership update",

        "leadership summary":
            "leadership update"
    }

    for phrase, replacement in phrase_aliases.items():

        if phrase in q:

            q = q.replace(
                phrase,
                replacement
            )

    return q


# ============================================================
# GET AVAILABLE SECTORS
# ============================================================

def get_available_sectors(deals_df):

    if "clean_sector" not in deals_df.columns:
        return []

    sectors = (
        deals_df["clean_sector"]
        .dropna()
        .astype(str)
        .str.lower()
        .str.strip()
        .unique()
        .tolist()
    )

    return sorted(sectors)


# ============================================================
# DETECT SECTOR
# ============================================================

def detect_sector(question, deals_df):

    question = str(question).lower()

    sectors = get_available_sectors(
        deals_df
    )

    # --------------------------------------------------------
    # EXACT MATCH
    # --------------------------------------------------------

    for sector in sectors:

        if sector in question:
            return sector


    # --------------------------------------------------------
    # COMMON ALIASES
    # --------------------------------------------------------

    aliases = {

        "renewable":
            "renewables",

        "solar":
            "renewables",

        "wind":
            "renewables",

        "power line":
            "powerline",

        "railway":
            "railways",

        "rail":
            "railways",

        "security":
            "security and surveillance",

        "surveillance":
            "security and surveillance",

        "construction":
            "construction",

        "mining":
            "mining",

        "aviation":
            "aviation",

        "manufacturing":
            "manufacturing",

        "tender":
            "tender",

        "dsp":
            "dsp"
    }


    for phrase, sector in aliases.items():

        if phrase in question:

            if sector in sectors:
                return sector


    # --------------------------------------------------------
    # FUZZY MATCHING FOR TYPOS
    # --------------------------------------------------------

    words = re.findall(
        r"[a-zA-Z]+",
        question
    )

    single_word_sectors = [
        sector
        for sector in sectors
        if " " not in sector
    ]

    for word in words:

        matches = get_close_matches(
            word,
            single_word_sectors,
            n=1,
            cutoff=0.78
        )

        if matches:
            return matches[0]

    return None


# ============================================================
# CURRENT QUARTER DATES
# ============================================================

def current_quarter_dates():

    today = pd.Timestamp.today().normalize()

    quarter = (
        (today.month - 1) // 3
    ) + 1

    start_month = (
        (quarter - 1) * 3
    ) + 1

    start = pd.Timestamp(
        year=today.year,
        month=start_month,
        day=1
    )

    if quarter == 1:
        end = pd.Timestamp(
            year=today.year,
            month=3,
            day=31
        )

    elif quarter == 2:
        end = pd.Timestamp(
            year=today.year,
            month=6,
            day=30
        )

    elif quarter == 3:
        end = pd.Timestamp(
            year=today.year,
            month=9,
            day=30
        )

    else:
        end = pd.Timestamp(
            year=today.year,
            month=12,
            day=31
        )

    return (
        quarter,
        today.year,
        start,
        end
    )


# ============================================================
# PIPELINE THIS QUARTER
# ============================================================

def pipeline_this_quarter(
    deals_df,
    sector=None
):

    quarter, year, start, end = (
        current_quarter_dates()
    )

    df = deals_df.copy()

    # Only Open + On Hold deals
    df = df[
        df[
            "clean_deal_status"
        ].isin(
            [
                "open",
                "on hold"
            ]
        )
    ]

    # Filter by sector if requested
    if sector:

        sector = clean_sector(
            sector
        )

        df = df[
            df[
                "clean_sector"
            ] == sector
        ]


    missing_close_dates = int(
        df[
            "clean_tentative_close_date"
        ].isna().sum()
    )


    dated = df[
        df[
            "clean_tentative_close_date"
        ].notna()
    ].copy()


    quarter_df = dated[

        (
            dated[
                "clean_tentative_close_date"
            ] >= start
        )

        &

        (
            dated[
                "clean_tentative_close_date"
            ] <= end
        )

    ]


    values = quarter_df[
        "clean_deal_value"
    ].dropna()


    return {

        "quarter":
            quarter,

        "year":
            year,

        "deal_count":
            len(quarter_df),

        "known_pipeline":
            float(values.sum()),

        "deals_with_value":
            len(values),

        "missing_value":
            int(
                quarter_df[
                    "clean_deal_value"
                ].isna().sum()
            ),

        "active_deals_missing_close_date":
            missing_close_dates
    }


# ============================================================
# PIPELINE THIS MONTH
# ============================================================

def pipeline_this_month(
    deals_df,
    sector=None
):

    today = pd.Timestamp.today().normalize()

    df = deals_df[
        deals_df[
            "clean_deal_status"
        ].isin(
            [
                "open",
                "on hold"
            ]
        )
    ].copy()


    if sector:

        sector = clean_sector(
            sector
        )

        df = df[
            df[
                "clean_sector"
            ] == sector
        ]


    missing_close_dates = int(
        df[
            "clean_tentative_close_date"
        ].isna().sum()
    )


    dated = df[
        df[
            "clean_tentative_close_date"
        ].notna()
    ].copy()


    month_df = dated[

        (
            dated[
                "clean_tentative_close_date"
            ].dt.year
            == today.year
        )

        &

        (
            dated[
                "clean_tentative_close_date"
            ].dt.month
            == today.month
        )

    ]


    values = month_df[
        "clean_deal_value"
    ].dropna()


    return {

        "month":
            today.strftime(
                "%B %Y"
            ),

        "deal_count":
            len(month_df),

        "known_pipeline":
            float(values.sum()),

        "deals_with_value":
            len(values),

        "missing_value":
            int(
                month_df[
                    "clean_deal_value"
                ].isna().sum()
            ),

        "active_deals_missing_close_date":
            missing_close_dates
    }


# ============================================================
# LEADERSHIP UPDATE
# ============================================================

def leadership_update(
    deals_df,
    work_orders_df
):

    pipeline = active_pipeline(
        deals_df
    )

    execution = execution_summary(
        work_orders_df
    )

    finance = financial_summary(
        work_orders_df
    )

    delayed = delayed_work_orders(
        work_orders_df
    )

    quality = work_order_quality_report(
        work_orders_df
    )

    sector_pipeline = pipeline_by_sector(
        deals_df
    )


    valid_sectors = sector_pipeline[
        sector_pipeline[
            "clean_sector"
        ].notna()
    ]


    if len(valid_sectors) > 0:

        top_sector = valid_sectors.iloc[0]

        top_sector_text = (
            f"{str(top_sector['clean_sector']).title()} "
            f"has the largest known active pipeline at "
            f"{format_money(top_sector['known_pipeline_value'])}."
        )

    else:

        top_sector_text = (
            "No usable sector-level pipeline data is available."
        )


    return f"""
### Leadership Update

**Sales**
- Active deals: **{pipeline['active_deal_count']}**
- Known active pipeline: **{format_money(pipeline['known_pipeline_value'])}**
- Active deals missing values: **{pipeline['deals_missing_value']}**
- {top_sector_text}

**Operations**
- Total work orders: **{execution['total_work_orders']}**
- Completed: **{execution['completed']}**
- Ongoing: **{execution['ongoing']}**
- Not started: **{execution['not_started']}**
- Paused / struck: **{execution['paused']}**
- Potentially overdue work orders: **{len(delayed)}**

**Finance**
- Known contract value: **{format_money(finance['total_contract_value'])}**
- Known billed amount: **{format_money(finance['total_billed'])}**
- Known collected amount: **{format_money(finance['total_collected'])}**
- Known receivables: **{format_money(finance['total_receivable'])}**
- Known amount still to bill: **{format_money(finance['total_to_bill'])}**

**Data Quality**
- Missing probable end dates: **{quality['missing_end_date']}**
- Missing collection amounts: **{quality['missing_collection_amount']}**
- Missing billing status: **{quality['missing_billing_status']}**
- Negative receivable records: **{quality['negative_receivables']}**
- Negative amount-to-bill records: **{quality['negative_amount_to_bill']}**
""".strip()


# ============================================================
# MAIN BUSINESS AGENT
# ============================================================

def ask_business_agent(
    question,
    deals_df,
    work_orders_df
):

    q = normalize_question(
        question
    )

    sector = detect_sector(
        q,
        deals_df
    )


    # ========================================================
    # EMPTY QUESTION
    # ========================================================

    if not q:

        return (
            "Please enter a business question."
        )


    # ========================================================
    # GREETINGS
    # ========================================================

    if q in [
        "hi",
        "hello",
        "hey",
        "good morning",
        "good afternoon",
        "good evening"
    ]:

        return (
            "Hello! Ask me about sales pipeline, sectors, "
            "work orders, billing, collections, receivables, "
            "delays, data quality, or leadership updates."
        )


    # ========================================================
    # LEADERSHIP UPDATE
    # ========================================================

    if (
        "leadership update" in q
        or
        "executive update" in q
        or
        "management update" in q
    ):

        return leadership_update(
            deals_df,
            work_orders_df
        )


    # ========================================================
    # DATA QUALITY
    # ========================================================

    if (
        "data quality" in q
        or
        "missing data" in q
        or
        "can i trust" in q
        or
        "quality issues" in q
        or
        "quality problem" in q
    ):

        deal_summary = deal_data_summary(
            deals_df
        )

        wo_quality = (
            work_order_quality_report(
                work_orders_df
            )
        )

        missing_sector = int(
            deals_df[
                "clean_sector"
            ].isna().sum()
        )

        missing_close_dates = int(
            deals_df[
                "clean_tentative_close_date"
            ].isna().sum()
        )


        return (
            "### Data Quality Summary\n\n"
            f"**Deals**\n"
            f"- Valid deal records: **{deal_summary['total_records']}**\n"
            f"- Missing deal values: **{deal_summary['records_missing_value']}**\n"
            f"- Missing sector: **{missing_sector}**\n"
            f"- Missing tentative close dates: **{missing_close_dates}**\n\n"

            f"**Work Orders**\n"
            f"- Missing execution status: "
            f"**{wo_quality['missing_execution_status']}**\n"
            f"- Missing sector: "
            f"**{wo_quality['missing_sector']}**\n"
            f"- Missing probable end dates: "
            f"**{wo_quality['missing_end_date']}**\n"
            f"- Missing collection amounts: "
            f"**{wo_quality['missing_collection_amount']}**\n"
            f"- Missing billing status: "
            f"**{wo_quality['missing_billing_status']}**\n"
            f"- Negative receivables: "
            f"**{wo_quality['negative_receivables']}**\n"
            f"- Negative amount-to-bill records: "
            f"**{wo_quality['negative_amount_to_bill']}**\n\n"

            "Missing financial values are treated as unknown, "
            "not zero."
        )


    # ========================================================
    # PIPELINE THIS QUARTER
    # ========================================================

    if (
        "pipeline" in q
        and
        (
            "quarter" in q
            or
            "this q" in q
        )
    ):

        result = pipeline_this_quarter(
            deals_df,
            sector
        )


        if sector:

            sector_text = (
                f" for **{sector.title()}**"
            )

        else:

            sector_text = ""


        return (
            f"### Q{result['quarter']} {result['year']} Pipeline"
            f"{sector_text}\n\n"

            f"- Deals expected to close this quarter: "
            f"**{result['deal_count']}**\n"

            f"- Known pipeline value: "
            f"**{format_money(result['known_pipeline'])}**\n"

            f"- Deals with recorded values: "
            f"**{result['deals_with_value']}**\n"

            f"- Deals missing values: "
            f"**{result['missing_value']}**\n\n"

            f"**Data caveat:** "
            f"{result['active_deals_missing_close_date']} "
            f"active deals are missing tentative close dates "
            f"and cannot be reliably included in quarter analysis."
        )


    # ========================================================
    # PIPELINE THIS MONTH
    # ========================================================

    if (
        "pipeline" in q
        and
        "month" in q
    ):

        result = pipeline_this_month(
            deals_df,
            sector
        )


        if sector:

            sector_text = (
                f" for **{sector.title()}**"
            )

        else:

            sector_text = ""


        return (
            f"### {result['month']} Pipeline"
            f"{sector_text}\n\n"

            f"- Deals expected to close: "
            f"**{result['deal_count']}**\n"

            f"- Known pipeline value: "
            f"**{format_money(result['known_pipeline'])}**\n"

            f"- Deals with recorded values: "
            f"**{result['deals_with_value']}**\n"

            f"- Deals missing values: "
            f"**{result['missing_value']}**\n\n"

            f"**Data caveat:** "
            f"{result['active_deals_missing_close_date']} active deals "
            f"are missing tentative close dates."
        )


    # ========================================================
    # SPECIFIC SECTOR PIPELINE
    # ========================================================

    if (
        "pipeline" in q
        and
        sector is not None
    ):

        result = pipeline_for_sector(
            deals_df,
            sector
        )


        if result[
            "active_deal_count"
        ] == 0:

            return (
                f"No active pipeline records were found "
                f"for **{sector.title()}**."
            )


        return (
            f"### {sector.title()} Pipeline\n\n"

            f"- Active deals: "
            f"**{result['active_deal_count']}**\n"

            f"- Known active pipeline: "
            f"**{format_money(result['known_pipeline_value'])}**\n"

            f"- Deals with recorded values: "
            f"**{result['deals_with_value']}**\n"

            f"- Deals missing values: "
            f"**{result['deals_missing_value']}**\n\n"

            "The actual pipeline may be higher because "
            "missing deal values are treated as unknown, not zero."
        )


    # ========================================================
    # PIPELINE BY SECTOR
    # ========================================================

    if (
        (
            "sector" in q
            or
            "sectors" in q
        )
        and
        (
            "pipeline" in q
            or
            "largest" in q
            or
            "highest" in q
            or
            "compare" in q
            or
            "strongest" in q
        )
    ):

        result = pipeline_by_sector(
            deals_df
        )

        result = result[
            result[
                "clean_sector"
            ].notna()
        ]


        if len(result) == 0:

            return (
                "No usable sector-level pipeline data "
                "is currently available."
            )


        lines = []


        for _, row in (
            result
            .head(10)
            .iterrows()
        ):

            lines.append(

                f"- **{str(row['clean_sector']).title()}**: "
                f"{int(row['deal_count'])} active deals, "
                f"{format_money(row['known_pipeline_value'])}"

            )


        return (
            "### Active Pipeline by Sector\n\n"
            +
            "\n".join(lines)
        )


    # ========================================================
    # ACTIVE PIPELINE
    # ========================================================

    if "pipeline" in q:

        result = active_pipeline(
            deals_df
        )

        return (
            "### Active Sales Pipeline\n\n"

            f"- Active deals: "
            f"**{result['active_deal_count']}**\n"

            f"- Known pipeline value: "
            f"**{format_money(result['known_pipeline_value'])}**\n"

            f"- Deals with recorded values: "
            f"**{result['deals_with_value']}**\n"

            f"- Deals missing values: "
            f"**{result['deals_missing_value']}**\n\n"

            "Active pipeline currently means deals with "
            "status **Open** or **On Hold**. "
            "Won and Dead deals are excluded."
        )


    # ========================================================
    # RECEIVABLES
    # ========================================================

    if (
        "receivable" in q
        or
        "waiting to collect" in q
        or
        "outstanding collection" in q
    ):

        finance = financial_summary(
            work_orders_df
        )

        return (
            "### Receivables\n\n"

            f"Known receivables are "
            f"**{format_money(finance['total_receivable'])}**.\n\n"

            f"There are **{finance['negative_receivables']}** "
            f"records with negative receivable values. "
            f"These may represent adjustments, over-collection, "
            f"or data-quality issues and should be reviewed."
        )


    # ========================================================
    # COLLECTIONS
    # ========================================================

    if (
        "collected" in q
        or
        "collection amount" in q
    ):

        finance = financial_summary(
            work_orders_df
        )

        quality = (
            work_order_quality_report(
                work_orders_df
            )
        )

        return (
            "### Collections\n\n"

            f"The known collected amount is "
            f"**{format_money(finance['total_collected'])}**.\n\n"

            f"**Data caveat:** "
            f"{quality['missing_collection_amount']} work orders "
            f"do not have a collection amount recorded."
        )


    # ========================================================
    # BILLING
    # ========================================================

    if (
        "billed" in q
        or
        "billing" in q
    ):

        finance = financial_summary(
            work_orders_df
        )

        quality = (
            work_order_quality_report(
                work_orders_df
            )
        )

        return (
            "### Billing\n\n"

            f"- Known billed amount: "
            f"**{format_money(finance['total_billed'])}**\n"

            f"- Known amount still to bill: "
            f"**{format_money(finance['total_to_bill'])}**\n\n"

            f"**Data caveat:** "
            f"{quality['missing_billing_status']} work orders "
            f"are missing billing status."
        )


    # ========================================================
    # CONTRACT VALUE
    # ========================================================

    if (
        "contract value" in q
        or
        "work order value" in q
    ):

        finance = financial_summary(
            work_orders_df
        )

        return (
            "### Work Order Contract Value\n\n"

            f"The known total contract value is "
            f"**{format_money(finance['total_contract_value'])}**."
        )


    # ========================================================
    # DELAYED WORK ORDERS
    # ========================================================

    if (
        "delayed" in q
        or
        "overdue" in q
        or
        "late work order" in q
    ):

        delayed = delayed_work_orders(
            work_orders_df
        )


        if len(delayed) == 0:

            return (
                "No potentially delayed work orders were found."
            )


        most_overdue = (
            delayed
            .sort_values(
                "days_overdue",
                ascending=False
            )
            .head(5)
        )


        lines = []


        for _, row in (
            most_overdue.iterrows()
        ):

            name = row.get(
                "Item Name",
                "Unknown"
            )

            sector_name = row.get(
                "Sector",
                "Unknown"
            )

            days = int(
                row[
                    "days_overdue"
                ]
            )


            lines.append(
                f"- **{name}** ({sector_name}): "
                f"{days} days overdue"
            )


        return (
            f"### Delayed Work Orders\n\n"

            f"There are **{len(delayed)}** potentially "
            f"delayed work orders.\n\n"

            f"**Most overdue examples:**\n"
            +
            "\n".join(lines)
            +
            "\n\nA work order is considered potentially delayed "
            "when its probable end date has passed and its "
            "execution status is not Completed."
        )


    # ========================================================
    # WORK ORDER STATUS / OPERATIONS
    # ========================================================

    if (
        "work order" in q
        or
        "execution" in q
        or
        "projects" in q
        or
        "operations" in q
    ):

        result = execution_summary(
            work_orders_df
        )

        return (
            "### Work Order Execution\n\n"

            f"- Total work orders: "
            f"**{result['total_work_orders']}**\n"

            f"- Completed: "
            f"**{result['completed']}**\n"

            f"- Ongoing: "
            f"**{result['ongoing']}**\n"

            f"- Executed until current month: "
            f"**{result['executed_until_current_month']}**\n"

            f"- Not started: "
            f"**{result['not_started']}**\n"

            f"- Partially completed: "
            f"**{result['partial_completed']}**\n"

            f"- Paused / struck: "
            f"**{result['paused']}**\n"

            f"- Missing execution status: "
            f"**{result['missing_status']}**"
        )


    # ========================================================
    # AMBIGUOUS REVENUE QUESTION
    # ========================================================

    if "revenue" in q:

        return (
            "When you say **revenue**, which metric do you mean?\n\n"
            "- Work-order contract value\n"
            "- Billed amount\n"
            "- Collected amount\n"
            "- Receivables\n"
            "- Sales pipeline\n\n"
            "For example: **How much have we billed?**"
        )


    # ========================================================
    # AMBIGUOUS SALES QUESTION
    # ========================================================

    if (
        "sales" in q
        and
        "pipeline" not in q
    ):

        return (
            "What part of sales would you like to analyse?\n\n"
            "- Active sales pipeline\n"
            "- Pipeline by sector\n"
            "- Pipeline this quarter\n"
            "- Pipeline this month\n\n"
            "For example: "
            "**How is our sales pipeline this quarter?**"
        )


    # ========================================================
    # AMBIGUOUS PERFORMANCE QUESTION
    # ========================================================

    if (
        "performance" in q
        and
        sector is None
    ):

        return (
            "Which type of performance would you like to see?\n\n"
            "- Sales pipeline performance\n"
            "- Work-order execution\n"
            "- Billing and collections\n"
            "- Sector performance"
        )


    # ========================================================
    # UNKNOWN QUESTION / HELP
    # ========================================================

    available_sectors = ", ".join(
        get_available_sectors(
            deals_df
        )
    )


    return (
        "I couldn't confidently determine which business metric "
        "you want.\n\n"

        "Try questions such as:\n\n"
        "- How much active pipeline do we have?\n"
        "- How is the renewables pipeline looking?\n"
        "- What's our pipeline this quarter?\n"
        "- What's our pipeline this month?\n"
        "- Which sectors have the largest pipeline?\n"
        "- How much money have we collected?\n"
        "- How much is receivable?\n"
        "- How much have we billed?\n"
        "- How are our work orders doing?\n"
        "- Which work orders are delayed?\n"
        "- What data quality issues do we have?\n"
        "- Prepare a leadership update.\n\n"

        f"**Available deal sectors:** {available_sectors}"
    )