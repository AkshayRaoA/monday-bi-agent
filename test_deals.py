import os

from dotenv import load_dotenv

from services.monday_client import (
    get_board_items,
    board_to_dataframe
)

from analytics.deals import (
    prepare_deals,
    deal_data_summary,
    active_pipeline,
    pipeline_by_sector
)


load_dotenv()


# ============================================================
# LOAD DEALS
# ============================================================

board_id = os.getenv("DEALS_BOARD_ID")

print("Loading Deals from monday.com...")

raw_data = get_board_items(board_id)

raw_df = board_to_dataframe(raw_data)


print("\nRaw Deals loaded:")
print(len(raw_df))


# ============================================================
# CLEAN DEALS
# ============================================================

deals_df = prepare_deals(raw_df)


print("\nValid Deals after cleaning:")
print(len(deals_df))


# ============================================================
# SECTORS
# ============================================================

print("\nAvailable sectors:")

sectors = (
    deals_df["clean_sector"]
    .dropna()
    .sort_values()
    .unique()
)

for sector in sectors:
    print("-", sector)


# ============================================================
# STATUS VALUES
# ============================================================

print("\nDeal statuses:")

print(
    deals_df[
        "clean_deal_status"
    ]
    .value_counts(
        dropna=False
    )
)


# ============================================================
# ALL DEAL DATA
# ============================================================

summary = deal_data_summary(
    deals_df
)

print("\n" + "=" * 60)
print("ALL DEAL DATA")
print("=" * 60)

print(
    "Valid records:",
    summary["total_records"]
)

print(
    "Records with value:",
    summary["records_with_value"]
)

print(
    "Records missing value:",
    summary["records_missing_value"]
)

print(
    "Known value across all statuses:",
    f"₹{summary['total_known_value']:,.2f}"
)


# ============================================================
# ACTIVE PIPELINE
# ============================================================

pipeline = active_pipeline(
    deals_df
)

print("\n" + "=" * 60)
print("ACTIVE PIPELINE")
print("=" * 60)

print(
    "Active deals:",
    pipeline["active_deal_count"]
)

print(
    "Known active pipeline:",
    f"₹{pipeline['known_pipeline_value']:,.2f}"
)

print(
    "Active deals with value:",
    pipeline["deals_with_value"]
)

print(
    "Active deals missing value:",
    pipeline["deals_missing_value"]
)


# ============================================================
# PIPELINE BY SECTOR
# ============================================================

print("\n" + "=" * 60)
print("ACTIVE PIPELINE BY SECTOR")
print("=" * 60)

sector_pipeline = pipeline_by_sector(
    deals_df
)

print(
    sector_pipeline.to_string(
        index=False
    )
)