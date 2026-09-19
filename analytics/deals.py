from services.cleaner import (
    clean_sector,
    clean_status,
    clean_number,
    clean_date,
    clean_text
)


# ============================================================
# REMOVE INVALID / EMBEDDED HEADER ROWS
# ============================================================

def remove_invalid_rows(df):

    df = df.copy()

    invalid = (
        df["Deal Status"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
        .eq("deal status")
    )

    df = df[~invalid]

    return df.reset_index(drop=True)


# ============================================================
# PREPARE DEAL DATA
# ============================================================

def prepare_deals(df):

    df = remove_invalid_rows(df)

    df = df.copy()

    # --------------------------------------------------------
    # SECTOR
    # --------------------------------------------------------

    if "Sector/service" in df.columns:
        df["clean_sector"] = (
            df["Sector/service"]
            .apply(clean_sector)
        )
    else:
        df["clean_sector"] = None

    # --------------------------------------------------------
    # DEAL STATUS
    # --------------------------------------------------------

    if "Deal Status" in df.columns:
        df["clean_deal_status"] = (
            df["Deal Status"]
            .apply(clean_status)
        )
    else:
        df["clean_deal_status"] = None

    # --------------------------------------------------------
    # DEAL STAGE
    # --------------------------------------------------------

    if "Deal Stage" in df.columns:
        df["clean_deal_stage"] = (
            df["Deal Stage"]
            .apply(clean_status)
        )
    else:
        df["clean_deal_stage"] = None

    # --------------------------------------------------------
    # DEAL VALUE
    # --------------------------------------------------------

    if "Masked Deal value" in df.columns:
        df["clean_deal_value"] = (
            df["Masked Deal value"]
            .apply(clean_number)
        )
    else:
        df["clean_deal_value"] = None

    # --------------------------------------------------------
    # TENTATIVE CLOSE DATE
    # --------------------------------------------------------

    if "Tentative Close Date" in df.columns:
        df["clean_tentative_close_date"] = (
            df["Tentative Close Date"]
            .apply(clean_date)
        )
    else:
        df["clean_tentative_close_date"] = None

    # --------------------------------------------------------
    # ACTUAL CLOSE DATE
    # --------------------------------------------------------

    if "Close Date (A)" in df.columns:
        df["clean_close_date"] = (
            df["Close Date (A)"]
            .apply(clean_date)
        )
    else:
        df["clean_close_date"] = None

    # --------------------------------------------------------
    # CLOSURE PROBABILITY
    # --------------------------------------------------------

    if "Closure Probability" in df.columns:
        df["clean_probability"] = (
            df["Closure Probability"]
            .apply(clean_status)
        )
    else:
        df["clean_probability"] = None

    return df


# ============================================================
# ALL DEAL DATA SUMMARY
# ============================================================

def deal_data_summary(df):

    values = df["clean_deal_value"].dropna()

    return {
        "total_records": len(df),
        "records_with_value": len(values),
        "records_missing_value":
            df["clean_deal_value"].isna().sum(),
        "total_known_value": values.sum()
    }


# ============================================================
# ACTIVE PIPELINE
# ============================================================

def active_pipeline(df):

    # For this prototype:
    # Open + On Hold = pipeline
    #
    # Dead and Won are NOT counted as active pipeline.

    active = df[
        df["clean_deal_status"].isin(
            ["open", "on hold"]
        )
    ]

    known_values = (
        active["clean_deal_value"]
        .dropna()
    )

    return {
        "active_deal_count": len(active),

        "known_pipeline_value":
            known_values.sum(),

        "deals_with_value":
            len(known_values),

        "deals_missing_value":
            active[
                "clean_deal_value"
            ].isna().sum()
    }


# ============================================================
# PIPELINE FOR SECTOR
# ============================================================

def pipeline_for_sector(df, sector):

    sector = clean_sector(sector)

    active = df[
        df["clean_deal_status"].isin(
            ["open", "on hold"]
        )
    ]

    filtered = active[
        active["clean_sector"] == sector
    ]

    known_values = (
        filtered["clean_deal_value"]
        .dropna()
    )

    return {
        "sector": sector,

        "active_deal_count":
            len(filtered),

        "known_pipeline_value":
            known_values.sum(),

        "deals_with_value":
            len(known_values),

        "deals_missing_value":
            filtered[
                "clean_deal_value"
            ].isna().sum()
    }


# ============================================================
# PIPELINE BY SECTOR
# ============================================================

def pipeline_by_sector(df):

    active = df[
        df["clean_deal_status"].isin(
            ["open", "on hold"]
        )
    ].copy()

    result = (
        active
        .groupby(
            "clean_sector",
            dropna=False
        )
        .agg(
            deal_count=(
                "Item ID",
                "count"
            ),
            known_pipeline_value=(
                "clean_deal_value",
                "sum"
            ),
            deals_with_value=(
                "clean_deal_value",
                "count"
            )
        )
        .reset_index()
    )

    result = result.sort_values(
        "known_pipeline_value",
        ascending=False
    )

    return result