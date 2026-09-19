import pandas as pd

from services.cleaner import (
    clean_text,
    clean_status,
    clean_sector,
    clean_number,
    clean_date
)


# ============================================================
# PREPARE / CLEAN WORK ORDER DATA
# ============================================================

def prepare_work_orders(df):

    df = df.copy()

    # --------------------------------------------------------
    # EXECUTION STATUS
    # --------------------------------------------------------

    if "Execution Status" in df.columns:
        df["clean_execution_status"] = (
            df["Execution Status"]
            .apply(clean_status)
        )
    else:
        df["clean_execution_status"] = None


    # --------------------------------------------------------
    # WO STATUS
    # --------------------------------------------------------

    if "WO Status (billed)" in df.columns:
        df["clean_wo_status"] = (
            df["WO Status (billed)"]
            .apply(clean_status)
        )
    else:
        df["clean_wo_status"] = None


    # --------------------------------------------------------
    # BILLING STATUS
    # --------------------------------------------------------

    if "Billing Status" in df.columns:
        df["clean_billing_status"] = (
            df["Billing Status"]
            .apply(clean_status)
        )
    else:
        df["clean_billing_status"] = None


    # --------------------------------------------------------
    # COLLECTION STATUS
    # --------------------------------------------------------

    if "Collection status" in df.columns:
        df["clean_collection_status"] = (
            df["Collection status"]
            .apply(clean_status)
        )
    else:
        df["clean_collection_status"] = None


    # --------------------------------------------------------
    # SECTOR
    # --------------------------------------------------------

    if "Sector" in df.columns:
        df["clean_sector"] = (
            df["Sector"]
            .apply(clean_sector)
        )
    else:
        df["clean_sector"] = None


    # --------------------------------------------------------
    # NATURE OF WORK
    # --------------------------------------------------------

    if "Nature of Work" in df.columns:
        df["clean_nature_of_work"] = (
            df["Nature of Work"]
            .apply(clean_status)
        )
    else:
        df["clean_nature_of_work"] = None


    # ========================================================
    # DATES
    # ========================================================

    date_columns = {
        "Data Delivery Date":
            "clean_data_delivery_date",

        "Date of PO/LOI":
            "clean_po_date",

        "Probable Start Date":
            "clean_start_date",

        "Probable End Date":
            "clean_end_date"
    }

    for original, cleaned in date_columns.items():

        if original in df.columns:

            df[cleaned] = (
                df[original]
                .apply(clean_date)
            )

        else:
            df[cleaned] = pd.NaT


    # ========================================================
    # FINANCIAL COLUMNS
    # ========================================================

    money_columns = {

        "Amount in Rupees (Excl of GST) (Masked)":
            "clean_amount_excl_gst",

        "Amount in Rupees (Incl of GST) (Masked)":
            "clean_amount_incl_gst",

        "Billed Value in Rupees (Excl of GST.) (Masked)":
            "clean_billed_excl_gst",

        "Billed Value in Rupees (Incl of GST.) (Masked)":
            "clean_billed_incl_gst",

        "Collected Amount in Rupees (Incl of GST.) (Masked)":
            "clean_collected_amount",

        "Amount to be billed in Rs. (Exl. of GST) (Masked)":
            "clean_to_bill_excl_gst",

        "Amount to be billed in Rs. (Incl. of GST) (Masked)":
            "clean_to_bill_incl_gst",

        "Amount Receivable (Masked)":
            "clean_receivable"
    }


    for original, cleaned in money_columns.items():

        if original in df.columns:

            df[cleaned] = (
                df[original]
                .apply(clean_number)
            )

        else:
            df[cleaned] = None


    return df


# ============================================================
# EXECUTION SUMMARY
# ============================================================

