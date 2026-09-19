import os

from dotenv import load_dotenv

from services.monday_client import (
    get_board_items,
    board_to_dataframe
)

from analytics.work_orders import (
    prepare_work_orders,
    execution_summary,
    financial_summary,
    work_orders_by_sector,
    delayed_work_orders,
    billing_status_summary,
    work_order_quality_report
)


load_dotenv()


# ============================================================
# LOAD WORK ORDERS FROM MONDAY.COM
# ============================================================

board_id = os.getenv(
    "WORK_ORDERS_BOARD_ID"
)


print(
    "Loading Work Orders from monday.com..."
)


raw_data = get_board_items(
    board_id
)


raw_df = board_to_dataframe(
    raw_data
)


print("\nWork Orders loaded:")
print(len(raw_df))


# ============================================================
# CLEAN DATA
# ============================================================

work_orders_df = prepare_work_orders(
    raw_df
)


# ============================================================
# AVAILABLE EXECUTION STATUSES
# ============================================================

print("\nExecution statuses:")

print(
    work_orders_df[
        "clean_execution_status"
    ]
    .value_counts(
        dropna=False
    )
)


# ============================================================
# EXECUTION SUMMARY
# ============================================================

execution = execution_summary(
    work_orders_df
)


print("\n" + "=" * 60)
print("EXECUTION SUMMARY")
print("=" * 60)


print(
    "Total Work Orders:",
    execution["total_work_orders"]
)

print(
    "Completed:",
    execution["completed"]
)

print(
    "Ongoing:",
    execution["ongoing"]
)

print(
    "Executed until current month:",
    execution[
        "executed_until_current_month"
    ]
)

print(
    "Not Started:",
    execution["not_started"]
)

print(
    "Partial Completed:",
    execution[
        "partial_completed"
    ]
)

print(
    "Paused / Struck:",
    execution["paused"]
)

print(
    "Missing Execution Status:",
    execution["missing_status"]
)


# ============================================================
# FINANCIAL SUMMARY
# ============================================================

finance = financial_summary(
    work_orders_df
)


print("\n" + "=" * 60)
print("FINANCIAL SUMMARY")
print("=" * 60)


print(
    "Total Contract Value:",
    f"₹{finance['total_contract_value']:,.2f}"
)

print(
    "Total Billed:",
    f"₹{finance['total_billed']:,.2f}"
)

print(
    "Total Collected:",
    f"₹{finance['total_collected']:,.2f}"
)

print(
    "Total Receivable:",
    f"₹{finance['total_receivable']:,.2f}"
)

print(
    "Amount Still To Bill:",
    f"₹{finance['total_to_bill']:,.2f}"
)

print(
    "Negative Receivables:",
    finance[
        "negative_receivables"
    ]
)

print(
    "Negative Amount-To-Bill Records:",
    finance[
        "negative_amount_to_bill"
    ]
)


# ============================================================
# BILLING STATUS
# ============================================================

print("\n" + "=" * 60)
print("BILLING STATUS")
print("=" * 60)


print(
    billing_status_summary(
        work_orders_df
    )
)


# ============================================================
# SECTOR PERFORMANCE
# ============================================================

print("\n" + "=" * 60)
print("WORK ORDERS BY SECTOR")
print("=" * 60)


sector_data = work_orders_by_sector(
    work_orders_df
)


print(
    sector_data.to_string(
        index=False
    )
)


# ============================================================
# DELAYED WORK ORDERS
# ============================================================

delayed = delayed_work_orders(
    work_orders_df
)


print("\n" + "=" * 60)
print("DELAYED WORK ORDERS")
print("=" * 60)


print(
    "Delayed Work Orders:",
    len(delayed)
)


if len(delayed) > 0:

    columns_to_show = [
        "Item Name",
        "Sector",
        "Execution Status",
        "Probable End Date",
        "days_overdue"
    ]

    existing_columns = [
        column
        for column in columns_to_show
        if column in delayed.columns
    ]

    print(
        delayed[
            existing_columns
        ]
        .head(10)
        .to_string(
            index=False
        )
    )


# ============================================================
# DATA QUALITY
# ============================================================

quality = work_order_quality_report(
    work_orders_df
)


print("\n" + "=" * 60)
print("DATA QUALITY")
print("=" * 60)


for key, value in quality.items():

    print(
        key,
        ":",
        value
    )