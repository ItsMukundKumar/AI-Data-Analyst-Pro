
from io import BytesIO
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from app.services.chart_data_preparer import prepare_chart_data


def generate_chart_image(df: pd.DataFrame, chart: dict) -> bytes:
    chart_type = chart["chart_type"]
    x_column = chart["x_column"]
    y_column = chart.get("y_column")

    chart_df = prepare_chart_data(df, chart)

    fig, ax = plt.subplots(figsize=(10, 5))

    try:
        if chart_type == "bar":
            if y_column is None:
                ax.bar(
                    chart_df[x_column].astype(str),
                    chart_df["value"]
                )
                ax.set_ylabel("Count")
            elif "value" in chart_df.columns:
                ax.bar(
                    chart_df[x_column].astype(str),
                    chart_df["value"]
                )
                ax.set_ylabel(chart["aggregation"].capitalize())
            else:
                ax.bar(
                    chart_df[x_column].astype(str),
                    chart_df[y_column]
                )
                ax.set_ylabel(y_column)

        elif chart_type == "line":
            value_column = (
                "value" if "value" in chart_df.columns else y_column
            )
            ax.plot(
                chart_df[x_column],
                chart_df[value_column],
                marker="o"
            )
            ax.set_ylabel(value_column)

        elif chart_type == "pie":
            value_column = (
                "value" if "value" in chart_df.columns else y_column
            )

            ax.pie(
                chart_df[value_column],
                labels=chart_df[x_column].astype(str),
                autopct="%1.1f%%"
            )

        elif chart_type == "scatter":
            ax.scatter(
                chart_df[x_column],
                chart_df[y_column]
            )
            ax.set_ylabel(y_column)

        elif chart_type == "histogram":
            ax.hist(
                chart_df[x_column],
                bins=20
            )
            ax.set_ylabel("Frequency")

        elif chart_type == "box":
            if chart_df[x_column].nunique() <= 15:
                groups = [
                    group[y_column].dropna().values
                    for _, group in chart_df.groupby(x_column)
                ]
                labels = [
                    str(name)
                    for name, _ in chart_df.groupby(x_column)
                ]

                ax.boxplot(groups, tick_labels=labels)
                ax.set_xlabel(x_column)
            else:
                ax.boxplot(chart_df[y_column].dropna())

            ax.set_ylabel(y_column)

        ax.set_title(chart["title"])
        ax.set_xlabel(x_column)
        ax.tick_params(axis="x", rotation=35)

        fig.tight_layout()

        image_buffer = BytesIO()

        fig.savefig(
            image_buffer,
            format="png",
            dpi=120,
            bbox_inches="tight"
        )

        image_buffer.seek(0)

        return image_buffer.getvalue()

    finally:
        plt.close(fig)
