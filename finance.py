from datetime import datetime, timedelta
from collections import defaultdict
from stock_info import SHARES, CPI_DATA


def calculate_inflation_corrected(purchase_date, cpi_data):
    purchase_month = purchase_date.strftime("%Y-%m")
    purchase_cpi = next(
        (cpi["cpi"] for cpi in cpi_data if cpi["month"] == purchase_month), None
    )
    if purchase_cpi is None:
        return 1.0
    latest_cpi = cpi_data[-1]["cpi"]
    return latest_cpi / purchase_cpi


def group_shares_by_name(shares):
    grouped = defaultdict(list)
    for share in shares:
        grouped[share["name"]].append(share)
    return grouped


def analyze_investments(shares, cpi_data):
    grouped_shares = group_shares_by_name(shares)
    results = []
    total_nominal_invested = 0
    total_real_invested = 0
    total_current_value = 0
    total_nominal_profit = 0
    total_real_profit = 0

    for company, purchases in grouped_shares.items():
        company_nominal_invested = 0
        company_real_invested = 0
        company_current_value = 0
        company_nominal_profit = 0
        company_real_profit = 0

        for purchase in purchases:
            batch_cost = purchase["quantity"] * purchase["cost"]
            batch_current = purchase["quantity"] * purchase["current_price"]

            purchase_date = datetime.strptime(purchase["purchase_date"], "%Y-%m-%d")
            inflation_factor = calculate_inflation_corrected(purchase_date, cpi_data)
            adjusted_cost = batch_cost * inflation_factor

            company_nominal_invested += batch_cost
            company_real_invested += adjusted_cost
            company_current_value += batch_current
            company_nominal_profit += batch_current - batch_cost
            company_real_profit += batch_current - adjusted_cost

        results.append(
            {
                "name": company,
                "total_nominal_invested": company_nominal_invested,
                "total_real_invested": company_real_invested,
                "total_current_value": company_current_value,
                "total_nominal_profit": company_nominal_profit,
                "total_real_profit": company_real_profit,
            }
        )
        total_nominal_invested += company_nominal_invested
        total_real_invested += company_real_invested
        total_current_value += company_current_value
        total_nominal_profit += company_nominal_profit
        total_real_profit += company_real_profit

    totals = {
        "total_nominal_invested": total_nominal_invested,
        "total_real_invested": total_real_invested,
        "total_current_value": total_current_value,
        "total_nominal_profit": total_nominal_profit,
        "total_real_profit": total_real_profit,
    }

    return results, totals


if __name__ == "__main__":
    results, totals = analyze_investments(SHARES, CPI_DATA)

    print("\nInvestment Analysis:")
    for result in results:
        print(f"\n{result['name']}:")
        print(f"  Total Invested (Nominal): ${result['total_nominal_invested']:,.2f}")
        print(
            f"  Total Invested (Inflation-corrected): ${result['total_real_invested']:,.2f}"
        )
        print(f"  Current Value: ${result['total_current_value']:,.2f}")
        print(f"  Nominal Profit: ${result['total_nominal_profit']:,.2f}")
        print(f"  Real Profit: ${result['total_real_profit']:,.2f}")

    print("\nPortfolio Totals:")
    print(f"  Total Invested (Nominal): ${totals['total_nominal_invested']:,.2f}")
    print(
        f"  Total Invested (Inflation-corrected): ${totals['total_real_invested']:,.2f}"
    )
    print(f"  Current Value: ${totals['total_current_value']:,.2f}")
    print(f"  Nominal Profit: ${totals['total_nominal_profit']:,.2f}")
    print(f"  Real Profit: ${totals['total_real_profit']:,.2f}")
