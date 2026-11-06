
from io import BytesIO

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from app.services.chart_data_preparer import prepare_chart_data


# Modern dashboard theme
sns.set_theme(style="whitegrid")

COLORS = {
    "primary": "#6366F1",
    "secondary": "#06B6D4",
    "success": "#10B981",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "purple": "#8B5CF6",
    "pink": "#EC4899",
    "blue": "#3B82F6",
    "teal": "#14B8A6",
}

PALETTE = [
    "#6366F1",
    "#06B6D4",
    "#10B981",
    "#F59E0B",
    "#8B5CF6",
    "#EC4899",
    "#3B82F6",
    "#14B8A6",
    "#F97316",
    "#64748B",
]


def style_axis(ax):
    """Apply a clean dashboard style."""

    ax.set_facecolor("#FFFFFF")

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.spines["left"].set_color("#E5E7EB")
    ax.spines["bottom"].set_color("#E5E7EB")

    ax.tick_params(colors="#64748B", labelsize=9)

    ax.grid(
        axis="y",
        color="#E5E7EB",
        linestyle="--",
        linewidth=0.7,
        alpha=0.8
    )

    ax.set_axisbelow(True)


def generate_chart_image(df: pd.DataFrame, chart: dict) -> bytes:

    chart_type = chart["chart_type"]
    x_column = chart["x_column"]
    y_column = chart.get("y_column")

    chart_df = prepare_chart_data(df, chart)

    fig, ax = plt.subplots(figsize=(11, 5.5))

    fig.patch.set_facecolor("#FFFFFF")

    try:

        # BAR CHART
        if chart_type == "bar":

            value_column = (
                "value" if "value" in chart_df.columns
                else y_column
            )

            values = chart_df[value_column]

            bars = ax.bar(
                chart_df[x_column].astype(str),
                values,
                color=PALETTE[:len(chart_df)],
                width=0.65,
                edgecolor="white",
                linewidth=1.2
            )

            ax.bar_label(
                bars,
                padding=3,
                fontsize=8,
                color="#475569"
            )

            ax.set_ylabel(
                "Count" if y_column is None
                else chart.get("aggregation", "").capitalize()
                if "value" in chart_df.columns
                else y_column
            )

        # LINE CHART
        elif chart_type == "line":

            value_column = (
                "value" if "value" in chart_df.columns
                else y_column
            )

            ax.plot(
                chart_df[x_column],
                chart_df[value_column],
                color=COLORS["primary"],
                linewidth=2.8,
                marker="o",
                markersize=6,
                markerfacecolor="#FFFFFF",
                markeredgewidth=2,
                markeredgecolor=COLORS["primary"]
            )

            ax.fill_between(
                range(len(chart_df)),
                chart_df[value_column],
                alpha=0.10,
                color=COLORS["primary"]
            ) if pd.api.types.is_numeric_dtype(
                chart_df[value_column]
            ) else None

            ax.set_ylabel(value_column)

        # PIE CHART
        elif chart_type == "pie":

            value_column = (
                "value" if "value" in chart_df.columns
                else y_column
            )

            wedges, texts, autotexts = ax.pie(
                chart_df[value_column],
                labels=chart_df[x_column].astype(str),
                autopct="%1.1f%%",
                colors=PALETTE,
                startangle=90,
                pctdistance=0.75,
                wedgeprops={
                    "edgecolor": "white",
                    "linewidth": 2
                },
                textprops={
                    "fontsize": 9,
                    "color": "#334155"
                }
            )

            for text in autotexts:
                text.set_color("white")
                text.set_fontweight("bold")
                text.set_fontsize(9)

        # SCATTER CHART
        elif chart_type == "scatter":

            ax.scatter(
                chart_df[x_column],
                chart_df[y_column],
                color=COLORS["secondary"],
                s=65,
                alpha=0.75,
                edgecolors="white",
                linewidths=0.8
            )

            ax.set_ylabel(y_column)

        # HISTOGRAM
        elif chart_type == "histogram":

            ax.hist(
                chart_df[x_column].dropna(),
                bins=20,
                color=COLORS["purple"],
                edgecolor="white",
                linewidth=1.2,
                alpha=0.85
            )

            ax.set_ylabel("Frequency")

        # BOX PLOT
        elif chart_type == "box":

            if chart_df[x_column].nunique() <= 15:

                grouped = chart_df.groupby(x_column)

                groups = [
                    group[y_column].dropna().values
                    for _, group in grouped
                ]

                labels = [
                    str(name)
                    for name, _ in grouped
                ]

                box = ax.boxplot(
                    groups,
                    tick_labels=labels,
                    patch_artist=True,
                    medianprops={
                        "color": "#1E293B",
                        "linewidth": 2
                    },
                    whiskerprops={"color": "#64748B"},
                    capprops={"color": "#64748B"},
                    flierprops={
                        "marker": "o",
                        "markerfacecolor": COLORS["pink"],
                        "markersize": 4,
                        "alpha": 0.5
                    }
                )

                for i, patch in enumerate(box["boxes"]):
                    patch.set_facecolor(PALETTE[i % len(PALETTE)])
                    patch.set_alpha(0.75)

                ax.set_xlabel(x_column)

            else:

                box = ax.boxplot(
                    chart_df[y_column].dropna(),
                    patch_artist=True
                )

                box["boxes"][0].set_facecolor(COLORS["primary"])

            ax.set_ylabel(y_column)

        # COMMON STYLING
        style_axis(ax)

        ax.set_title(
            chart["title"],
            fontsize=15,
            fontweight="bold",
            color="#1E293B",
            pad=18
        )

        if chart_type != "pie":
            ax.set_xlabel(
                x_column,
                fontsize=10,
                color="#475569",
                labelpad=10
            )

        ax.tick_params(axis="x", rotation=35)

        fig.tight_layout(pad=2)

        image_buffer = BytesIO()

        fig.savefig(
            image_buffer,
            format="png",
            dpi=160,
            bbox_inches="tight",
            facecolor=fig.get_facecolor()
        )

        image_buffer.seek(0)

        return image_buffer.getvalue()

    finally:
        plt.close(fig)
