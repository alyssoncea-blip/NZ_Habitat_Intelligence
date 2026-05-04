"""Executive Dashboard KPIs (8 KPIs).

Calculates KPIs 01-08: Habitat Score, GDP YoY, IR Stability, Tourism Link,
Supply Pressure, Rent Gap, OCR, Inflation.
"""

import logging

import pandas as pd

from .kpi_base import KPIBaseCalculator

logger = logging.getLogger(__name__)


class ExecutiveKPICalculator(KPIBaseCalculator):
    """Calculates Executive Dashboard KPIs from Silver/Bronze data."""

    def calc(self) -> pd.DataFrame:
        """Calculate all 8 executive KPIs."""
        logger.info("Calculating KPIs 01-08: Executive")
        gdp_pc = self._get_gdp_per_capita()
        gdp_yoy = self._get_gdp_per_capita_yoy()
        ir_score = self._get_ir_impact_score()
        tour_corr = self._get_tourism_economy_corr()
        supply_p = self._get_housing_supply_pressure()
        rent_erosion = self._get_affordability_erosion()
        ocr = self._get_ocr_current()
        inflation = self._get_inflation_latest()

        habitat_score = round(
            (100 - min(100, ir_score)) * 0.30
            + supply_p * 0.35
            + min(100, gdp_pc / 600) * 0.35,
            1,
        )

        rows = [
            {
                "name": "Habitat Intelligence Score",
                "value": habitat_score,
                "unit": "pts",
                "description": "Overall NZ habitat quality (0-100)",
                "category": "Executive",
                "source": "Silver features composite",
            },
            {
                "name": "GDP per Capita YoY",
                "value": round(gdp_yoy, 1),
                "unit": "%",
                "description": "Economic growth per person",
                "category": "Executive",
                "source": "World Bank GDP",
            },
            {
                "name": "Interest Rate Stability",
                "value": round(100 - min(100, ir_score), 1),
                "unit": "pts",
                "description": "Monetary policy stability (0-100)",
                "category": "Executive",
                "source": "RBNZ/World Bank interest rates",
            },
            {
                "name": "Tourism-Economy Link",
                "value": round(abs(tour_corr) * 100, 1),
                "unit": "%",
                "description": "Tourism-GDP correlation strength",
                "category": "Executive",
                "source": "MBIE tourism + World Bank GDP",
            },
            {
                "name": "Housing Supply Pressure",
                "value": round(supply_p, 1),
                "unit": "pts",
                "description": "Population vs housing growth gap",
                "category": "Executive",
                "source": "Stats NZ building consents + population",
            },
            {
                "name": "Rent Affordability Gap",
                "value": round(rent_erosion, 1),
                "unit": "%-pts",
                "description": "Rent inflation minus wage growth",
                "category": "Executive",
                "source": "Tenancy Services rent + Stats NZ income",
            },
            {
                "name": "Current OCR",
                "value": round(ocr, 2),
                "unit": "%",
                "description": "Reserve Bank Official Cash Rate",
                "category": "Executive",
                "source": "RBNZ OCR",
            },
            {
                "name": "Inflation (CPI)",
                "value": round(inflation, 1),
                "unit": "%",
                "description": "Consumer price inflation annual",
                "category": "Executive",
                "source": "Stats NZ CPI",
            },
        ]
        return pd.DataFrame(rows)
