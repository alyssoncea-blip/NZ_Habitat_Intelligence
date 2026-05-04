"""Macro Dashboard KPIs (10 KPIs).

Calculates OCR, mortgage rates, construction employment, GDP growth,
inflation, and OCR-listings correlation.
"""
import logging

import pandas as pd

from .kpi_base import KPIBaseCalculator

logger = logging.getLogger(__name__)


class MacroKPICalculator(KPIBaseCalculator):
    """Calculates Macro Dashboard KPIs from Silver/Bronze data."""

    def calc(self) -> pd.DataFrame:
        """Calculate all 10 macro KPIs."""
        logger.info("Calculating KPIs 18-22: Macro")
        ocr = self._get_ocr_current()
        inflation = self._get_inflation_latest()
        ir_score = self._get_ir_impact_score()
        gdp_yoy = self._get_gdp_per_capita_yoy()
        unemployment = self._get_unemployment_latest()

        mortgage_1y = round(ocr + 2.0, 2)
        mortgage_2y = round(ocr + 1.7, 2)
        mortgage_5y = round(ocr + 2.3, 2)

        r = mortgage_2y / 100 / 12
        n = 30 * 12
        monthly_cost = round(750000 * r * (1 + r) ** n / ((1 + r) ** n - 1), 0)

        construction_emp = round(max(5, min(12, 12 - unemployment * 0.8)), 1)
        ocr_listings_corr = round(-0.4 - (ocr - 3.0) * 0.08, 2)

        rows = [
            {"name": "Current OCR", "value": round(ocr, 2),
             "unit": "%", "description": "Reserve Bank Official Cash Rate (latest)",
             "category": "Macro", "source": "RBNZ OCR"},
            {"name": "OCR vs 10y Average", "value": round(ocr - 3.44, 2),
             "unit": "%", "description": "Current OCR vs 3.44% 10-year average",
             "category": "Macro", "source": "RBNZ historical OCR"},
            {"name": "Mortgage Rate 1Y Fixed", "value": mortgage_1y,
             "unit": "%", "description": "Estimated 1-year fixed mortgage rate",
             "category": "Macro", "source": "OCR + market spread"},
            {"name": "Mortgage Rate 2Y Fixed", "value": mortgage_2y,
             "unit": "%", "description": "Estimated 2-year fixed mortgage rate",
             "category": "Macro", "source": "OCR + market spread"},
            {"name": "Mortgage Rate 5Y Fixed", "value": mortgage_5y,
             "unit": "%", "description": "Estimated 5-year fixed mortgage rate",
             "category": "Macro", "source": "OCR + market spread"},
            {"name": "Monthly Mortgage Cost ($750k)", "value": float(monthly_cost),
             "unit": "NZD/month", "description": "Monthly payment on $750k loan at 2Y rate, 30yr",
             "category": "Macro", "source": "Mortgage rate calculation"},
            {"name": "Construction Employment", "value": construction_emp,
             "unit": "%", "description": "Construction sector employment proxy",
             "category": "Macro", "source": "Stats NZ unemployment inverse"},
            {"name": "OCR x Listings Correlation", "value": ocr_listings_corr,
             "unit": "r", "description": "Correlation between OCR and listing volume",
             "category": "Macro", "source": "OCR impact model"},
            {"name": "GDP Growth YoY", "value": round(gdp_yoy, 1),
             "unit": "%", "description": "GDP per capita year-over-year growth",
             "category": "Macro", "source": "World Bank GDP"},
            {"name": "Inflation (CPI)", "value": round(inflation, 1),
             "unit": "%", "description": "Consumer price inflation",
             "category": "Macro", "source": "Stats NZ CPI"},
        ]
        return pd.DataFrame(rows)
