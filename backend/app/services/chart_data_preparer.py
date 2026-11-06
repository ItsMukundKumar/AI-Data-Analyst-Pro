import pandas as pd


def prepare_chart_data(df: pd.DataFrame, chart: dict) -> pd.DataFrame:
    chart_type = chart["chart_type"]
    x_column = chart["x_column"]
    y_column = chart.get("y_column")
    aggregation = chart.get("aggregation") or "none"

    if x_column not in df.columns:
        raise ValueError(f"Column not found: {x_column}")

    if y_column is not None and y_column not in df.columns:
        raise ValueError(f"Column not found: {y_column}")

    working_df = df.copy()

    # Histogram: use the distribution of one numerical column.
    if chart_type == "histogram":
        if not pd.api.types.is_numeric_dtype(working_df[x_column]):
            raise ValueError("Histogram requires a numerical column.")

        return working_df[[x_column]].dropna()

    # Scatter: use pairs of numerical values.
    if chart_type == "scatter":
        if y_column is None:
            raise ValueError("Scatter chart requires a Y column.")

        return working_df[[x_column, y_column]].dropna().head(5000)

    # Box plot: compare numerical distributions.
    if chart_type == "box":
        if y_column is None:
            raise ValueError("Box chart requires a numerical Y column.")

        return working_df[[x_column, y_column]].dropna()

    # Count records by category when Y is not supplied.
    if y_column is None:
        if aggregation != "count":
            raise ValueError("A chart without a Y column must use count aggregation.")

        result = (
            working_df.groupby(x_column, dropna=False).size().reset_index(name="value")
        )

    else:
        if aggregation == "none":
            result = working_df[[x_column, y_column]].dropna()

        else:
            if not pd.api.types.is_numeric_dtype(working_df[y_column]):
                raise ValueError("Y column must be numerical.")

            operations = {
                "sum": "sum",
                "mean": "mean",
                "median": "median",
                "min": "min",
                "max": "max",
                "count": "count",
            }

            if aggregation not in operations:
                raise ValueError("Unsupported aggregation.")

            result = (
                working_df.groupby(x_column, dropna=False)[y_column]
                .agg(operations[aggregation])
                .reset_index(name="value")
            )

    # Limit category-based charts to the 20 largest groups.
    if chart_type in ["bar", "pie"] and "value" in result.columns and len(result) > 20:
        result = result.nlargest(20, "value")

    # Sort line charts by their X-axis.
    if chart_type == "line":
        result = result.sort_values(by=x_column)

    return result
