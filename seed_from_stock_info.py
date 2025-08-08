from __future__ import annotations
import argparse
from datetime import date
from decimal import Decimal
from typing import List, Dict

from dotenv import load_dotenv

from data.models import SharePurchase, init_db
from data.db import db
from stock_info import SHARES

# An Example Seed Script to populate the database with share purchases


def build_rows_from_shares(shares: List[Dict]) -> List[Dict]:
    rows: List[Dict] = []
    for s in shares:
        rows.append(
            {
                "symbol": s["name"],
                "quantity": int(s["quantity"]),
                "cost": Decimal(str(s["cost"])),  # money-safe
                "purchase_date": date.fromisoformat(s["purchase_date"]),
            }
        )
    return rows


def seed_shares(reset: bool = False) -> int:
    if reset:
        SharePurchase.delete().execute()

    rows = build_rows_from_shares(SHARES)
    if not rows:
        return 0

    # Use atomic + bulk insert for speed
    with db.atomic():
        SharePurchase.insert_many(rows).execute()
    return len(rows)


def main() -> None:
    load_dotenv()
    init_db()

    parser = argparse.ArgumentParser(description="Seed SharePurchase from stock_info.SNARES")
    parser.add_argument("--reset", action="store_true", help="Delete existing rows before seeding")
    args = parser.parse_args()

    inserted = seed_shares(reset=args.reset)
    print(f"Seeded {inserted} share purchases.")


if __name__ == "__main__":
    main()


