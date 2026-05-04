"""Forecast backtesting with walk-forward validation.

Evaluates forecast model accuracy using expanding window walk-forward validation.
Produces MAPE, RMSE, directional accuracy, and confidence calibration metrics.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    """Results from a single backtest fold."""

    train_end: int
    test_start: int
    test_end: int
    mape: float
    rmse: float
    mae: float
    directional_accuracy: float
    mean_error: float
    predictions: List[float] = field(default_factory=list)
    actuals: List[float] = field(default_factory=list)


@dataclass
class BacktestSummary:
    """Aggregate backtest results."""

    mean_mape: float
    mean_rmse: float
    mean_mae: float
    mean_directional_accuracy: float
    mean_error_bias: float
    n_folds: int
    fold_results: List[BacktestResult] = field(default_factory=list)


def walk_forward_backtest(
    series: pd.Series,
    forecast_horizon: int = 1,
    min_train_size: int = 5,
    step_size: int = 1,
) -> BacktestSummary:
    """Walk-forward validation with expanding training window.

    Args:
        series: Time series to forecast (indexed by year or sequential int).
        forecast_horizon: Number of periods to forecast ahead.
        min_train_size: Minimum observations required for first training window.
        step_size: How many periods to advance the test window each fold.

    Returns:
        BacktestSummary with aggregate metrics and per-fold results.
    """
    if len(series) < min_train_size + forecast_horizon:
        logger.warning(
            "Series too short for backtest: %d obs, need at least %d",
            len(series),
            min_train_size + forecast_horizon,
        )
        return BacktestSummary(
            mean_mape=0.0,
            mean_rmse=0.0,
            mean_mae=0.0,
            mean_directional_accuracy=0.0,
            mean_error_bias=0.0,
            n_folds=0,
        )

    values = series.dropna().values
    n = len(values)
    fold_results = []

    train_end = min_train_size
    while train_end + forecast_horizon <= n:
        train = values[:train_end]
        test = values[train_end : train_end + forecast_horizon]

        # Simple forecast: last value + mean growth rate
        if len(train) >= 2:
            growth_rates = np.diff(train) / train[:-1]
            mean_growth = np.mean(growth_rates)
            predictions = [
                train[-1] * (1 + mean_growth) ** (i + 1) for i in range(len(test))
            ]
        else:
            predictions = [train[-1]] * len(test)

        # Calculate metrics
        test_arr = np.array(test)
        pred_arr = np.array(predictions)

        # MAPE
        nonzero_mask = test_arr != 0
        if nonzero_mask.any():
            mape = float(
                np.mean(
                    np.abs(
                        (test_arr[nonzero_mask] - pred_arr[nonzero_mask])
                        / test_arr[nonzero_mask]
                    )
                )
                * 100
            )
        else:
            mape = 0.0

        # RMSE
        rmse = float(np.sqrt(np.mean((test_arr - pred_arr) ** 2)))

        # MAE
        mae = float(np.mean(np.abs(test_arr - pred_arr)))

        # Directional accuracy
        if len(test) >= 2:
            actual_direction = np.sign(np.diff(test_arr))
            pred_direction = np.sign(np.diff(pred_arr))
            if len(actual_direction) > 0:
                directional_accuracy = float(
                    np.mean(actual_direction == pred_direction) * 100
                )
            else:
                directional_accuracy = 50.0
        else:
            directional_accuracy = 50.0

        # Mean error (bias)
        mean_error = float(np.mean(test_arr - pred_arr))

        fold_results.append(
            BacktestResult(
                train_end=train_end,
                test_start=train_end,
                test_end=train_end + forecast_horizon,
                mape=mape,
                rmse=rmse,
                mae=mae,
                directional_accuracy=directional_accuracy,
                mean_error=mean_error,
                predictions=list(predictions),
                actuals=test_arr.tolist(),
            )
        )

        train_end += step_size

    if not fold_results:
        return BacktestSummary(
            mean_mape=0.0,
            mean_rmse=0.0,
            mean_mae=0.0,
            mean_directional_accuracy=0.0,
            mean_error_bias=0.0,
            n_folds=0,
        )

    return BacktestSummary(
        mean_mape=float(np.mean([f.mape for f in fold_results])),
        mean_rmse=float(np.mean([f.rmse for f in fold_results])),
        mean_mae=float(np.mean([f.mae for f in fold_results])),
        mean_directional_accuracy=float(
            np.mean([f.directional_accuracy for f in fold_results])
        ),
        mean_error_bias=float(np.mean([f.mean_error for f in fold_results])),
        n_folds=len(fold_results),
        fold_results=fold_results,
    )


def backtest_from_features(
    features: Dict[str, pd.DataFrame],
    target_col: str = "gdp_per_capita",
    feature_key: str = "affordability",
    forecast_horizon: int = 1,
    min_train_size: int = 5,
) -> BacktestSummary:
    """Run backtest using silver layer features.

    Args:
        features: Dict of feature DataFrames from silver layer.
        target_col: Column name to forecast.
        feature_key: Key in features dict containing the target series.
        forecast_horizon: Steps ahead to forecast.
        min_train_size: Minimum training window size.

    Returns:
        BacktestSummary with results.
    """
    df = features.get(feature_key)
    if df is None or df.empty or target_col not in df.columns:
        logger.warning("Feature %s with column %s not found", feature_key, target_col)
        return BacktestSummary(
            mean_mape=0.0,
            mean_rmse=0.0,
            mean_mae=0.0,
            mean_directional_accuracy=0.0,
            mean_error_bias=0.0,
            n_folds=0,
        )

    series = (
        df.set_index("year")[target_col] if "year" in df.columns else df[target_col]
    )
    return walk_forward_backtest(
        series=series,
        forecast_horizon=forecast_horizon,
        min_train_size=min_train_size,
    )


def format_backtest_report(summary: BacktestSummary) -> str:
    """Format backtest results as a human-readable report."""
    lines = [
        "=" * 50,
        "FORECAST BACKTEST REPORT",
        "=" * 50,
        f"Folds evaluated: {summary.n_folds}",
        "",
        "AGGREGATE METRICS",
        f"  Mean MAPE:              {summary.mean_mape:.1f}%",
        f"  Mean RMSE:              {summary.mean_rmse:.2f}",
        f"  Mean MAE:               {summary.mean_mae:.2f}",
        f"  Directional Accuracy:   {summary.mean_directional_accuracy:.1f}%",
        f"  Mean Error Bias:        {summary.mean_error_bias:.2f}",
        "",
    ]

    if summary.fold_results:
        lines.append("PER-FOLD RESULTS")
        lines.append(
            f"  {'Fold':<6} {'Train End':<10} {'MAPE':<10} {'RMSE':<10} {'Dir Acc':<10}"
        )
        lines.append(f"  {'-' * 6} {'-' * 10} {'-' * 10} {'-' * 10} {'-' * 10}")
        for i, fold in enumerate(summary.fold_results):
            lines.append(
                f"  {i + 1:<6} {fold.train_end:<10} {fold.mape:<10.1f} {fold.rmse:<10.2f} {fold.directional_accuracy:<10.1f}"
            )

    lines.append("=" * 50)
    return "\n".join(lines)
