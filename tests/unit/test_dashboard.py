"""Unit tests for dashboard pages and components."""
import pandas as pd


class TestDashboardImports:
    """Test that all dashboard modules import correctly."""

    def test_import_main_app(self):
        """Test main app import."""
        from app.main import app, server, run_app
        assert app is not None
        assert server is not None
        assert run_app is not None

    def test_import_layout(self):
        """Test layout component import."""
        from app.components.layout import create_layout, create_section_header, create_hero_section, create_filter_bar
        assert create_layout is not None
        assert create_section_header is not None
        assert create_hero_section is not None
        assert create_filter_bar is not None

    def test_import_navigation(self):
        """Test navigation component import."""
        from app.components.navigation import create_navbar
        assert create_navbar is not None

    def test_import_charts(self):
        """Test charts component import."""
        from app.components.charts import (
            create_line_chart,
            create_gauge_chart,
            create_bar_chart,
            create_scatter_plot,
            create_heatmap,
        )
        assert create_line_chart is not None
        assert create_gauge_chart is not None
        assert create_bar_chart is not None
        assert create_scatter_plot is not None
        assert create_heatmap is not None

    def test_import_executive_page(self):
        """Test executive page import."""
        from app.pages.executive import create_executive_dashboard
        assert create_executive_dashboard is not None

    def test_import_housing_page(self):
        """Test housing page import."""
        from app.pages.housing_real import create_housing_dashboard
        assert create_housing_dashboard is not None

    def test_import_tourism_page(self):
        """Test tourism page import."""
        from app.pages.tourism_real import create_tourism_dashboard
        assert create_tourism_dashboard is not None

    def test_import_macro_page(self):
        """Test macro page import."""
        from app.pages.macro import create_macro_dashboard
        assert create_macro_dashboard is not None

    def test_import_affordability_page(self):
        """Test affordability page import."""
        from app.pages.affordability import create_affordability_dashboard
        assert create_affordability_dashboard is not None

    def test_import_forecast_page(self):
        """Test forecast page import."""
        from app.pages.forecast import create_forecast_dashboard
        assert create_forecast_dashboard is not None

    def test_import_data_loader(self):
        """Test data loader import."""
        from app.utils.data_loader import DataLoader, load_kpis_for_dashboard
        assert DataLoader is not None
        assert load_kpis_for_dashboard is not None

    def test_import_kpi_processor(self):
        """Test KPI processor import."""
        from app.utils.kpi_processor import process_kpis_for_visualization
        assert process_kpis_for_visualization is not None

    def test_import_kpi_labels(self):
        """Test KPI labels import."""
        from app.utils.kpi_labels import KPI_LABEL_MAP, to_executive_label
        assert KPI_LABEL_MAP is not None
        assert to_executive_label is not None

    def test_import_style_config(self):
        """Test style config import."""
        from app.utils.style_config import COLORS, FONTS, STYLES, get_kpi_color
        assert COLORS is not None
        assert FONTS is not None
        assert STYLES is not None
        assert get_kpi_color is not None

    def test_import_quality_indicators(self):
        """Test quality indicators import."""
        from app.utils.quality_indicators import (
            get_data_quality_score,
            get_data_quality_score_legacy,
            show_data_source_info,
        )
        assert get_data_quality_score is not None
        assert get_data_quality_score_legacy is not None
        assert show_data_source_info is not None


class TestLayoutComponents:
    """Tests for layout components."""

    def test_create_layout_returns_container(self):
        """Test create_layout returns a Dash container."""
        from app.components.layout import create_layout
        layout = create_layout()
        assert layout is not None

    def test_create_section_header(self):
        """Test create_section_header returns a component."""
        from app.components.layout import create_section_header
        header = create_section_header("Test Title", "Test Subtitle")
        assert header is not None

    def test_create_hero_section(self):
        """Test create_hero_section returns a component."""
        from app.components.layout import create_hero_section
        hero = create_hero_section("Test KPI", "100", "Test subtitle")
        assert hero is not None

    def test_create_filter_bar(self):
        """Test create_filter_bar returns a component."""
        from app.components.layout import create_filter_bar
        filter_bar = create_filter_bar(
            region_options=["All Regions", "Auckland", "Wellington"],
            time_options=["3M", "6M", "12M"],
        )
        assert filter_bar is not None


class TestChartComponents:
    """Tests for chart components."""

    def test_create_line_chart(self):
        """Test create_line_chart returns a Plotly figure."""
        from app.components.charts import create_line_chart
        df = pd.DataFrame({
            "year": [2019, 2020, 2021],
            "value": [10, 20, 30],
        })
        fig = create_line_chart(df, "year", "value", title="Test Chart", show_range=False)
        assert fig is not None

    def test_create_bar_chart(self):
        """Test create_bar_chart returns a Plotly figure."""
        from app.components.charts import create_bar_chart
        df = pd.DataFrame({
            "category": ["A", "B", "C"],
            "value": [10, 20, 30],
        })
        fig = create_bar_chart(df, "category", "value", title="Test Bar Chart")
        assert fig is not None

    def test_create_gauge_chart(self):
        """Test create_gauge_chart returns a Plotly figure."""
        from app.components.charts import create_gauge_chart
        fig = create_gauge_chart(value=75, title="Test Gauge")
        assert fig is not None


class TestDashboardPages:
    """Tests for dashboard page creation."""

    def test_create_executive_dashboard(self):
        """Test executive dashboard creation."""
        from app.pages.executive import create_executive_dashboard
        dashboard = create_executive_dashboard()
        assert dashboard is not None

    def test_create_housing_dashboard(self):
        """Test housing dashboard creation."""
        from app.pages.housing_real import create_housing_dashboard
        dashboard = create_housing_dashboard()
        assert dashboard is not None

    def test_create_tourism_dashboard(self):
        """Test tourism dashboard creation."""
        from app.pages.tourism import create_tourism_dashboard
        dashboard = create_tourism_dashboard()
        assert dashboard is not None

    def test_create_macro_dashboard(self):
        """Test macro dashboard creation."""
        from app.pages.macro import create_macro_dashboard
        dashboard = create_macro_dashboard()
        assert dashboard is not None

    def test_create_affordability_dashboard(self):
        """Test affordability dashboard creation."""
        from app.pages.affordability import create_affordability_dashboard
        dashboard = create_affordability_dashboard()
        assert dashboard is not None

    def test_create_forecast_dashboard(self):
        """Test forecast dashboard creation."""
        from app.pages.forecast import create_forecast_dashboard
        dashboard = create_forecast_dashboard()
        assert dashboard is not None
