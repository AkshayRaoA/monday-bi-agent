import os
import requests
import pandas as pd
from dotenv import load_dotenv


# ============================================================
# LOAD LOCAL .ENV FILE
# ============================================================

load_dotenv()


MONDAY_API_URL = "https://api.monday.com/v2"


# ============================================================
# GET CONFIG VALUE
# Works locally with .env
# Works online with Streamlit Secrets
# ============================================================

def get_config_value(name):

    # --------------------------------------------------------
    # First try environment variable / .env
    # --------------------------------------------------------

    value = os.getenv(name)

    if value:
        return str(value).strip()


    # --------------------------------------------------------
    # Then try Streamlit Cloud secrets
    # --------------------------------------------------------

    try:

        import streamlit as st

        if name in st.secrets:

            value = st.secrets[name]

            if value:
                return str(value).strip()

    except Exception:
        pass


    return None


# ============================================================
# MONDAY API REQUEST
# ============================================================

def monday_request(query, variables=None):

    token = get_config_value(
        "MONDAY_API_TOKEN"
    )


    if not token:

        raise RuntimeError(
            "MONDAY_API_TOKEN is missing. "
            "Add it to the local .env file or "
            "Streamlit Cloud Secrets."
        )


    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }


    try:

        response = requests.post(
            MONDAY_API_URL,
            json={
                "query": query,
                "variables": variables or {}
            },
            headers=headers,
            timeout=30
        )

    except requests.exceptions.Timeout:

        raise RuntimeError(
            "monday.com API request timed out."
        )

    except requests.exceptions.ConnectionError:

        raise RuntimeError(
            "Could not connect to monday.com."
        )


    # --------------------------------------------------------
    # AUTHENTICATION ERROR
    # --------------------------------------------------------

    if response.status_code == 401:

        raise RuntimeError(
            "monday.com authentication failed. "
            "Check MONDAY_API_TOKEN in your "
            "Streamlit Secrets."
        )


    # --------------------------------------------------------
    # PERMISSION ERROR
    # --------------------------------------------------------

    if response.status_code == 403:

        raise RuntimeError(
            "monday.com denied access to the board. "
            "Check whether the API token owner has access "
            "to both monday.com boards."
        )


    # --------------------------------------------------------
    # RATE LIMIT
    # --------------------------------------------------------

    if response.status_code == 429:

        raise RuntimeError(
            "monday.com API rate limit reached. "
            "Please wait and try again."
        )


    # --------------------------------------------------------
    # OTHER HTTP ERRORS
    # --------------------------------------------------------

    try:

        response.raise_for_status()

    except requests.exceptions.HTTPError:

        raise RuntimeError(
            f"monday.com API returned HTTP "
            f"{response.status_code}."
        )


    # --------------------------------------------------------
    # PARSE JSON
    # --------------------------------------------------------

    try:

        result = response.json()

    except ValueError:

        raise RuntimeError(
            "monday.com returned an invalid response."
        )


    # --------------------------------------------------------
    # GRAPHQL ERRORS
    # --------------------------------------------------------

    if "errors" in result:

        raise RuntimeError(
            f"monday.com GraphQL error: "
            f"{result['errors']}"
        )


    if "data" not in result:

        raise RuntimeError(
            "monday.com response did not contain data."
        )


    return result["data"]


# ============================================================
# GET BOARD INFORMATION
# ============================================================

def get_board_info(board_id):

    if not board_id:

        raise RuntimeError(
            "Board ID is missing."
        )


    query = """
    query ($boardIds: [ID!]) {
        boards(ids: $boardIds) {
            id
            name
            columns {
                id
                title
                type
            }
        }
    }
    """


    return monday_request(
        query,
        {
            "boardIds": [
                str(board_id)
            ]
        }
    )


# ============================================================
# GET BOARD ITEMS
# ============================================================

