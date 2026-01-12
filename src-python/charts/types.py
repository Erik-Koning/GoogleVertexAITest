"""Chart type definitions and validation."""

from enum import Enum
from typing import Literal


class ChartType(str, Enum):
    """Supported chart types."""

    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    HISTOGRAM = "histogram"


ChartTypeLiteral = Literal["bar", "line", "pie", "scatter", "histogram"]

CHART_TYPE_DESCRIPTIONS = {
    ChartType.BAR: "Bar charts for comparing categories (e.g., MER comparison across funds)",
    ChartType.LINE: "Line charts for time series and trends (e.g., historical performance)",
    ChartType.PIE: "Pie charts for distributions (e.g., asset allocation, portfolio breakdown)",
    ChartType.SCATTER: "Scatter plots for correlations (e.g., risk vs return)",
    ChartType.HISTOGRAM: "Histograms for frequency distributions (e.g., return distributions)",
}
