"""Affordability Dashboard KPIs (regional + national).

Calculates years to buy, rent burden, affordability ranking,
demographic vs supply gap, and net migration.
"""
import logging
from typing import Any, Dict

import numpy as np
import pandas as pd

from .kpi_base import KPIBaseCalculator, NZ_REGIONS

logger = logging.getLogger(__name__)


class AffordabilityKPICalculator(KPIBaseCalculator):
    """Calculates Affordability Dashboard KPIs from Silver/Bronze data."""

    def calc(self) -> pd.DataFrame:
        """Calculate all affordability KPIs."""
        logger.info("Calculating KPIs 23-27: Affordability")
        regional = self._get_regional_data()
        rows = []

        years_data = []
        for region in NZ_REGIONS:
            if region not in regional:
                continue
            income = regional[region].get("median_income", 65000)
            price = self._estimate_median_price(region, regional)
            years = round(price / income, 1)
            years_data.append({"region": region, "years": years})
            rows.append({"name": f"Years to Buy - {region}",
                         "value": years, "unit": "years",
                         "description": f"Years of median income to buy median home in {region}",
                         "category": "Affordability", "source": "Stats NZ income + price estimate"})

        if years_data:
            nat_years = round(np.mean([d["years"] for d in years_data]), 1)
            rows.append({"name": "Years to Buy (National Avg)",
                         "value": nat_years, "unit": "years",
                         "description": "Average years of income to buy across regions",
                         "category": "Affordability", "source": "Stats NZ income + price estimate"})

        for region in NZ_REGIONS:
            if region not in regional:
                continue
            income = regional[region].get("median_income", 65000)
            weekly_rent = regional[region].get("weekly_rent", 550)
            annual_rent = weekly_rent * 52
            burden = round(annual_rent / income * 100, 0)
            rows.append({"name": f"Rent Burden - {region}",
                         "value": float(burden), "unit": "%",
                         "description": f"Annual rent as % of median income in {region}",
                         "category": "Affordability", "source": "Tenancy Services rent + Stats NZ income"})

        ranked = sorted(years_data, key=lambda x: x["years"])
        for rank, d in enumerate(ranked, 1):
            rows.append({"name": f"Affordability Rank - {d['region']}",
                         "value": rank, "unit": "/16",
                         "description": f"Affordability ranking for {d['region']}",
                         "category": "Affordability", "source": "Years-to-buy calculation"})

        supply_p = self._get_housing_supply_pressure()
        rows.append({"name": "Demographic vs Supply Gap",
                     "value": round(supply_p, 1), "unit": "pts",
                     "description": "Population growth minus housing supply growth",
                     "category": "Affordability", "source": "Stats NZ population + consents"})

        df = self.features.get("supply_deficit")
        if df is not None and not df.empty and "population_growth_yoy" in df.columns:
            valid = df["population_growth_yoy"].dropna()
            if not valid.empty:
                pop_growth = float(valid.iloc[-1])
                net_migration = round(pop_growth / 100 * 5200000, 0)
                rows.append({"name": "Net Migration (National)",
                             "value": float(net_migration), "unit": "people/yr",
                             "description": "Estimated net migration",
                             "category": "Affordability", "source": "Stats NZ population growth"})

        return pd.DataFrame(rows)