def execution_summary(df):

    df = prepare_work_orders(df)

    status_counts = (
        df["clean_execution_status"]
        .value_counts(dropna=False)
        .to_dict()
    )

    return {
        "total_work_orders": len(df),

        "completed":
            status_counts.get(
                "completed",
                0
            ),

        "ongoing":
            status_counts.get(
                "ongoing",
                0
            ),

        "executed_until_current_month":
            status_counts.get(
                "executed until current month",
                0
            ),

        "not_started":
            status_counts.get(
                "not started",
                0
            ),

        "partial_completed":
            status_counts.get(
                "partial completed",
                0
            ),

        "paused":
            status_counts.get(
                "pause / struck",
                0
            ),

        "missing_status":
            df[
                "clean_execution_status"
            ].isna().sum()
    }


# ============================================================
# FINANCIAL SUMMARY
# ============================================================

def financial_summary(df):

    df = prepare_work_orders(df)

    contract_value = (
        df["clean_amount_incl_gst"]
        .dropna()
    )

    billed = (
        df["clean_billed_incl_gst"]
        .dropna()
    )

    collected = (
        df["clean_collected_amount"]
        .dropna()
    )

    receivable = (
        df["clean_receivable"]
        .dropna()
    )

    to_bill = (
        df["clean_to_bill_incl_gst"]
        .dropna()
    )


    return {

        "total_contract_value":
            contract_value.sum(),

        "total_billed":
            billed.sum(),

        "total_collected":
            collected.sum(),

        "total_receivable":
            receivable.sum(),

        "total_to_bill":
            to_bill.sum(),

        "work_orders_missing_collection":
            df[
                "clean_collected_amount"
            ].isna().sum(),

        "negative_receivables":
            (
                df[
                    "clean_receivable"
                ] < 0
            ).sum(),

        "negative_amount_to_bill":
            (
                df[
                    "clean_to_bill_incl_gst"
                ] < 0
            ).sum()
    }


# ============================================================
# WORK ORDERS BY SECTOR
# ============================================================

def work_orders_by_sector(df):

    df = prepare_work_orders(df)

    result = (
        df
        .groupby(
            "clean_sector",
            dropna=False
        )
        .agg(

            work_orders=(
                "Item ID",
                "count"
            ),

            contract_value=(
                "clean_amount_incl_gst",
                "sum"
            ),

            billed=(
                "clean_billed_incl_gst",
                "sum"
            ),

            collected=(
                "clean_collected_amount",
                "sum"
            ),

            receivable=(
                "clean_receivable",
                "sum"
            )
        )
        .reset_index()
    )

    result = result.sort_values(
        "contract_value",
        ascending=False
    )

    return result


# ============================================================
# DELAYED WORK ORDERS
# ============================================================

def delayed_work_orders(df):

    df = prepare_work_orders(df)

    today = pd.Timestamp.today().normalize()

    delayed = df[

        (
            df["clean_end_date"].notna()
        )

        &

        (
            df["clean_end_date"] < today
        )

        &

        (
            df["clean_execution_status"]
            != "completed"
        )

    ].copy()


    delayed["days_overdue"] = (

        today
        -
        delayed["clean_end_date"]

    ).dt.days


    return delayed


# ============================================================
# BILLING STATUS SUMMARY
# ============================================================

def billing_status_summary(df):

    df = prepare_work_orders(df)

    return (
        df["clean_billing_status"]
        .value_counts(
            dropna=False
        )
    )


# ============================================================
# DATA QUALITY REPORT
# ============================================================

def work_order_quality_report(df):

    df = prepare_work_orders(df)

    return {

        "total_records":
            len(df),

        "missing_execution_status":
            df[
                "clean_execution_status"
            ].isna().sum(),

        "missing_sector":
            df[
                "clean_sector"
            ].isna().sum(),

        "missing_end_date":
            df[
                "clean_end_date"
            ].isna().sum(),

        "missing_collection_amount":
            df[
                "clean_collected_amount"
            ].isna().sum(),

        "missing_billing_status":
            df[
                "clean_billing_status"
            ].isna().sum(),

        "negative_receivables":
            (
                df[
                    "clean_receivable"
                ] < 0
            ).sum(),

        "negative_amount_to_bill":
            (
                df[
                    "clean_to_bill_incl_gst"
                ] < 0
            ).sum()
    }