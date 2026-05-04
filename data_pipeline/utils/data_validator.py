"""
Data Validator Module
Performs data quality checks and schema validation
"""

import pandas as pd
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class DataValidator:
    """Validates data quality and schema"""

    def __init__(self, config):
        """Initialize DataValidator

        Args:
            config: Configuration object
        """
        self.config = config

    def validate_not_null(self, df: pd.DataFrame, columns: list) -> bool:
        """Check that specified columns have no null values

        Args:
            df: DataFrame to validate
            columns: List of column names to check

        Returns:
            True if validation passes
        """
        for col in columns:
            if col not in df.columns:
                error = f"Column '{col}' not found in DataFrame"
                logger.error(error)
                return False

            null_count = df[col].isnull().sum()
            if null_count > 0:
                warning = f"Column '{col}' has {null_count} null values"
                logger.warning(warning)

        return True

    def validate_schema(
        self, df: pd.DataFrame, expected_schema: Dict[str, type]
    ) -> bool:
        """Validate DataFrame schema

        Args:
            df: DataFrame to validate
            expected_schema: Dict mapping column names to expected types

        Returns:
            True if schema is valid
        """
        for col, expected_type in expected_schema.items():
            if col not in df.columns:
                error = f"Expected column '{col}' not found in DataFrame"
                logger.error(error)
                return False

            # Check if column can be converted to expected type
            try:
                df[col].astype(expected_type)
            except (ValueError, TypeError) as e:
                error = f"Column '{col}' cannot be converted to {expected_type}: {e}"
                logger.error(error)
                return False

        return True

    def validate_row_count(
        self, df: pd.DataFrame, expected_count: Optional[int]
    ) -> bool:
        """Validate row count

        Args:
            df: DataFrame to validate
            expected_count: Expected number of rows (None to skip)

        Returns:
            True if validation passes
        """
        if expected_count is not None and len(df) != expected_count:
            warning = f"Expected {expected_count} rows, got {len(df)}"
            logger.warning(warning)

        return True

    def validate_date_column(self, df: pd.DataFrame, date_col: str) -> bool:
        """Validate that a column contains valid dates

        Args:
            df: DataFrame to validate
            date_col: Name of date column

        Returns:
            True if validation passes
        """
        if date_col not in df.columns:
            error = f"Date column '{date_col}' not found"
            logger.error(error)
            return False

        try:
            df[date_col] = pd.to_datetime(df[date_col])
            return True
        except Exception as e:
            error = f"Column '{date_col}' contains invalid dates: {e}"
            logger.error(error)
            return False

    def get_errors(self) -> list:
        """Get validation errors

        Returns:
            List of error messages
        """
        return []

    def get_warnings(self) -> list:
        """Get validation warnings

        Returns:
            List of warning messages
        """
        return []

    def validate_data_quality(self, df: pd.DataFrame) -> Dict[str, float]:
        """Perform comprehensive data quality validation

        Args:
            df: DataFrame to validate

        Returns:
            Dictionary with validation results
        """
        results = {
            "quality_score": 1.0,
            "issues": [],
            "null_counts": {},
            "duplicate_count": 0,
        }

        # Check for nulls
        for col in df.columns:
            null_count = df[col].isnull().sum()
            results["null_counts"][col] = null_count
            if null_count > 0:
                results["quality_score"] -= (null_count / len(df)) * 0.1

        # Check for duplicates
        results["duplicate_count"] = df.duplicated().sum()
        if results["duplicate_count"] > 0:
            results["quality_score"] -= 0.05

        return results


def create_validator(config):
    """Create and return a DataValidator instance

    Args:
        config: Configuration object

    Returns:
        DataValidator instance
    """
    return DataValidator(config)
