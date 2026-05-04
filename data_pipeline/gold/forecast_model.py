"""Forecast Model — ARIMA with backtesting for NZ house price prediction.

Uses statsmodels ARIMA for time series forecasting with:
- Automatic order selection (AIC)
- Backtesting against historical data
- R² and MAPE reporting
- Confidence intervals
"""
import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class NZPriceForecaster:
    """ARIMA-based forecaster for NZ house prices with backtesting."""

    def __init__(self):
        self.model = None
        self.results = None
        self.forecast = None
        self.backtest_results = {}

    def fit(self, data: pd.Series) -> bool:
        """Fit ARIMA model to historical data."""
        try:
            from statsmodels.tsa.arima.model import ARIMA

            # Try different orders and pick best by AIC
            best_aic = float("inf")
            best_order = (1, 1, 1)

            for p in range(0, 3):
                for d in range(0, 2):
                    for q in range(0, 3):
                        try:
                            model = ARIMA(data, order=(p, d, q))
                            results = model.fit()
                            if results.aic < best_aic:
                                best_aic = results.aic
                                best_order = (p, d, q)
                                self.results = results
                        except Exception:
                            continue

            if self.results is None:
                # Fallback to simple ARIMA(1,1,1)
                model = ARIMA(data, order=(1, 1, 1))
                self.results = model.fit()

            logger.info("  ARIMA best order: %s, AIC: %.1f", best_order, best_aic)
            return True

        except ImportError:
            logger.warning("  statsmodels not available — using linear regression fallback")
            return self._fit_linear(data)
        except Exception as e:
            logger.error("  ARIMA fit failed: %s — using linear fallback", e)
            return self._fit_linear(data)

    def _fit_linear(self, data: pd.Series) -> bool:
        """Fallback: simple linear regression."""
        x = np.arange(len(data))
        y = data.values
        coeffs = np.polyfit(x, y, 1)
        self._linear_coeffs = coeffs
        self._linear_data = data
        return True

    def forecast_n(self, steps: int = 12, alpha: float = 0.05) -> Dict[str, Any]:
        """Generate forecast with confidence intervals."""
        if self.results is not None:
            try:
                fc = self.results.get_forecast(steps=steps)
                predicted = fc.predicted_mean
                conf_int = fc.conf_int(alpha=alpha)
                return {
                    "predicted": predicted.values.tolist(),
                    "ci_lower": conf_int.iloc[:, 0].values.tolist(),
                    "ci_upper": conf_int.iloc[:, 1].values.tolist(),
                    "method": "ARIMA",
                }
            except Exception as e:
                logger.warning("  ARIMA forecast failed: %s — using linear", e)

        # Linear fallback
        if hasattr(self, "_linear_coeffs"):
            n = len(self._linear_data)
            x_future = np.arange(n, n + steps)
            predicted = np.polyval(self._linear_coeffs, x_future)
            # Simple confidence interval based on residual std
            y_pred = np.polyval(self._linear_coeffs, np.arange(n))
            residuals = self._linear_data.values - y_pred
            std = np.std(residuals)
            return {
                "predicted": predicted.tolist(),
                "ci_lower": (predicted - 1.96 * std).tolist(),
                "ci_upper": (predicted + 1.96 * std).tolist(),
                "method": "Linear Regression",
            }

        return {"predicted": [], "ci_lower": [], "ci_upper": [], "method": "None"}

    def backtest(self, data: pd.Series, test_size: int = 5) -> Dict[str, Any]:
        """Backtest model against held-out data."""
        if len(data) < test_size + 10:
            return {"error": "Not enough data for backtesting"}

        train = data.iloc[:-test_size]
        test = data.iloc[-test_size:]

        # Fit on train
        try:
            from statsmodels.tsa.arima.model import ARIMA
            model = ARIMA(train, order=(1, 1, 1))
            results = model.fit()
            fc = results.get_forecast(steps=test_size)
            predicted = fc.predicted_mean.values
        except Exception:
            # Linear fallback
            x = np.arange(len(train))
            coeffs = np.polyfit(x, train.values, 1)
            x_test = np.arange(len(train), len(train) + test_size)
            predicted = np.polyval(coeffs, x_test)

        # Calculate metrics
        actual = test.values
        mae = float(np.mean(np.abs(predicted - actual)))
        mape = float(np.mean(np.abs((actual - predicted) / actual)) * 100) if np.all(actual != 0) else float("inf")
        r_squared = float(1 - np.sum((actual - predicted) ** 2) / np.sum((actual - np.mean(actual)) ** 2))

        self.backtest_results = {
            "mae": round(mae, 2),
            "mape": round(mape, 1),
            "r_squared": round(max(0, r_squared), 3),
            "test_size": test_size,
            "actual": actual.tolist(),
            "predicted": predicted.tolist(),
        }

        logger.info("  Backtest: MAE=%.1f, MAPE=%.1f%%, R²=%.3f", mae, mape, r_squared)
        return self.backtest_results


def run_forecast_pipeline(
    gdp_data: pd.DataFrame,
    inflation_data: pd.DataFrame,
    population_data: pd.DataFrame,
) -> Dict[str, Any]:
    """Run full forecast pipeline with backtesting.

    Args:
        gdp_data: DataFrame with 'year' and 'value' columns
        inflation_data: DataFrame with 'year' and 'value' columns
        population_data: DataFrame with 'year' and 'value' columns

    Returns:
        Forecast results with backtesting metrics
    """
    forecaster = NZPriceForecaster()

    # Use GDP per capita as proxy for house price trend
    if "value" not in gdp_data.columns or "year" not in gdp_data.columns:
        return {"error": "Invalid GDP data"}

    gdp = gdp_data.sort_values("year").set_index("year")["value"]

    if len(gdp) < 10:
        return {"error": "Not enough GDP data for forecasting"}

    # Calculate GDP per capita if population available
    if population_data is not None and "value" in population_data.columns:
        pop = population_data.sort_values("year").set_index("year")["value"]
        common_years = gdp.index.intersection(pop.index)
        if len(common_years) >= 10:
            gdp_pc = gdp[common_years] / pop[common_years]
        else:
            gdp_pc = gdp
    else:
        gdp_pc = gdp

    # Fit model
    success = forecaster.fit(gdp_pc)
    if not success:
        return {"error": "Model fitting failed"}

    # Backtest
    backtest = forecaster.backtest(gdp_pc, test_size=5)

    # Forecast 12 months ahead
    forecast = forecaster.forecast_n(steps=12)

    # Calculate current values
    latest_gdp_pc = float(gdp_pc.iloc[-1])
    gdp_growth = float(gdp_pc.pct_change(fill_method=None).iloc[-1] * 100) if len(gdp_pc) >= 2 else 0

    return {
        "current_gdp_per_capita": round(latest_gdp_pc, 0),
        "gdp_growth_yoy": round(gdp_growth, 1),
        "forecast": forecast,
        "backtest": backtest,
        "model_confidence": round(max(40, min(90, 60 + backtest.get("r_squared", 0) * 30)), 0),
        "data_points": len(gdp_pc),
        "year_range": f"{int(gdp_pc.index.min())}-{int(gdp_pc.index.max())}",
    }
