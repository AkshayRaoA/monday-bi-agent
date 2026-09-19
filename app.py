import streamlit as st

from services.monday_client import (
    get_board_items,
    board_to_dataframe,
    get_config_value
)

from analytics.deals import (
    prepare_deals,
    active_pipeline,
    pipeline_by_sector
)

from analytics.work_orders import (
    prepare_work_orders,
    execution_summary,
    financial_summary,
    work_orders_by_sector,
    delayed_work_orders,
    work_order_quality_report
)

from agent.agent import (
    ask_business_agent
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Monday BI Agent",
    page_icon="📊",
    layout="wide"
)


# ============================================================
# FORMAT MONEY
# ============================================================

def format_money(value):

    if value is None:
        return "₹0"

    try:

        value = float(
            value
        )

    except (
        TypeError,
        ValueError
    ):

        return "Unknown"


    if abs(value) >= 10_000_000:

        return (
            f"₹"
            f"{value / 10_000_000:.2f} Cr"
        )


    if abs(value) >= 100_000:

        return (
            f"₹"
            f"{value / 100_000:.2f} Lakh"
        )


    return f"₹{value:,.2f}"


# ============================================================
# LOAD DEALS
# ============================================================

@st.cache_data(
    ttl=60
)
def load_deals():

    board_id = get_config_value(
        "DEALS_BOARD_ID"
    )


    if not board_id:

        raise RuntimeError(
            "DEALS_BOARD_ID is missing."
        )


    raw_data = get_board_items(
        board_id
    )


    df = board_to_dataframe(
        raw_data
    )


    return prepare_deals(
        df
    )


# ============================================================
# LOAD WORK ORDERS
# ============================================================

@st.cache_data(
    ttl=60
)
def load_work_orders():

    board_id = get_config_value(
        "WORK_ORDERS_BOARD_ID"
    )


    if not board_id:

        raise RuntimeError(
            "WORK_ORDERS_BOARD_ID is missing."
        )


    raw_data = get_board_items(
        board_id
    )


    df = board_to_dataframe(
        raw_data
    )


    return prepare_work_orders(
        df
    )


# ============================================================
# TITLE
# ============================================================

st.title(
    "📊 Monday.com Business Intelligence Agent"
)

st.caption(
    "Live business intelligence from "
    "Deals and Work Orders"
)


# ============================================================
# CHECK CONFIGURATION
# ============================================================

token = get_config_value(
    "MONDAY_API_TOKEN"
)

deals_board_id = get_config_value(
    "DEALS_BOARD_ID"
)

work_orders_board_id = (
    get_config_value(
        "WORK_ORDERS_BOARD_ID"
    )
)


missing_config = []


if not token:

    missing_config.append(
        "MONDAY_API_TOKEN"
    )


if not deals_board_id:

    missing_config.append(
        "DEALS_BOARD_ID"
    )


if not work_orders_board_id:

    missing_config.append(
        "WORK_ORDERS_BOARD_ID"
    )


if missing_config:

    st.error(
        "Missing configuration: "
        +
        ", ".join(
            missing_config
        )
    )


    st.info(
        "When running locally, add these values "
        "to `.env`. When deployed on Streamlit "
        "Cloud, add them under App → Settings → Secrets."
    )


    st.stop()


# ============================================================
# LOAD MONDAY DATA
# ============================================================

try:

    with st.spinner(
        "Loading live monday.com data..."
    ):

        deals_df = load_deals()

        work_orders_df = (
            load_work_orders()
        )


except Exception as error:

    st.error(
        "Could not load monday.com data."
    )


    st.error(
        str(error)
    )


    st.info(
        "If this works locally but not on "
        "Streamlit Cloud, check the values in "
        "App Settings → Secrets."
    )


    st.stop()


# ============================================================
# CONNECTION STATUS + REFRESH
# ============================================================

status_col, refresh_col = (
    st.columns(
        [4, 1]
    )
)


with status_col:

    st.success(
        f"🟢 Connected to monday.com | "
        f"{len(deals_df)} valid deals | "
        f"{len(work_orders_df)} work orders"
    )


with refresh_col:

    if st.button(
        "🔄 Refresh Data",
        width="stretch"
    ):

        st.cache_data.clear()

        st.rerun()


# ============================================================
# TABS
# ============================================================

chat_tab, dashboard_tab = (
    st.tabs(
        [
            "💬 Ask the BI Agent",
            "📊 Dashboard"
        ]
    )
)


# ============================================================
# CHAT TAB
# ============================================================

