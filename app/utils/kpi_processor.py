"""
KPI processing for visualization
Transformation and enrichment of data for premium dashboards
"""
import pandas as pd
import numpy as np
from .style_config import get_kpi_color
from .logger import get_logger

logger = get_logger(__name__)

def process_kpis_for_visualization(kpis_df):
    """
    Process KPI data for visualization.

    Args:
        kpis_df: DataFrame, dict, or None with KPIs (quality or legacy format)

    Returns:
        Dict with processed KPIs ready for visualization
    """
    if kpis_df is None:
        logger.warning("None KPI data")
        return {"kpis": [], "summary": {}}

    # Handle dict input (from dashboard data modules)
    if isinstance(kpis_df, dict):
        kpi_list = kpis_df.get("kpis", [])
        if not kpi_list:
            logger.warning("Empty KPI dict")
            return {"kpis": [], "summary": {}}
        df = pd.DataFrame(kpi_list)
    elif isinstance(kpis_df, pd.DataFrame):
        if kpis_df.empty:
            logger.warning("Empty KPI DataFrame")
            return {"kpis": [], "summary": {}}
        df = kpis_df.copy()
    else:
        logger.warning(f"Unexpected KPI data type: {type(kpis_df)}")
        return {"kpis": [], "summary": {}}

    logger.info(f"Processing {len(df)} KPIs for visualization")

    # Detect format
    is_quality_format = all(col in df.columns for col in ['name', 'value', 'unit', 'description'])
    is_legacy_format = len(df.columns) >= 4 and not is_quality_format

    if is_quality_format:
        logger.info("Detected QUALITY format")
        processed_df = process_quality_format(df)
    elif is_legacy_format:
        logger.info("Detected LEGACY format")
        processed_df = process_legacy_format(df)
    else:
        logger.warning("Unknown format, attempting basic processing")
        processed_df = process_basic_format(df)

    # Add common calculated fields
    processed_df = add_calculated_fields(processed_df)

    # Sort by category and importance
    processed_df = sort_kpis_by_importance(processed_df)

    logger.info(f"Processing complete: {len(processed_df)} KPIs ready")
    return {"kpis": processed_df.to_dict(orient="records"), "summary": get_kpi_summary(processed_df)}

def process_quality_format(df):
    """Process QUALITY format (complete)."""
    processed = df.copy()

    # Ensure consistent types
    if 'value' in processed.columns:
        processed['value'] = pd.to_numeric(processed['value'], errors='coerce')

    # Add missing fields if absent
    if 'category' not in processed.columns:
        processed['category'] = 'general'

    if 'source' not in processed.columns:
        processed['source'] = 'Unknown'

    if 'confidence' not in processed.columns:
        processed['confidence'] = calculate_confidence(processed)

    # Clean strings
    string_columns = ['name', 'unit', 'description', 'category', 'source']
    for col in string_columns:
        if col in processed.columns:
            processed[col] = processed[col].astype(str).str.strip()

    return processed

def process_legacy_format(df):
    """Process LEGACY format (arrays)"""
    # Assume first columns are [name, value, unit, description, ...]
    processed = pd.DataFrame()

    if len(df.columns) >= 1:
        processed['name'] = df.iloc[:, 0].astype(str).str.strip()

    if len(df.columns) >= 2:
        processed['value'] = pd.to_numeric(df.iloc[:, 1], errors='coerce')

    if len(df.columns) >= 3:
        processed['unit'] = df.iloc[:, 2].astype(str).str.strip()

    if len(df.columns) >= 4:
        processed['description'] = df.iloc[:, 3].astype(str).str.strip()

    # Default fields
    processed['category'] = 'general'
    processed['source'] = 'Legacy Format'
    processed['confidence'] = calculate_confidence(processed)

    return processed

