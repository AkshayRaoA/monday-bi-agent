import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

MONDAY_API_URL = "https://api.monday.com/v2"
MONDAY_API_TOKEN = os.getenv("MONDAY_API_TOKEN")


def monday_request(query, variables=None):
    headers = {
        "Authorization": MONDAY_API_TOKEN,
        "Content-Type": "application/json"
    }

    response = requests.post(
        MONDAY_API_URL,
        json={
            "query": query,
            "variables": variables or {}
        },
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    result = response.json()

    if "errors" in result:
        raise Exception(result["errors"])

    return result["data"]


def get_board_info(board_id):
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
            "boardIds": [str(board_id)]
        }
    )


def get_board_items(board_id):
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

    return monday_request(
        query,
        {
            "boardIds": [str(board_id)]
        }
    )


def board_to_dataframe(board_data):
    board = board_data["boards"][0]

    column_map = {
        column["id"]: column["title"]
        for column in board["columns"]
    }

    rows = []

    for item in board["items_page"]["items"]:
        row = {
            "Item ID": item["id"],
            "Item Name": item["name"]
        }

        for value in item["column_values"]:
            column_id = value["id"]

            column_title = column_map.get(
                column_id,
                column_id
            )

            row[column_title] = value["text"]

        rows.append(row)

    return pd.DataFrame(rows)


def test_board(board_id, label):
    print("\n" + "=" * 60)
    print(f"Reading {label} board...")
    print("=" * 60)

    data = get_board_items(board_id)

    board = data["boards"][0]

    print("Board name:", board["name"])
    print(
        "Number of items:",
        len(board["items_page"]["items"])
    )

    print("\nFirst 5 items:")

    for item in board["items_page"]["items"][:5]:
        print("-", item["name"])

    df = board_to_dataframe(data)

    print("\nDataFrame preview:")
    print(df.head())

    print("\nColumns found:")
    for column in df.columns:
        print("-", column)

    return df


if __name__ == "__main__":

    deals_board_id = os.getenv("DEALS_BOARD_ID")
    work_orders_board_id = os.getenv("WORK_ORDERS_BOARD_ID")

    if not MONDAY_API_TOKEN:
        print("ERROR: MONDAY_API_TOKEN is missing in .env")
        exit()

    if not deals_board_id:
        print("ERROR: DEALS_BOARD_ID is missing in .env")
        exit()

    if not work_orders_board_id:
        print("ERROR: WORK_ORDERS_BOARD_ID is missing in .env")
        exit()

    try:
        deals_df = test_board(
            deals_board_id,
            "Deals"
        )

        work_orders_df = test_board(
            work_orders_board_id,
            "Work Orders"
        )

        print("\n" + "=" * 60)
        print("SUCCESS")
        print("=" * 60)

        print(
            f"Deals loaded: {len(deals_df)}"
        )

        print(
            f"Work Orders loaded: {len(work_orders_df)}"
        )

        print(
            "\nPython is successfully reading both "
            "monday.com boards."
        )

    except Exception as error:
        print("\nERROR:")
        print(error)