with chat_tab:

    st.subheader(
        "Ask a business question"
    )


    st.write(
        "Ask about sales pipeline, sectors, "
        "work orders, billing, collections, "
        "delays, or data quality."
    )


    # --------------------------------------------------------
    # EXAMPLE QUESTIONS
    # --------------------------------------------------------

    with st.expander(
        "💡 Example questions"
    ):

        st.markdown(
            """
- How much active pipeline do we have?
- How is the renewables pipeline looking?
- What's our pipeline this quarter?
- What's our pipeline this month?
- Which sectors have the largest pipeline?
- How much money have we collected?
- How much is receivable?
- How much have we billed?
- How are our work orders doing?
- Which projects are behind schedule?
- What data quality issues should leadership know about?
- Prepare a leadership update.
"""
        )


    # --------------------------------------------------------
    # SESSION CHAT HISTORY
    # --------------------------------------------------------

    if (
        "messages"
        not in st.session_state
    ):

        st.session_state.messages = [

            {
                "role":
                    "assistant",

                "content":
                    "Hello! I'm your Business "
                    "Intelligence Agent. Ask me about "
                    "pipeline, work orders, billing, "
                    "collections, delays, sectors, "
                    "or data quality."
            }

        ]


    # --------------------------------------------------------
    # DISPLAY CHAT HISTORY
    # --------------------------------------------------------

    for message in (
        st.session_state.messages
    ):

        with st.chat_message(
            message[
                "role"
            ]
        ):

            st.markdown(
                message[
                    "content"
                ]
            )


    # --------------------------------------------------------
    # CHAT INPUT
    # --------------------------------------------------------

    question = st.chat_input(
        "Ask a business question..."
    )


    if question:

        st.session_state.messages.append(
            {
                "role":
                    "user",

                "content":
                    question
            }
        )


        with st.chat_message(
            "user"
        ):

            st.markdown(
                question
            )


        with st.chat_message(
            "assistant"
        ):

            with st.spinner(
                "Analyzing live monday.com data..."
            ):

                try:

                    answer = (
                        ask_business_agent(
                            question,
                            deals_df,
                            work_orders_df
                        )
                    )

                except Exception as error:

                    answer = (
                        "I encountered an error "
                        "while analysing the data:\n\n"
                        f"`{error}`"
                    )


            st.markdown(
                answer
            )


        st.session_state.messages.append(
            {
                "role":
                    "assistant",

                "content":
                    answer
            }
        )


    # --------------------------------------------------------
    # BUTTONS
    # --------------------------------------------------------

    st.divider()


    button_col1, button_col2 = (
        st.columns(
            [1, 4]
        )
    )


    with button_col1:

        leadership_button = (
            st.button(
                "📋 Leadership Update",
                width="stretch"
            )
        )


    if leadership_button:

        answer = ask_business_agent(
            "Prepare a leadership update",
            deals_df,
            work_orders_df
        )


        st.session_state.messages.append(
            {
                "role":
                    "user",

                "content":
                    "Prepare a leadership update"
            }
        )


        st.session_state.messages.append(
            {
                "role":
                    "assistant",

                "content":
                    answer
            }
        )


        st.rerun()


    with button_col2:

        if st.button(
            "🗑️ Clear Chat"
        ):

            st.session_state.messages = [

                {
                    "role":
                        "assistant",

                    "content":
                        "Chat cleared. What would "
                        "you like to know?"
                }

            ]


            st.rerun()


# ============================================================
# DASHBOARD TAB
# ============================================================

