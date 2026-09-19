import pandas as pd
import re


# ============================================================
# VALUES THAT SHOULD BE TREATED AS MISSING
# ============================================================

MISSING_VALUES = {
    "",
    "-",
    "--",
    "na",
    "n/a",
    "nan",
    "none",
    "null",
    "nil",
    "unknown"
}


# ============================================================
# CLEAN NORMAL TEXT
# ============================================================

def clean_text(value):

    if value is None:
        return None

    value = str(value).strip()

    if value.lower() in MISSING_VALUES:
        return None

    return value


# ============================================================
# CLEAN STATUS
# ============================================================

def clean_status(value):

    value = clean_text(value)

    if value is None:
        return None

    # Example:
    # "BILLED" → "billed"
    # " Billed " → "billed"
    # "BIlled" → "billed"

    return value.lower().strip()


# ============================================================
# CLEAN SECTOR
# ============================================================

def clean_sector(value):

    value = clean_text(value)

    if value is None:
        return None

    value = value.lower().strip()

    aliases = {
        "energy sector": "energy",
        "renewable": "renewables",
        "renewable energy": "renewables",
        "power line": "powerline"
    }

    return aliases.get(value, value)


# ============================================================
# CLEAN DATE
# ============================================================

def clean_date(value):

    value = clean_text(value)

    if value is None:
        return pd.NaT

    value = str(value).strip()

    # monday normally returns ISO dates: YYYY-MM-DD
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return pd.to_datetime(
            value,
            format="%Y-%m-%d",
            errors="coerce"
        )

    # Fallback for other messy formats
    return pd.to_datetime(
        value,
        errors="coerce",
        dayfirst=True
    )


# ============================================================
# CLEAN NUMBERS / MONEY
# ============================================================

def clean_number(value):

    value = clean_text(value)

    if value is None:
        return None

    text = str(value).strip()

    # Remove common symbols
    text = text.replace("₹", "")
    text = text.replace("$", "")
    text = text.replace(",", "")
    text = text.replace(" ", "")

    # Handle lakh
    if text.lower().endswith("l"):
        try:
            number = float(text[:-1])
            return number * 100000
        except ValueError:
            return None

    # Handle million
    if text.lower().endswith("m"):
        try:
            number = float(text[:-1])
            return number * 1000000
        except ValueError:
            return None

    # Normal number
    try:
        return float(text)

    except ValueError:
        return None


# ============================================================
# CLEAN PERCENTAGE
# ============================================================

def clean_percentage(value):

    value = clean_text(value)

    if value is None:
        return None

    text = str(value).replace("%", "").strip()

    try:
        return float(text)

    except ValueError:
        return None