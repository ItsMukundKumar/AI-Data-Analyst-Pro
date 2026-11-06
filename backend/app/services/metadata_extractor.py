
import math
import pandas as pd
from pandas.api.types import (
    is_numeric_dtype,
    is_datetime64_any_dtype,
    is_bool_dtype,
)


def make_json_safe(value):
    """Convert Pandas and NumPy values into JSON-safe Python values."""
    if value is None or pd.isna(value):
        return None

    if hasattr(value, "item"):
        value = value.item()

    if isinstance(value, float) and not math.isfinite(value):
        return None

    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()

    return value


def extract_metadata(df: pd.DataFrame) -> dict:
    total_rows = len(df)
    total_columns = len(df.columns)

    numerical_columns = []
    categorical_columns = []
    datetime_columns = []
    boolean_columns = []
    other_columns = []

    column_details = {}

    for column in df.columns:
        series = df[column]
        column_name = str(column)
        dtype = str(series.dtype)

        if is_bool_dtype(series):
            boolean_columns.append(column_name)
            column_type = "boolean"

        elif is_numeric_dtype(series):
            numerical_columns.append(column_name)
            column_type = "numerical"

        elif is_datetime64_any_dtype(series):
            datetime_columns.append(column_name)
            column_type = "datetime"

        elif (
            isinstance(series.dtype, pd.CategoricalDtype)
            or pd.api.types.is_object_dtype(series.dtype)
            or pd.api.types.is_string_dtype(series.dtype)
        ):
            categorical_columns.append(column_name)
            column_type = "categorical"

        else:
            other_columns.append(column_name)
            column_type = "other"

        missing_count = int(series.isna().sum())
        missing_percentage = (
            round((missing_count / total_rows) * 100, 2)
            if total_rows > 0 else 0.0
        )

        details = {
            "data_type": dtype,
            "column_type": column_type,
            "missing_count": missing_count,
            "missing_percentage": missing_percentage,
            "unique_values": int(series.nunique(dropna=True)),
        }

        if column_type == "numerical":
            numeric_series = pd.to_numeric(series, errors="coerce")

            details["statistics"] = {
                "mean": make_json_safe(numeric_series.mean()),
                "median": make_json_safe(numeric_series.median()),
                "standard_deviation": make_json_safe(numeric_series.std()),
                "minimum": make_json_safe(numeric_series.min()),
                "maximum": make_json_safe(numeric_series.max()),
            }

        elif column_type == "categorical":
            top_values = series.mode(dropna=True)

            details["statistics"] = {
                "most_frequent_value": (
                    str(make_json_safe(top_values.iloc[0]))
                    if not top_values.empty else None
                ),
                "unique_values_count": int(series.nunique(dropna=True)),
            }

        elif column_type == "datetime":
            details["statistics"] = {
                "minimum_date": make_json_safe(series.min()),
                "maximum_date": make_json_safe(series.max()),
            }

        column_details[column_name] = details

    metadata = {
        "dataset_overview": {
            "total_rows": total_rows,
            "total_columns": total_columns,
            "duplicate_rows": int(df.duplicated().sum()),
            "total_missing_values": int(df.isna().sum().sum()),
        },
        "column_classification": {
            "numerical_columns": numerical_columns,
            "categorical_columns": categorical_columns,
            "datetime_columns": datetime_columns,
            "boolean_columns": boolean_columns,
            "other_columns": other_columns,
        },
        "columns": column_details,
    }

    return metadata
