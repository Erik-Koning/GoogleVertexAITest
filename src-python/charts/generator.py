"""Generate charts using Matplotlib and return as base64 PNG."""

import base64
import io
from typing import Literal

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

# Use non-interactive backend for server environments
matplotlib.use("Agg")


def generate_chart(
    data: dict[str, float],
    title: str,
    chart_type: Literal["bar", "line", "pie", "scatter", "histogram"],
) -> str:
    """
    Generate a chart and return as base64-encoded PNG.

    Args:
        data: Dictionary of label -> value pairs
        title: Chart title
        chart_type: Type of chart to generate

    Returns:
        Base64-encoded PNG string with data URI prefix
    """
    # Create figure with appropriate size
    fig, ax = plt.subplots(figsize=(10, 6))

    labels = list(data.keys())
    values = list(data.values())

    if chart_type == "bar":
        _create_bar_chart(ax, labels, values)
    elif chart_type == "line":
        _create_line_chart(ax, labels, values)
    elif chart_type == "pie":
        _create_pie_chart(ax, labels, values)
    elif chart_type == "scatter":
        _create_scatter_chart(ax, labels, values)
    elif chart_type == "histogram":
        _create_histogram(ax, values)
    else:
        # Default to bar
        _create_bar_chart(ax, labels, values)

    ax.set_title(title, fontsize=14, fontweight="bold", pad=20)

    # Adjust layout
    plt.tight_layout()

    # Convert to base64
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
    buffer.seek(0)
    plt.close(fig)

    image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{image_base64}"


def _create_bar_chart(ax: plt.Axes, labels: list[str], values: list[float]) -> None:
    """Create a bar chart."""
    colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(labels)))
    bars = ax.bar(labels, values, color=colors, edgecolor="black", linewidth=0.5)

    # Add value labels on bars
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax.annotate(
            f"{value:.2f}" if isinstance(value, float) else str(value),
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    ax.set_ylabel("Value")
    ax.tick_params(axis="x", rotation=45)


def _create_line_chart(ax: plt.Axes, labels: list[str], values: list[float]) -> None:
    """Create a line chart."""
    ax.plot(labels, values, marker="o", linewidth=2, markersize=8, color="#2E86AB")
    ax.fill_between(labels, values, alpha=0.3, color="#2E86AB")

    # Add value labels at points
    for i, (label, value) in enumerate(zip(labels, values)):
        ax.annotate(
            f"{value:.2f}" if isinstance(value, float) else str(value),
            xy=(i, value),
            xytext=(0, 10),
            textcoords="offset points",
            ha="center",
            fontsize=9,
        )

    ax.set_ylabel("Value")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(True, linestyle="--", alpha=0.7)


def _create_pie_chart(ax: plt.Axes, labels: list[str], values: list[float]) -> None:
    """Create a pie chart."""
    colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))

    # Explode the largest slice slightly
    explode = [0.05 if v == max(values) else 0 for v in values]

    wedges, texts, autotexts = ax.pie(
        values,
        labels=labels,
        autopct="%1.1f%%",
        colors=colors,
        explode=explode,
        startangle=90,
        pctdistance=0.75,
    )

    # Style the percentage text
    for autotext in autotexts:
        autotext.set_fontsize(9)
        autotext.set_fontweight("bold")

    ax.axis("equal")


def _create_scatter_chart(ax: plt.Axes, labels: list[str], values: list[float]) -> None:
    """Create a scatter chart."""
    # For scatter, we need x and y values
    # If we only have one dimension, use index as x
    x = list(range(len(values)))

    scatter = ax.scatter(x, values, c=values, cmap="viridis", s=100, edgecolors="black")
    plt.colorbar(scatter, ax=ax, label="Value")

    # Add labels
    for i, (label, value) in enumerate(zip(labels, values)):
        ax.annotate(
            label,
            xy=(i, value),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8,
        )

    ax.set_xlabel("Index")
    ax.set_ylabel("Value")
    ax.grid(True, linestyle="--", alpha=0.7)


def _create_histogram(ax: plt.Axes, values: list[float]) -> None:
    """Create a histogram."""
    ax.hist(values, bins="auto", color="#2E86AB", edgecolor="black", alpha=0.7)
    ax.set_xlabel("Value")
    ax.set_ylabel("Frequency")
    ax.grid(True, linestyle="--", alpha=0.7, axis="y")
