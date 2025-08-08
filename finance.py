from dotenv import load_dotenv
load_dotenv()

from data.models import init_db
from data.repositories import load_share_purchases_as_rows
from stock_info import CPI_DATA
from services.investment_service import run_investment_analysis
from infra.twelvedata_price_provider import TwelveDataPriceProvider

if __name__ == "__main__":
    init_db()
    shares = load_share_purchases_as_rows()
    # Domain/service pipeline (temporary fixed prices = 0 until TwelveData integration)
    results, totals = run_investment_analysis(
        purchase_rows=shares,
        cpi_rows=CPI_DATA,
        price_provider=TwelveDataPriceProvider(),
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
    print(
        f"  Total Invested (Inflation-corrected): ${totals.total_real_invested:,.2f}"
    )
    print(f"  Current Value: ${totals.total_current_value:,.2f}")
    print(f"  Nominal Profit: ${totals.total_nominal_profit:,.2f}")
    print(f"  Real Profit: ${totals.total_real_profit:,.2f}")
