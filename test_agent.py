import os

from dotenv import load_dotenv

from services.monday_client import (
    get_board_items,
    board_to_dataframe
)

from analytics.deals import (
    prepare_deals
)

from analytics.work_orders import (
    prepare_work_orders
)

from agent.agent import (
    ask_business_agent
)


load_dotenv()


# ============================================================
# LOAD DEALS
# ============================================================

print("Loading Deals...")

deals_raw = get_board_items(
    os.getenv(
        "DEALS_BOARD_ID"
    )
)

deals_df = prepare_deals(
    board_to_dataframe(
        deals_raw
    )
)


# ============================================================
# LOAD WORK ORDERS
# ============================================================

print("Loading Work Orders...")

work_orders_raw = get_board_items(
    os.getenv(
        "WORK_ORDERS_BOARD_ID"
    )
)

work_orders_df = (
    prepare_work_orders(
        board_to_dataframe(
            work_orders_raw
        )
    )
)


print("\nData loaded successfully.")


# ============================================================
# CHAT
# ============================================================

print("\n" + "=" * 60)
print("MONDAY BUSINESS INTELLIGENCE AGENT")
print("=" * 60)

print(
    "This version uses no paid AI API."
)

print(
    "Type 'exit' to stop."
)


while True:

    question = input(
        "\nYou: "
    )


    if question.lower().strip() in [
        "exit",
        "quit"
    ]:

        print(
            "\nAgent: Goodbye!"
        )

        break


    answer = ask_business_agent(

        question,

        deals_df,

        work_orders_df
    )


    print(
        "\nAgent:"
    )

    print(
        answer
    )