def process_basic_format(df):
    """Processing for unknown formats"""
    processed = pd.DataFrame()

    # Try to find columns by common names
    name_mapping = {
        'name': ['name', 'kpi_name', 'indicator', 'metric'],
        'value': ['value', 'kpi_value', 'measurement', 'result'],
        'unit': ['unit', 'measurement_unit', 'uom'],
        'description': ['description', 'desc', 'definition', 'notes']
    }

    for standard_col, possible_names in name_mapping.items():
        for possible_name in possible_names:
            if possible_name in df.columns:
                processed[standard_col] = df[possible_name]
                break

    # If 'value' not found, use first numeric column
    if 'value' not in processed.columns:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            processed['value'] = df[numeric_cols[0]]

    # If 'name' not found, create index-based names
    if 'name' not in processed.columns:
        processed['name'] = [f"KPI_{i+1}" for i in range(len(df))]

    # Default fields
    if 'unit' not in processed.columns:
        processed['unit'] = ''

    if 'description' not in processed.columns:
        processed['description'] = ''

    processed['category'] = 'general'
    processed['source'] = 'Auto-detected'
    processed['confidence'] = calculate_confidence(processed)

    return processed

def add_calculated_fields(df):
    """Add calculated fields for visualization - vectorized version."""
    if df.empty:
        return df

    processed = df.copy()

    # Vectorized status and color calculation
    def get_status_color(row):
        try:
            kpi_name = str(row.get('name', ''))
            kpi_value = row.get('value')
            kpi_category = row.get('category', 'general')
            return get_kpi_color(kpi_name, kpi_value, kpi_category)
        except Exception as e:
            logger.warning(f"Error calculating color for KPI {row.get('name')}: {e}")
            return ('Unknown', '#6c757d')

    status_colors = processed.apply(get_status_color, axis=1)
    processed['status'] = status_colors.apply(lambda x: x[0])
    processed['color'] = status_colors.apply(lambda x: x[1])

    # Add trend using vectorized function
    processed['trend'] = calculate_trend_vectorized(processed)

    # Add formatted value for display
    processed['display_value'] = format_kpi_value_vectorized(processed)

    # Classify importance
    processed['importance'] = calculate_importance_vectorized(processed)

    return processed


def calculate_trend_vectorized(df):
    """
    Vectorized version of calculate_trend.
    Determines trend (up/down/neutral) based on KPI value.
    """
    # KPIs where higher value is positive
    positive_high_kpis = ['growth', 'increase', 'rate of return', 'score', 'index', 'performance']
    # KPIs where lower value is positive
    positive_low_kpis = ['deficit', 'gap', 'risk', 'volatility', 'uncertainty', 'pressure']

    # Convert value to numeric, defaulting to 0
    values = pd.to_numeric(df.get('value', pd.Series([0]*len(df))), errors='coerce').fillna(0)

    # Check KPI name patterns using vectorized operations
    name_lower = df['name'].astype(str).str.lower()
    is_positive_high = name_lower.str.contains('|'.join(positive_high_kpis), case=False, na=False)
    is_positive_low = name_lower.str.contains('|'.join(positive_low_kpis), case=False, na=False)

    # Initialize trends as 'neutral'
    trends = pd.Series(['neutral'] * len(df))

    # For positive_high KPIs: >10 = up, >0 = slightly up, <-5 = down
    mask_high = is_positive_high
    trends_masked = trends.mask(mask_high & (values > 10), 'up')
    trends_masked = trends_masked.mask(mask_high & (values > 0) & (values <= 10), 'slightly up')
    trends_masked = trends_masked.mask(mask_high & (values < -5), 'down')
    trends = trends_masked

    # For positive_low KPIs: <5 = up, <15 = neutral, else down
    mask_low = is_positive_low & ~mask_high  # Not already assigned
    trends_masked = trends.mask(mask_low & (values < 5), 'up')
    trends_masked = trends_masked.mask(mask_low & (values >= 5) & (values < 15), 'neutral')
    trends_masked = trends_masked.mask(mask_low & (values >= 15), 'down')
    trends = trends_masked

    return trends.tolist()


def format_kpi_value_vectorized(df):
    """
    Vectorized version of format_kpi_value.
    Formats values for display based on unit type.
    """
    def format_single(val, unit):
        if val is None or pd.isna(val):
            return 'N/A'

        try:
            # Format based on unit type
            if '%' in unit:
                return f"{float(val):.1f}%"
            elif any(term in unit for term in ['$', 'USD', 'NZD']):
                if abs(float(val)) >= 1000000:
                    return f"${float(val)/1000000:.1f}M"
                elif abs(float(val)) >= 1000:
                    return f"${float(val)/1000:.1f}K"
                else:
                    return f"${float(val):.0f}"
            elif any(term in unit for term in ['pts', 'score', 'index']):
                return f"{float(val):.1f}"
            else:
                if isinstance(val, float):
                    return f"{val:.2f}"
                else:
                    return str(val)

        except (ValueError, TypeError):
            return str(val) if val is not None else 'N/A'

    # Apply formatting to each row
    return df.apply(lambda row: format_single(row.get('value'), row.get('unit', '')), axis=1).tolist()


