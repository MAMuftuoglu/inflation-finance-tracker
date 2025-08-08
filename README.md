### Financial Report (SQLite + Twelve Data)

This project analyzes a stock portfolio stored in SQLite, adjusts investments for inflation (CPI), fetches current prices from Twelve Data in a single batch call, and prints a concise analysis.

### Project structure
- `finance.py`: entrypoint (loads `.env`, orchestrates analysis, prints results)
- `core/`: domain types and pure analysis logic
  - `core/models.py`, `core/analysis.py`, `core/ports.py`
- `services/`: orchestration that maps DB rows to domain and calls analysis
  - `services/investment_service.py`
- `data/`: persistence layer (Peewee/SQLite)
  - `data/db.py`, `data/models.py`, `data/repositories.py`
- `infra/`: external integrations
  - `infra/tw_client.py` (Twelve Data client)
  - `infra/twelvedata_price_provider.py` (batch price provider)
- `stock_info.py`: sample CPI and purchases for seeding
- `seed_from_stock_info.py`: seed DB from `stock_info.py`

### Requirements
- Python 3.10+
- Twelve Data API key
- Windows 11 PowerShell (examples below use PowerShell)

### Setup (Windows PowerShell)
```powershell
# From repository root
py -m venv .venv
.\.venv\Scripts\Activate.ps1

# Optional: If activation is blocked
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

# Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Configure environment
Create `.env` in the project root (or copy the example):
```powershell
Copy-Item .env.example .env
notepad .env
```
Supported variables:
- `TWELVE_DATA_KEY` (preferred) or `TD_API_KEY`: Twelve Data API key
- `DB_PATH` (optional): SQLite DB path; defaults to `./financial_report.db`

### Seed the database
`SharePurchase` expects real ticker symbols only. The provided `seed_from_stock_info.py` currently takes `name` values from `stock_info.SHARES` and saves them as `symbol`. Update `stock_info.py` to use valid symbols (e.g., `AAPL`, `NDAQ`) before seeding, or change the seeding logic to map names to symbols.

Run the seed (this will reset the table if you pass `--reset`):
```powershell
python .\seed_from_stock_info.py --reset
```

### Run the analysis
```powershell
python .\finance.py
```
What happens:
- Loads CPI from `stock_info.py`
- Loads purchases from SQLite (`data/repositories.py`)
- Fetches latest prices in one batch via Twelve Data (`infra/twelvedata_price_provider.py` → `/price` endpoint)
- Runs inflation-adjusted analysis (`core/analysis.py`) and prints per-company and portfolio totals

### Notes
- Money values are handled as `Decimal` internally for accuracy; Peewee uses `DecimalField` in the DB layer.
- SQLite is configured with WAL and a small timeout for better reliability on Windows.
- Twelve Data free plans have symbol and rate limits; batch requests still count per symbol. It allows 800 API calls a day and 8 calls a minute.

### TO-DO
- Instead of relying on limited API such as Twelve Data, a parser for Google Finance might be implemented
- Get CPI values from U.S. Bureau of Labor Statistics API to streamline the process

### Troubleshooting
- “TwelveData API key not found”: Ensure `.env` contains `TWELVE_DATA_KEY` (or `TD_API_KEY`) and that `finance.py` is loading `.env` early.
- “database is locked”: Try closing other processes that access the DB, or increase the `timeout` in `data/db.py`.
- PowerShell activation error: Set the execution policy as shown in Setup.


