"""Tests for chart generation."""

import base64
import pytest

from src.charts.generator import generate_chart
from src.charts.types import ChartType


class TestChartGenerator:
    """Tests for chart generation."""

    @pytest.fixture
    def sample_data(self):
        return {
            "Fund A": 1.2,
            "Fund B": 0.9,
            "Fund C": 1.5,
            "Fund D": 0.8,
        }

    def test_bar_chart_generation(self, sample_data):
        """Test that bar charts are generated correctly."""
        result = generate_chart(
            data=sample_data,
            title="MER Comparison",
            chart_type="bar",
        )

        assert result.startswith("data:image/png;base64,")
        # Verify it's valid base64
        base64_data = result.replace("data:image/png;base64,", "")
        decoded = base64.b64decode(base64_data)
        assert len(decoded) > 0
        # PNG magic bytes
        assert decoded[:8] == b'\x89PNG\r\n\x1a\n'

    def test_line_chart_generation(self, sample_data):
        """Test that line charts are generated correctly."""
        result = generate_chart(
            data=sample_data,
            title="Performance Over Time",
            chart_type="line",
        )

        assert result.startswith("data:image/png;base64,")

    def test_pie_chart_generation(self, sample_data):
        """Test that pie charts are generated correctly."""
        result = generate_chart(
            data=sample_data,
            title="Asset Allocation",
            chart_type="pie",
        )

        assert result.startswith("data:image/png;base64,")

    def test_scatter_chart_generation(self, sample_data):
        """Test that scatter charts are generated correctly."""
        result = generate_chart(
            data=sample_data,
            title="Risk vs Return",
            chart_type="scatter",
        )

        assert result.startswith("data:image/png;base64,")

    def test_histogram_generation(self):
        """Test that histograms are generated correctly."""
        data = {
            "Bin1": 5,
            "Bin2": 10,
            "Bin3": 15,
            "Bin4": 8,
            "Bin5": 3,
        }
        result = generate_chart(
            data=data,
            title="Return Distribution",
            chart_type="histogram",
        )

        assert result.startswith("data:image/png;base64,")

    def test_empty_data_handling(self):
        """Test that empty data is handled gracefully."""
        result = generate_chart(
            data={},
            title="Empty Chart",
            chart_type="bar",
        )
        # Should still return a valid image (empty chart)
        assert result.startswith("data:image/png;base64,")


class TestChartTypes:
    """Tests for chart type definitions."""

    def test_chart_type_enum(self):
        """Test ChartType enum values."""
        assert ChartType.BAR.value == "bar"
        assert ChartType.LINE.value == "line"
        assert ChartType.PIE.value == "pie"
        assert ChartType.SCATTER.value == "scatter"
        assert ChartType.HISTOGRAM.value == "histogram"