def get_board_items(board_id):

    if not board_id:

        raise RuntimeError(
            "Board ID is missing."
        )


    query = """
    query ($boardIds: [ID!]) {
        boards(ids: $boardIds) {

            id
            name

            columns {
                id
                title
                type
            }

            items_page(limit: 500) {

                cursor

                items {

                    id
                    name

                    column_values {
                        id
                        text
                        value
                    }
                }
            }
        }
    }
    """


    data = monday_request(
        query,
        {
            "boardIds": [
                str(board_id)
            ]
        }
    )


    # --------------------------------------------------------
    # CHECK BOARD EXISTS
    # --------------------------------------------------------

    if (
        "boards" not in data
        or
        not data["boards"]
    ):

        raise RuntimeError(
            "No monday.com board was found. "
            "Check the board ID and token permissions."
        )


    return data


# ============================================================
# CONVERT MONDAY BOARD TO PANDAS DATAFRAME
# ============================================================

def board_to_dataframe(board_data):

    if (
        not board_data
        or
        "boards" not in board_data
        or
        not board_data["boards"]
    ):

        raise RuntimeError(
            "Board data is empty."
        )


    board = board_data[
        "boards"
    ][0]


    # --------------------------------------------------------
    # MAP MONDAY COLUMN IDs TO HUMAN-READABLE TITLES
    # --------------------------------------------------------

    column_map = {

        column["id"]:
            column["title"]

        for column in board[
            "columns"
        ]
    }


    rows = []


    items = (
        board
        .get(
            "items_page",
            {}
        )
        .get(
            "items",
            []
        )
    )


    for item in items:

        row = {
            "Item ID":
                item.get(
                    "id"
                ),

            "Item Name":
                item.get(
                    "name"
                )
        }


        for value in item.get(
            "column_values",
            []
        ):

            column_id = (
                value.get(
                    "id"
                )
            )


            column_title = (
                column_map.get(
                    column_id,
                    column_id
                )
            )


            row[
                column_title
            ] = value.get(
                "text"
            )


        rows.append(
            row
        )


    return pd.DataFrame(
        rows
    )


# ============================================================
# TEST BOARD
# ============================================================

def test_board(
    board_id,
    label
):

    print(
        "\n" + "=" * 60
    )

    print(
        f"Reading {label} board..."
    )

    print(
        "=" * 60
    )


    data = get_board_items(
        board_id
    )


    board = data[
        "boards"
    ][0]


    print(
        "Board name:",
        board["name"]
    )


    print(
        "Number of items:",
        len(
            board[
                "items_page"
            ][
                "items"
            ]
        )
    )


    df = board_to_dataframe(
        data
    )


    print(
        "\nFirst 5 rows:"
    )

    print(
        df.head()
    )


    return df


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    deals_board_id = (
        get_config_value(
            "DEALS_BOARD_ID"
        )
    )

    work_orders_board_id = (
        get_config_value(
            "WORK_ORDERS_BOARD_ID"
        )
    )


    if not get_config_value(
        "MONDAY_API_TOKEN"
    ):

        print(
            "ERROR: MONDAY_API_TOKEN "
            "is missing."
        )

        raise SystemExit


    if not deals_board_id:

        print(
            "ERROR: DEALS_BOARD_ID "
            "is missing."
        )

        raise SystemExit


    if not work_orders_board_id:

        print(
            "ERROR: WORK_ORDERS_BOARD_ID "
            "is missing."
        )

        raise SystemExit


    try:

        deals_df = test_board(
            deals_board_id,
            "Deals"
        )


        work_orders_df = test_board(
            work_orders_board_id,
            "Work Orders"
        )


        print(
            "\n" + "=" * 60
        )

        print(
            "SUCCESS"
        )

        print(
            "=" * 60
        )


        print(
            f"Deals loaded: "
            f"{len(deals_df)}"
        )


        print(
            f"Work Orders loaded: "
            f"{len(work_orders_df)}"
        )


    except Exception as error:

        print(
            "\nERROR:"
        )

        print(
            error
        )