with dashboard_tab:

    # ========================================================
    # SALES PIPELINE
    # ========================================================

    st.header(
        "Sales Pipeline"
    )


    pipeline = active_pipeline(
        deals_df
    )


    col1, col2, col3, col4 = (
        st.columns(
            4
        )
    )


    col1.metric(
        "Active Deals",
        pipeline[
            "active_deal_count"
        ]
    )


    col2.metric(
        "Known Active Pipeline",
        format_money(
            pipeline[
                "known_pipeline_value"
            ]
        )
    )


    col3.metric(
        "Deals With Value",
        pipeline[
            "deals_with_value"
        ]
    )


    col4.metric(
        "Missing Deal Values",
        pipeline[
            "deals_missing_value"
        ]
    )


    # ========================================================
    # PIPELINE BY SECTOR
    # ========================================================

    st.subheader(
        "Pipeline by Sector"
    )


    sector_pipeline = (
        pipeline_by_sector(
            deals_df
        )
    )


    sector_display = (
        sector_pipeline.copy()
    )


    sector_display[
        "clean_sector"
    ] = sector_display[
        "clean_sector"
    ].fillna(
        "Unknown / Missing"
    )


    sector_display[
        "known_pipeline_value"
    ] = sector_display[
        "known_pipeline_value"
    ].apply(
        format_money
    )


    sector_display = (
        sector_display.rename(
            columns={
                "clean_sector":
                    "Sector",

                "deal_count":
                    "Active Deals",

                "known_pipeline_value":
                    "Known Pipeline",

                "deals_with_value":
                    "Deals With Value"
            }
        )
    )


    st.dataframe(
        sector_display,
        width="stretch",
        hide_index=True
    )


    # ========================================================
    # WORK ORDER EXECUTION
    # ========================================================

    st.header(
        "Work Order Execution"
    )


    execution = execution_summary(
        work_orders_df
    )


    col1, col2, col3, col4 = (
        st.columns(
            4
        )
    )


    col1.metric(
        "Total Work Orders",
        execution[
            "total_work_orders"
        ]
    )


    col2.metric(
        "Completed",
        execution[
            "completed"
        ]
    )


    col3.metric(
        "Ongoing",
        execution[
            "ongoing"
        ]
    )


    col4.metric(
        "Not Started",
        execution[
            "not_started"
        ]
    )


    col1, col2, col3 = (
        st.columns(
            3
        )
    )


    col1.metric(
        "Executed Until Current Month",
        execution[
            "executed_until_current_month"
        ]
    )


    col2.metric(
        "Partially Completed",
        execution[
            "partial_completed"
        ]
    )


    col3.metric(
        "Paused / Struck",
        execution[
            "paused"
        ]
    )


    # ========================================================
    # FINANCIAL OVERVIEW
    # ========================================================

    st.header(
        "Financial Overview"
    )


    finance = financial_summary(
        work_orders_df
    )


    col1, col2, col3 = (
        st.columns(
            3
        )
    )


    col1.metric(
        "Known Contract Value",
        format_money(
            finance[
                "total_contract_value"
            ]
        )
    )


    col2.metric(
        "Known Billed",
        format_money(
            finance[
                "total_billed"
            ]
        )
    )


    col3.metric(
        "Known Collected",
        format_money(
            finance[
                "total_collected"
            ]
        )
    )


    col1, col2 = st.columns(
        2
    )


    col1.metric(
        "Known Receivable",
        format_money(
            finance[
                "total_receivable"
            ]
        )
    )


    col2.metric(
        "Known Amount To Bill",
        format_money(
            finance[
                "total_to_bill"
            ]
        )
    )


    # ========================================================
    # WORK ORDERS BY SECTOR
    # ========================================================

    st.subheader(
        "Work Orders by Sector"
    )


    sector_work_orders = (
        work_orders_by_sector(
            work_orders_df
        )
    )


    wo_display = (
        sector_work_orders.copy()
    )


    wo_display = (
        wo_display.rename(
            columns={
                "clean_sector":
                    "Sector",

                "work_orders":
                    "Work Orders",

                "contract_value":
                    "Contract Value",

                "billed":
                    "Billed",

                "collected":
                    "Collected",

                "receivable":
                    "Receivable"
            }
        )
    )


    for column in [
        "Contract Value",
        "Billed",
        "Collected",
        "Receivable"
    ]:

        wo_display[
            column
        ] = wo_display[
            column
        ].apply(
            format_money
        )


    st.dataframe(
        wo_display,
        width="stretch",
        hide_index=True
    )


    # ========================================================
    # DELAYED WORK ORDERS
    # ========================================================

    st.header(
        "⚠️ Delayed Work Orders"
    )


    delayed = delayed_work_orders(
        work_orders_df
    )


    st.metric(
        "Potentially Delayed Work Orders",
        len(
            delayed
        )
    )


    if len(
        delayed
    ) > 0:

        columns = [
            "Item Name",
            "Sector",
            "Execution Status",
            "Probable End Date",
            "days_overdue"
        ]


        existing_columns = [

            column

            for column in columns

            if column
            in delayed.columns

        ]


        delayed_display = (
            delayed[
                existing_columns
            ].copy()
        )


        delayed_display = (
            delayed_display.rename(
                columns={
                    "Item Name":
                        "Work Order",

                    "Probable End Date":
                        "Expected End",

                    "days_overdue":
                        "Days Overdue"
                }
            )
        )


        st.dataframe(
            delayed_display,
            width="stretch",
            hide_index=True
        )


    # ========================================================
    # DATA QUALITY
    # ========================================================

    st.header(
        "Data Quality"
    )


    quality = (
        work_order_quality_report(
            work_orders_df
        )
    )


    col1, col2, col3 = (
        st.columns(
            3
        )
    )


    col1.metric(
        "Missing End Dates",
        quality[
            "missing_end_date"
        ]
    )


    col2.metric(
        "Missing Collection Amount",
        quality[
            "missing_collection_amount"
        ]
    )


    col3.metric(
        "Missing Billing Status",
        quality[
            "missing_billing_status"
        ]
    )


    col1, col2 = (
        st.columns(
            2
        )
    )


    col1.metric(
        "Negative Receivables",
        quality[
            "negative_receivables"
        ]
    )


    col2.metric(
        "Negative Amount-to-Bill",
        quality[
            "negative_amount_to_bill"
        ]
    )


    st.warning(
        """
Missing financial values are treated as unknown,
not as zero.

Financial figures represent known values from
available monday.com records.
"""
    )