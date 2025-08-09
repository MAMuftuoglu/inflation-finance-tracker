import os
import datetime
from decimal import Decimal
from typing import Dict

import requests

from core.ports import CpiDataProvider as CpiDataProviderProtocol


class BlsCpiDataProvider(CpiDataProviderProtocol):
    def get_cpi_from_initial_date(self, initial_year: str) -> Dict[str, Decimal]:
        """Return mapping of YYYY-MM -> CPI (Decimal) from BLS starting at initial year."""

        start_year = (initial_year or "").strip()[:4]
        if not start_year.isdigit() or len(start_year) != 4:
            raise ValueError("initial_year must be a 4-digit year, e.g. '2020' or '2020-01')")

        end_year = str(datetime.datetime.now().year)

        body: Dict[str, object] = {
            "seriesid": ["CUSR0000SA0"],
            "startyear": start_year,
            "endyear": end_year,
        }

        api_key = os.getenv("BLS_API_KEY")
        if api_key:
            body["registrationkey"] = api_key

        resp = requests.post(
            "https://api.bls.gov/publicAPI/v2/timeseries/data/",
            json=body,
            timeout=30,
        )
        resp.raise_for_status()
        payload = resp.json()

        results = payload.get("Results") or payload.get("results") or {}
        series_list = results.get("series") or []
        if not series_list:
            return {}

        data_points = series_list[0].get("data") or []
        month_to_cpi: Dict[str, Decimal] = {}
        for entry in data_points:
            if not isinstance(entry, dict):
                continue
            year = entry.get("year")
            period = entry.get("period")
            value = entry.get("value")
            # Only monthly periods M01..M12; skip M13 (annual avg)
            if not (isinstance(year, str) and isinstance(period, str) and period.startswith("M") and period != "M13"):
                continue
            try:
                month_index = int(period[1:])
                key = f"{int(year):04d}-{month_index:02d}"
                month_to_cpi[key] = Decimal(str(value))
            except Exception:
                continue

        return month_to_cpi