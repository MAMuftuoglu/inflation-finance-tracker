from dotenv import load_dotenv
load_dotenv()

from decimal import Decimal
from datetime import date

from data.models import init_db
from data.repositories import add_share_purchase, load_share_purchases_as_rows
from core.analysis import purchase_summary
from infra.cpi_data_provider import BlsCpiDataProvider
from services.investment_service import run_investment_analysis


if __name__ == "__main__":
    init_db()
    continue_loop = True

    while continue_loop:
        selection = input(
"""What would you like to do?
(1) Add a share purchase
(2) Show your share purchases
(3) View investment analysis
(4) Exit
-> """)

        if selection == "1":
            try:
                symbol = input("Enter the ticker symbol of the share you purchased: ")
                market = input("Enter the market of the share you purchased: ")
                quantity = Decimal(input("Enter the quantity of the share you purchased: "))
                cost = Decimal(input("Enter the cost of the share you purchased: "))
                purchase_date = date.fromisoformat(input("Enter the date you purchased the share in YYYY-MM-DD format: "))
                result = add_share_purchase(symbol, market, quantity, cost, purchase_date)
                if result["success"]:
                    print(f"Purchase added successfully: {result['symbol']} - {result['market']} - {result['quantity']} - {result['cost']} - {result['purchase_date']}")
                else:
                    print(f"Error: {result['error']}")
            except Exception as e:
                print(f"Error: {e}")
                print("Please try again.")

        elif selection == "2":
            purchases = load_share_purchases_as_rows()
            purchase_summary(purchases)

        elif selection == "3":
            purchases = load_share_purchases_as_rows()
            if not purchases or len(purchases) == 0:
                print("No purchases found. Please add a purchase first.")
                continue
            earliest_date = purchases[0]["purchase_date"]
            cpi_data_provider = BlsCpiDataProvider()

            results, totals = run_investment_analysis(
                purchase_rows=purchases,
                initial_year=earliest_date,
                cpi_data_provider=cpi_data_provider,
            )
            print("\nInvestment Analysis:")
            for result in results:
                print(f"\n{result.name}:")
                print(f"  Total Invested (Nominal): ${result.total_nominal_invested:,.2f}")
                print(
                    f"  Total Invested (Inflation-corrected): ${result.total_real_invested:,.2f}"
                )
                print(f"  Current Value: ${result.total_current_value:,.2f}")
                print(f"  Nominal Profit: ${result.total_nominal_profit:,.2f}")
                print(f"  Real Profit: ${result.total_real_profit:,.2f}")
            print("\nPortfolio Totals:")
            print(f"  Total Invested (Nominal): ${totals.total_nominal_invested:,.2f}")
            print(f"  Total Invested (Inflation-corrected): ${totals.total_real_invested:,.2f}")
            print(f"  Current Value: ${totals.total_current_value:,.2f}")
            print(f"  Nominal Profit: ${totals.total_nominal_profit:,.2f}")
            print(f"  Real Profit: ${totals.total_real_profit:,.2f}")

        elif selection == "4":
            continue_loop = False

        else:
            print("Invalid selection. Please select from the options above.")
        print()