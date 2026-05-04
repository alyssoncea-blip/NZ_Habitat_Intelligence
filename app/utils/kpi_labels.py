"""Executive-friendly labels for technical KPI names."""

KPI_LABEL_MAP = {
    "Habitat Intelligence Score": "Habitat Score",
    "GDP per Capita YoY": "GDP per Capita Growth",
    "Interest Rate Stability": "Rate Stability",
    "Tourism-Economy Link": "Tourism-Economy Correlation",
    "Housing Supply Pressure": "Housing Supply Stress",
    "Rent Inflation Premium": "Rent vs CPI Premium",
    "Median House Price Estimate": "Median House Price",
    "Average Days on Market": "Days on Market",
    "Annual New Listings": "New Listings (Annual)",
    "Houses as % of Listings": "House Listing Share",
    "Average Price per m²": "Price per m2",
    "Housing Supply Gap": "Housing Deficit",
    "Tourism Pressure Index": "Tourism Pressure",
    "Airbnb Share of Rentals": "Airbnb Rental Share",
    "Tourism to Rent Price Lag": "Tourism-to-Rent Lag",
    "Visitor Seasonality Strength": "Seasonality Strength",
    "Tourism-Housing Market Link": "Tourism-Housing Link",
    "Current OCR vs 10y Avg": "OCR vs 10Y Average",
    "5yr Mortgage Rate Estimate": "5Y Mortgage Rate",
    "Construction Sector Stability": "Construction Stability",
    "Home Price to Income Ratio": "Price-to-Income Ratio",
    "Rent Burden Benchmark": "Rent Burden",
    "Regional Affordability Spread": "Regional Affordability Gap",
    "Net Internal Migration": "Net Internal Migration",
    "12-Month Price Change Forecast": "12M Price Forecast",
    "Forecast Confidence Range": "Forecast Confidence Range",
    "Regions with High Forecast Risk": "High-Risk Regions",
    "Overall Model Confidence": "Model Confidence",
}


def to_executive_label(technical_name):
    """Return concise executive label while preserving KPI identity."""
    if technical_name is None:
        return "KPI"
    name = str(technical_name)
    return KPI_LABEL_MAP.get(name, name)
