"""
Silver Layer - Data Transformation Utilities
Additional transformation functions for silver layer
"""
import logging
import pandas as pd
from typing import List

def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names to snake_case
    
    Args:
        df: DataFrame with potentially mixed column names
    
    Returns:
        DataFrame with normalized column names
    """
    def to_snake_case(name):
        if not isinstance(name, str):
            return name
        name = name.lower().strip()
        name = name.replace(' ', '_').replace('-', '_').replace('.', '_')
        import re
        name = re.sub(r'[^a-z0-9_]', '', name)
        name = re.sub(r'_+', '_', name)
        return name
    
    df.columns = [to_snake_case(col) for col in df.columns]
    return df

def normalize_dates(df: pd.DataFrame, date_cols: List[str], date_format: str = '%Y-%m-%d') -> pd.DataFrame:
    """Normalize date columns to specified format
    
    Args:
        df: DataFrame with date columns
        date_cols: List of column names containing dates
        date_format: Target date format
    
    Returns:
        DataFrame with standardized dates
    """
    for col in date_cols:
        if col in df.columns:
            try:
                df[col] = pd.to_datetime(df[col]).dt.strftime(date_format)
            except Exception:
                pass
    return df

def remove_duplicates(df: pd.DataFrame, subset_cols: List[str] = None) -> pd.DataFrame:
    """Remove duplicate rows
    
    Args:
        df: DataFrame to process
        subset_cols: Columns to check for duplicates (None for all columns)
    
    Returns:
        DataFrame without duplicates
    """
    initial_count = len(df)
    if subset_cols:
        df = df.drop_duplicates(subset=subset_cols)
    else:
        df = df.drop_duplicates()
    final_count = len(df)
    
    if initial_count != final_count:
        logger = logging.getLogger(__name__)
        logger.info(f"Removed {initial_count - final_count} duplicate rows")
    
    return df

def clean_numeric_fields(df: pd.DataFrame, numeric_cols: List[str]) -> pd.DataFrame:
    """Clean numeric fields by converting to proper types
    
    Args:
        df: DataFrame to process
        numeric_cols: List of numeric column names
    
    Returns:
        DataFrame with cleaned numeric columns
    """
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

def create_transformer(config):
    """Create and return a SilverTransformer instance
    
    Args:
        config: Configuration object
    
    Returns:
        SilverTransformer instance
    """
    return SilverTransformer(config)

class SilverTransformer:
    """Handles data transformation for silver layer"""
    
    def __init__(self, config):
        """Initialize SilverTransformer
        
        Args:
            config: Configuration object
        """
        self.config = config
    
    def standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names to snake_case
        
        Args:
            df: Input DataFrame
        
        Returns:
            DataFrame with standardized columns
        """
        return normalize_column_names(df)
    
    def normalize_dates(self, df: pd.DataFrame, date_cols: List[str]) -> pd.DataFrame:
        """Standardize date formats
        
        Args:
            df: Input DataFrame
            date_cols: List of date column names
        
        Returns:
            DataFrame with standardized dates
        """
        return normalize_dates(df, date_cols)
    
    def remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate rows
        
        Args:
            df: Input DataFrame
        
        Returns:
            DataFrame without duplicates
        """
        return remove_duplicates(df)
    
    def clean_numeric_fields(self, df: pd.DataFrame, numeric_cols: List[str]) -> pd.DataFrame:
        """Clean numeric columns
        
        Args:
            df: Input DataFrame
            numeric_cols: List of numeric column names
        
        Returns:
            DataFrame with cleaned numeric columns
        """
        return clean_numeric_fields(df, numeric_cols)
    
    def validate_transformation(self, df: pd.DataFrame, expected_columns: list):
        """Validate that transformation produced expected columns
        
        Args:
            df: Transformed DataFrame
            expected_columns: List of expected column names
        
        Raises:
            ValueError: If expected columns are missing
        """
        missing_cols = [col for col in expected_columns if col not in df.columns]
        if missing_cols:
            logger = logging.getLogger(__name__)
            logger.warning(f"Missing expected columns after transformation: {missing_cols}")

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply all transformations to DataFrame
        
        Args:
            df: Input DataFrame
        
        Returns:
            Transformed DataFrame
        """
        # Standardize columns
        df = self.standardize_columns(df)
        
        # Normalize dates if date columns exist
        date_cols = [col for col in df.columns if 'date' in col.lower()]
        if date_cols:
            df = self.normalize_dates(df, date_cols)
        
        # Remove duplicates
        df = self.remove_duplicates(df)
        
        # Clean numeric fields
        numeric_cols = [col for col in df.columns if df[col].dtype in ['float64', 'int64']]
        if numeric_cols:
            df = self.clean_numeric_fields(df, numeric_cols)
        
        return df