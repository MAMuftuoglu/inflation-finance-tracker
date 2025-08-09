# Financial Report (SQLite + BLS CPI + Google Finance)

CLI tool to record stock share purchases in SQLite, adjust investments for inflation using BLS CPI, fetch current prices from Google Finance, and print a concise analysis per company and for the whole portfolio.

### Project structure
- `main.py`: entrypoint (loads `.env`, provides interactive CLI, orchestrates analysis)
- `core/`: domain types and pure analysis logic
  - `core/models.py`, `core/analysis.py`, `core/ports.py`, `core/dto.py`
- `services/`: orchestration that maps DB rows to domain and calls analysis
  - `services/investment_service.py`
- `data/`: persistence layer (Peewee/SQLite)
  - `data/db.py`, `data/models.py`, `data/repositories.py`
- `infra/`: external integrations
  - `infra/cpi_data_provider.py` (BLS CPI provider)
  - `infra/google_finance_price_provider.py` (current price provider via Google Finance)

### Requirements
- Python 3.10+
- Windows 11 PowerShell (examples use PowerShell)
- BLS Public API key (optional but recommended for CPI fetch)

### Setup (Windows PowerShell)
```powershell
# From repository root
py -m venv .venv
.\.venv\Scripts\Activate.ps1

# Optional: if activation is blocked
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

# Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Configure environment
Create a `.env` file in the project root with the following content (edit values as needed):
```env
# REQUIREMENT
BLS_API_KEY=your_bls_api_key_here

# Optional: override database location; defaults to ./financial_report.db
DB_PATH=D:\\Users\\you\\financial_report\\financial_report.db
```
See [U.S. Bureau of Labor Statistics registration page](https://data.bls.gov/registrationEngine/) for API key.

You can create/edit it from PowerShell:
```powershell
if (-not (Test-Path .env)) { New-Item -ItemType File -Path .env | Out-Null }
notepad .env
```

### Run the app
```powershell
python .\main.py
```

You will see an interactive menu:
```
What would you like to do?
(1) Add a share purchase
(2) Show your share purchases
(3) View investment analysis
(4) Exit
->
```

#### (1) Add a share purchase
You will be asked for:
- symbol (e.g., `AAPL`)
- market (e.g., `NASDAQ`, `NYSE`, `IST`, etc.)
- quantity (decimal allowed)
- cost (price per share, decimal allowed)
- purchase date (YYYY-MM-DD)

The app stores purchases in `SharePurchase` and also keeps a `symbol -> market` mapping in `ShareMarketMap`. If you later enter the same symbol with a different market, the mapping will be updated. For now only use uppercase characters only. Also, to enter a decimal, use . as decimal point.

#### (2) Show your share purchases
Prints your stored purchases in chronological order.

#### (3) View investment analysis
- Fetches CPI from BLS (from the year of your earliest purchase through current year)
- Scrapes current prices from Google Finance for each distinct `symbol:market`
- Runs inflation-adjusted analysis and prints per-company results and portfolio totals

### How prices are fetched (Google Finance)
- Prices are scraped from Google Finance using requests + BeautifulSoup.
- Market is required to build the quote URL (e.g., `AAPL:NASDAQ`).
- If Google changes page structure, parsing may need updates.

### Database
- Default DB path is `./financial_report.db` (can be overridden via `DB_PATH` in `.env`).
- SQLite is configured with WAL and a small timeout for better reliability on Windows.

### Notes
- Money values are handled as `Decimal` end-to-end (Peewee `DecimalField` in the DB layer).

### Troubleshooting
- PowerShell script execution policy may block venv activation. Run:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
  ```
- If you see network or parsing errors for prices, try again later or verify the market code you entered. Example pairs: `AAPL:NASDAQ`, `MSFT:NASDAQ`, `GOOGL:NASDAQ`, `ASELS:IST`.
