"""
Schema validation for NZ Habitat Intelligence pipeline.
Provides validation at Bronze, Silver, and Gold layers to catch data issues early.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation strictness levels."""

    LENIENT = "lenient"  # Only critical checks
    MODERATE = "moderate"  # Standard checks
    STRICT = "strict"  # All checks including best practices


@dataclass
class ValidationResult:
    """Result of a validation check."""

    passed: bool
    level: ValidationLevel
    errors: List[str]
    warnings: List[str]
    info: Dict[str, Any]

    def merge(self, other: "ValidationResult") -> "ValidationResult":
        """Merge two validation results."""
        return ValidationResult(
            passed=self.passed and other.passed,
            level=self.level,
            errors=self.errors + other.errors,
            warnings=self.warnings + other.warnings,
            info={**self.info, **other.info},
        )


class SchemaValidator:
    """
    Schema validator for pipeline data.
    Validates data at ingestion points to catch issues early.
    """

    WORLD_BANK_SCHEMA = {
        "required": ["country", "indicator", "year", "value"],
        "optional": [],
        "types": {
            "country": "string",
            "indicator": "string",
            "year": "integer",
            "value": "float",
        },
        "constraints": {
            "year": {"min": 1960, "max": 2030},
            "value": {
                "min": None,
                "max": None,
            },  # Allow any value including negative (for growth rates)
        },
    }

    POPULATION_SCHEMA = {
        "required": ["region", "year", "population"],
        "optional": ["growth_rate"],
        "types": {
            "region": "string",
            "year": "integer",
            "population": "integer",
            "growth_rate": "float",
        },
        "constraints": {
            "year": {"min": 1960, "max": 2050},
            "population": {"min": 0, "max": None},
            "growth_rate": {"min": -20, "max": 30},
        },
    }

    RBNZ_OCR_SCHEMA = {
        "required": ["date", "indicator", "value"],
        "optional": [],
        "types": {"date": "datetime", "indicator": "string", "value": "float"},
        "constraints": {
            "value": {"min": -5, "max": 25}  # Reasonable OCR range
        },
    }

    TOURISM_SCHEMA = {
        "required": ["region", "year", "visitors"],
        "optional": ["growth_yoy", "seasonal_index"],
        "types": {
            "region": "string",
            "year": "integer",
            "visitors": "integer",
            "growth_yoy": "float",
            "seasonal_index": "float",
        },
        "constraints": {
            "year": {"min": 1960, "max": 2050},
            "visitors": {"min": 0, "max": None},
            "growth_yoy": {"min": -50, "max": 100},
            "seasonal_index": {"min": 0, "max": 5},
        },
    }

    BUILDING_CONSENTS_SCHEMA = {
        "required": ["region", "year", "consents"],
        "optional": ["growth_yoy"],
        "types": {
            "region": "string",
            "year": "integer",
            "consents": "integer",
            "growth_yoy": "float",
        },
        "constraints": {
            "year": {"min": 1960, "max": 2050},
            "consents": {"min": 0, "max": None},
            "growth_yoy": {"min": -50, "max": 100},
        },
    }

    SCHEMA_MAP = {
        "world_bank": WORLD_BANK_SCHEMA,
        "population": POPULATION_SCHEMA,
        "rbnz_ocr": RBNZ_OCR_SCHEMA,
        "tourism": TOURISM_SCHEMA,
        "building_consents": BUILDING_CONSENTS_SCHEMA,
    }

    def __init__(self, level: ValidationLevel = ValidationLevel.MODERATE):
        """
        Initialize schema validator.

        Args:
            level: Validation strictness level
        """
        self.level = level
        self.logger = logging.getLogger(__name__)

    def validate_dataframe(
        self, df: pd.DataFrame, schema_name: str, source_name: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate a DataFrame against a known schema.

        Args:
            df: DataFrame to validate
            schema_name: Name of schema to validate against
            source_name: Optional source name for logging

        Returns:
            ValidationResult with pass/fail and error details
        """
        errors = []
        warnings = []
        info = {"row_count": len(df), "column_count": len(df.columns)}

        if schema_name not in self.SCHEMA_MAP:
            warnings.append(f"Unknown schema '{schema_name}', skipping validation")
            return ValidationResult(
                passed=True, level=self.level, errors=[], warnings=warnings, info=info
            )

        schema = self.SCHEMA_MAP[schema_name]

        # Check required columns
        for col in schema["required"]:
            if col not in df.columns:
                errors.append(f"Missing required column: {col}")

        # Type checking (if level is strict)
        if self.level == ValidationLevel.STRICT:
            for col, expected_type in schema["types"].items():
                if col in df.columns:
                    type_ok, type_error = self._check_type(df[col], expected_type)
                    if not type_ok:
                        errors.append(f"Type error in {col}: {type_error}")

        # Constraint checking
        for col, constraints in schema.get("constraints", {}).items():
            if col in df.columns:
                constraint_errors = self._check_constraints(df[col], col, constraints)
                errors.extend(constraint_errors)

        # Null checking
        for col in schema["required"]:
            if col in df.columns:
                null_count = df[col].isna().sum()
                null_pct = (null_count / len(df)) * 100 if len(df) > 0 else 0
                if null_pct > 50 and self.level != ValidationLevel.LENIENT:
                    warnings.append(f"Column '{col}' has {null_pct:.1f}% null values")
                elif null_count > 0:
                    errors.append(f"Column '{col}' has {null_count} null values")

        passed = len(errors) == 0

        if not passed:
            self.logger.error(
                f"Validation failed for {source_name or schema_name}: {errors}"
            )
        elif warnings:
            self.logger.warning(
                f"Validation passed with warnings for {source_name or schema_name}: {warnings}"
            )

        return ValidationResult(
            passed=passed, level=self.level, errors=errors, warnings=warnings, info=info
        )

    def _check_type(self, series: pd.Series, expected_type: str) -> tuple:
        """Check if series matches expected type."""
        if expected_type == "string":
            if series.dtype == object:
                return True, ""
            return False, f"expected object, got {series.dtype}"
        elif expected_type == "integer":
            if pd.api.types.is_integer_dtype(series):
                return True, ""
            # Check if convertible
            try:
                series.dropna().astype(int)
                return True, ""
            except (ValueError, TypeError):
                return False, "cannot convert to integer"
        elif expected_type == "float":
            if pd.api.types.is_float_dtype(series):
                return True, ""
            try:
                series.dropna().astype(float)
                return True, ""
            except (ValueError, TypeError):
                return False, "cannot convert to float"
        elif expected_type == "datetime":
            if pd.api.types.is_datetime64_any_dtype(series):
                return True, ""
            try:
                pd.to_datetime(series.dropna())
                return True, ""
            except Exception:
                return False, "cannot convert to datetime"
        return True, ""

    def _check_constraints(
        self, series: pd.Series, col_name: str, constraints: Dict[str, Any]
    ) -> List[str]:
        """Check if series meets constraints."""
        errors = []

        min_val = constraints.get("min")
        max_val = constraints.get("max")

        if min_val is not None and pd.api.types.is_numeric_dtype(series):
            below_min = (series < min_val).sum()
            if below_min > 0:
                errors.append(
                    f"Column '{col_name}' has {below_min} values below minimum ({min_val})"
                )

        if max_val is not None and pd.api.types.is_numeric_dtype(series):
            above_max = (series > max_val).sum()
            if above_max > 0:
                errors.append(
                    f"Column '{col_name}' has {above_max} values above maximum ({max_val})"
                )

        return errors

    def validate_schema_compatibility(
        self,
        df1: pd.DataFrame,
        df2: pd.DataFrame,
        name1: str = "df1",
        name2: str = "df2",
    ) -> ValidationResult:
        """
        Validate that two DataFrames have compatible schemas.

        Args:
            df1: First DataFrame
            df2: Second DataFrame
            name1: Name of first DataFrame
            name2: Name of second DataFrame

        Returns:
            ValidationResult
        """
        errors = []
        warnings = []

        cols1 = set(df1.columns)
        cols2 = set(df2.columns)

        only_in_1 = cols1 - cols2
        only_in_2 = cols2 - cols1

        if only_in_1:
            warnings.append(f"Columns only in {name1}: {only_in_1}")
        if only_in_2:
            warnings.append(f"Columns only in {name2}: {only_in_2}")

        common_cols = cols1 & cols2
        if not common_cols:
            errors.append(f"No common columns between {name1} and {name2}")

        return ValidationResult(
            passed=len(errors) == 0,
            level=self.level,
            errors=errors,
            warnings=warnings,
            info={"common_columns": len(common_cols)},
        )


def validate_bronze_ingestion(
    df: pd.DataFrame,
    source_type: str,
    level: ValidationLevel = ValidationLevel.MODERATE,
) -> ValidationResult:
    """
    Convenience function to validate bronze layer ingestion.

    Args:
        df: DataFrame to validate
        source_type: Type of source (world_bank, population, rbnz_ocr, tourism, building_consents)
        level: Validation level

    Returns:
        ValidationResult
    """
    validator = SchemaValidator(level)
    return validator.validate_dataframe(df, source_type)


def validate_silver_features(
    df: pd.DataFrame,
    feature_name: str,
    level: ValidationLevel = ValidationLevel.MODERATE,
) -> ValidationResult:
    """
    Validate silver layer feature data.

    Args:
        df: Feature DataFrame
        feature_name: Name of feature
        level: Validation level

    Returns:
        ValidationResult
    """
    errors = []
    warnings = []

    # Check for required feature columns
    if "region" not in df.columns and "year" not in df.columns:
        errors.append("Feature must have either 'region' or 'year' column")

    # Check for numeric columns (features should be numeric)
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) == 0:
        warnings.append("Feature has no numeric columns")

    # Check for null-heavy columns
    for col in df.columns:
        null_pct = df[col].isna().sum() / len(df) if len(df) > 0 else 0
        if null_pct > 0.5:
            warnings.append(f"Column '{col}' is {null_pct * 100:.1f}% null")

    return ValidationResult(
        passed=len(errors) == 0,
        level=level,
        errors=errors,
        warnings=warnings,
        info={"numeric_columns": len(numeric_cols), "row_count": len(df)},
    )