def calculate_confidence(df):
    """
    Vectorized version of calculate_confidence.
    Calculates confidence score based on available data fields.
    """
    score = pd.Series([50.0] * len(df))

    has_description = df.get('description', pd.Series(dtype=str)).astype(str).str.strip().str.len() > 0
    score = score + has_description.astype(int) * 10

    has_unit = df.get('unit', pd.Series(dtype=str)).astype(str).str.strip().str.len() > 0
    score = score + has_unit.astype(int) * 10

    category = df.get('category', pd.Series(['general'] * len(df))).astype(str)
    has_category = (category.str.strip().str.len() > 0) & (category != 'general')
    score = score + has_category.astype(int) * 5

    source = df.get('source', pd.Series([''] * len(df))).astype(str).str.lower()
    real_source = source.str.contains('world bank|stats nz|real', case=False, na=False)
    synthetic_source = source.str.contains('synthetic|proxy|estimated', case=False, na=False)
    score = score + real_source.astype(int) * 15
    score = score - synthetic_source.astype(int) * 10

    score = score.clip(0, 100)

    return score.tolist()


def calculate_importance_vectorized(df):
    """
    Vectorized version of calculate_importance.
    Calculates importance score for sorting.
    """
    high_importance_terms = ['habitat', 'intelligence', 'score', 'growth', 'gdp', 'inflation', 'unemployment', 'housing']
    medium_importance_terms = ['rate', 'index', 'pressure', 'deficit', 'gap', 'affordability']

    name_lower = df['name'].astype(str).str.lower()

    # Base score from name matching
    high_match = name_lower.str.contains('|'.join(high_importance_terms), case=False, na=False)
    medium_match = name_lower.str.contains('|'.join(medium_importance_terms), case=False, na=False)

    score = pd.Series([0.0] * len(df))
    score = score + high_match.astype(int) * 30
    score = score + medium_match.astype(int) * 15

    # Add confidence contribution (capped at 20)
    confidence = pd.to_numeric(df.get('confidence', pd.Series([50]*len(df))), errors='coerce').fillna(50)
    score = score + confidence * 0.2

    return score.tolist()

def sort_kpis_by_importance(df):
    """Sort KPIs by importance score."""
    if df.empty or 'importance' not in df.columns:
        return df

    return df.sort_values('importance', ascending=False).reset_index(drop=True)

def filter_kpis_by_category(df, category):
    """Filter KPIs by category."""
    if df.empty or 'category' not in df.columns:
        return pd.DataFrame()

    return df[df['category'].str.lower() == category.lower()].copy()

def get_kpi_summary(df):
    """Return statistical summary of KPIs."""
    if df.empty:
        return {"total_kpis": 0, "categories": [], "avg_confidence": 0}

    summary = {
        "total_kpis": len(df),
        "value_stats": {},
        "categories": [],
        "confidence_stats": {}
    }

    # Value statistics
    if 'value' in df.columns and df['value'].notna().any():
        valid_values = df['value'].dropna()
        if len(valid_values) > 0:
            summary["value_stats"] = {
                "min": float(valid_values.min()),
                "max": float(valid_values.max()),
                "mean": float(valid_values.mean()),
                "median": float(valid_values.median())
            }

    # Count by category
    if 'category' in df.columns:
        cat_counts = df['category'].value_counts()
        summary["categories"] = cat_counts.to_dict()

    # Confidence statistics
    if 'confidence' in df.columns and df['confidence'].notna().any():
        valid_conf = df['confidence'].dropna()
        if len(valid_conf) > 0:
            summary["confidence_stats"] = {
                "avg": float(valid_conf.mean()),
                "min": float(valid_conf.min()),
                "max": float(valid_conf.max())
            }

    # Count by status
    if 'status' in df.columns:
        status_counts = df['status'].value_counts()
        summary["status_counts"] = status_counts.to_dict()

    return summary
