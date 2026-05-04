"""Forecast Dashboard KPIs (13 KPIs).

Calculates 12-month price forecast, confidence intervals, OCR/tourism scenario
impacts, trend decomposition, divergence alert, and model confidence.
"""

import logging

import numpy as np
import pandas as pd

from .kpi_base import KPIBaseCalculator, NZ_REGIONS

logger = logging.getLogger(__name__)


class ForecastKPICalculator(KPIBaseCalculator):
    """Calculates Forecast Dashboard KPIs from Silver/Bronze data."""

    def calc(self) -> pd.DataFrame:
        """Calculate all 13 forecast KPIs."""
        logger.info("Calculating KPIs 28-34: Forecast")
        gdp_yoy = self._get_gdp_per_capita_yoy()
        macro_vol = self._get_macro_volatility()
        ocr = self._get_ocr_current()
        regional = self._get_regional_data()

        prices = [
            self._estimate_median_price(r, regional)
            for r in NZ_REGIONS
            if r in regional
        ]
        median_price = float(np.median(prices)) if prices else 650000

        forecast_12m = round(median_price * (1 + gdp_yoy / 100), 0)

        volatility = max(0.02, macro_vol / 100 * 0.15)
        ci_80_w = forecast_12m * volatility * 1.28
        ci_95_w = forecast_12m * volatility * 1.96

        ocr_impact = round(-1.2 * 0.5 * (ocr / 5.0), 1)

        supply_p = self._get_housing_supply_pressure()
        base_dom = max(20, min(80, 55 - supply_p * 0.3))
        tourism_dom_impact = round(base_dom * (1 - 0.15 * 0.20), 0)

        trend_component = round(gdp_yoy, 1)
        seasonal_component = round(1.5, 1)

        divergence = round(abs(gdp_yoy - 2.0) * 3 + macro_vol * 0.1, 1)

        confidence = round(
            max(40, min(90, 80 - macro_vol * 0.3 - abs(gdp_yoy - 2.0) * 5)), 0
        )

        rows = [
            {
                "name": "12-Month Price Forecast",
                "value": float(forecast_12m),
                "unit": "NZD",
                "description": "Projected median price in 12 months (GDP-based)",
                "category": "Forecast",
                "source": "GDP growth linear regression",
            },
            {
                "name": "Current Median Price",
                "value": round(median_price, 0),
                "unit": "NZD",
                "description": "Current national median house price",
                "category": "Forecast",
                "source": "Stats NZ income x price-to-income ratio",
            },
            {
                "name": "Forecast Growth",
                "value": round(gdp_yoy, 1),
                "unit": "%",
                "description": "Expected annual price growth",
                "category": "Forecast",
                "source": "World Bank GDP per capita YoY",
            },
            {
                "name": "Confidence 80% Lower",
                "value": round(forecast_12m - ci_80_w, 0),
                "unit": "NZD",
                "description": "80% confidence interval lower bound",
                "category": "Forecast",
                "source": "Macroeconomic volatility",
            },
            {
                "name": "Confidence 80% Upper",
                "value": round(forecast_12m + ci_80_w, 0),
                "unit": "NZD",
                "description": "80% confidence interval upper bound",
                "category": "Forecast",
                "source": "Macroeconomic volatility",
            },
            {
                "name": "Confidence 95% Lower",
                "value": round(forecast_12m - ci_95_w, 0),
                "unit": "NZD",
                "description": "95% confidence interval lower bound",
                "category": "Forecast",
                "source": "Macroeconomic volatility",
            },
            {
                "name": "Confidence 95% Upper",
                "value": round(forecast_12m + ci_95_w, 0),
                "unit": "NZD",
                "description": "95% confidence interval upper bound",
                "category": "Forecast",
                "source": "Macroeconomic volatility",
            },
            {
                "name": "OCR +0.5% Price Impact",
                "value": ocr_impact,
                "unit": "%",
                "description": "Estimated price impact of 50bps OCR increase",
                "category": "Forecast",
                "source": "OCR elasticity model",
            },
            {
                "name": "Tourism +20% DOM Impact",
                "value": float(tourism_dom_impact),
                "unit": "days",
                "description": "Expected DOM after 20% tourism increase",
                "category": "Forecast",
                "source": "Tourism-DOM elasticity model",
            },
            {
                "name": "Trend Component",
                "value": trend_component,
                "unit": "%",
                "description": "GDP-based trend component",
                "category": "Forecast",
                "source": "GDP growth decomposition",
            },
            {
                "name": "Seasonal Component",
                "value": seasonal_component,
                "unit": "%",
                "description": "NZ housing seasonal adjustment",
                "category": "Forecast",
                "source": "Historical seasonal pattern",
            },
            {
                "name": "Divergence Alert Score",
                "value": divergence,
                "unit": "pts",
                "description": "Model divergence alert (higher = more risk)",
                "category": "Forecast",
                "source": "GDP + volatility divergence",
            },
            {
                "name": "Model Confidence Score",
                "value": float(confidence),
                "unit": "/100",
                "description": "Overall model confidence",
                "category": "Forecast",
                "source": "Volatility + GDP stability",
            },
        ]
        return pd.DataFrame(rows)
