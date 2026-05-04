"""Pydantic schemas for bronze layer data validation.

Provides schema enforcement for all incoming data sources.
Each schema validates structure, types, and constraints.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class WorldBankRecord(BaseModel):
    """Schema for World Bank API records."""

    year: int = Field(..., ge=1960, le=2030)
    value: float = Field(...)
    country: Optional[str] = "NZL"
    indicator: Optional[str] = None

    @field_validator("year")
    @classmethod
    def year_must_be_reasonable(cls, v: int) -> int:
        if v < 1960 or v > 2030:
            raise ValueError(f"Year {v} is outside reasonable range")
        return v


class RBNZRecord(BaseModel):
    """Schema for RBNZ API records."""

    date: str = Field(...)
    value: float = Field(...)
    indicator: Optional[str] = None

    @field_validator("date")
    @classmethod
    def date_format(cls, v: str) -> str:
        """Validate date is in ISO format."""
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError(f"Invalid date format: {v}")
        return v


class StatsNZRecord(BaseModel):
    """Schema for Stats NZ records."""

    region: str = Field(..., min_length=1)
    year: int = Field(..., ge=1990, le=2030)
    value: Optional[float] = None
    population: Optional[int] = None
    consents: Optional[int] = None
    median_household_income: Optional[float] = None


class MBIERecord(BaseModel):
    """Schema for MBIE tourism records."""

    region: str = Field(..., min_length=1)
    year: int = Field(..., ge=1990, le=2030)
    visitors: Optional[int] = None
    tourism_expenditure_nzd_millions: Optional[float] = None
    growth_yoy: Optional[float] = None


class LINZRecord(BaseModel):
    """Schema for LINZ property records."""

    region: str = Field(..., min_length=1)
    year: int = Field(..., ge=1990, le=2030)
    property_count: Optional[int] = None
    median_price: Optional[float] = None


class REINZRecord(BaseModel):
    """Schema for REINZ sales records."""

    region: str = Field(..., min_length=1)
    year: int = Field(..., ge=1990, le=2030)
    month: Optional[int] = Field(None, ge=1, le=12)
    sales_count: Optional[int] = None
    median_price: Optional[float] = None
    days_to_sell: Optional[int] = None


# Mapping of source name to schema
SCHEMA_MAP: Dict[str, type] = {
    "world_bank": WorldBankRecord,
    "rbnz": RBNZRecord,
    "stats_nz": StatsNZRecord,
    "mbie_tourism": MBIERecord,
    "linz": LINZRecord,
    "reinz": REINZRecord,
}


def validate_records(source: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate a list of records against the source schema.

    Args:
        source: Source name (e.g., "world_bank", "rbnz").
        records: List of record dictionaries.

    Returns:
        Dictionary with validation results:
        - valid: bool
        - valid_count: int
        - invalid_count: int
        - errors: list of error messages
        - validated_records: list of validated records
    """
    schema = SCHEMA_MAP.get(source)
    if schema is None:
        return {
            "valid": False,
            "errors": [f"No schema defined for source: {source}"],
            "valid_count": 0,
            "invalid_count": len(records),
            "validated_records": records,
        }

    errors = []
    validated = []
    invalid_count = 0

    for i, record in enumerate(records):
        try:
            validated_record = schema(**record)
            validated.append(validated_record.model_dump())
        except Exception as e:
            invalid_count += 1
            errors.append(f"Record {i}: {str(e)}")

    return {
        "valid": invalid_count == 0,
        "valid_count": len(validated),
        "invalid_count": invalid_count,
        "errors": errors[:10],  # Limit error messages
        "validated_records": validated,
    }
