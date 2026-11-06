import pandas as pd
import re


def clean_column_names(df: pd.DataFrame):

    cleaned_columns = []
    used_names = set()

    for column in df.columns:

        # Convert column name to string
        name = str(column)

        # Remove leading and trailing spaces
        name = name.strip()

        # Convert to lowercase
        name = name.lower()

        # Replace spaces and special characters with underscores
        name = re.sub(r"[^a-zA-Z0-9]+", "_", name)

        # Remove underscores from beginning and end
        name = name.strip("_")

        # Handle empty column names
        if not name:
            name = "column"

        # Prevent duplicate column names
        original_name = name
        counter = 1

        while name in used_names:
            name = f"{original_name}_{counter}"
            counter += 1

        used_names.add(name)
        cleaned_columns.append(name)

    df.columns = cleaned_columns

    return df


def clean_dataset(
    df: pd.DataFrame,
    drop_rows_with_missing: bool = True
):

    # Work on a copy so the original DataFrame is not
    # modified if cleaning fails.
    cleaned_df = df.copy()

    # Initial statistics
    original_rows = len(cleaned_df)
    original_columns = len(cleaned_df.columns)

    missing_before = (
        cleaned_df.isnull()
        .sum()
        .to_dict()
    )

    missing_total_before = int(
        cleaned_df.isnull().sum().sum()
    )

    # 1. Remove duplicate rows
    duplicate_count = int(
        cleaned_df.duplicated().sum()
    )

    cleaned_df = cleaned_df.drop_duplicates()

    # 2. Remove completely empty columns
    empty_columns = cleaned_df.columns[
        cleaned_df.isnull().all()
    ].tolist()

    cleaned_df = cleaned_df.dropna(
        axis=1,
        how="all"
    )

    # 3. Remove rows containing missing values
    if drop_rows_with_missing:

        rows_before_missing_removal = len(cleaned_df)

        cleaned_df = cleaned_df.dropna(
            axis=0,
            how="any"
        )

        missing_rows_removed = (
            rows_before_missing_removal - len(cleaned_df)
        )

    else:
        missing_rows_removed = 0

    # 4. Handle dataset with no remaining columns
    if len(cleaned_df.columns) == 0:
        cleaned_df = cleaned_df.iloc[0:0].copy()

    # 5. Standardize column names
    cleaned_df = clean_column_names(cleaned_df)

    # Final statistics
    final_rows = len(cleaned_df)
    final_columns = len(cleaned_df.columns)

    missing_after = (
        cleaned_df.isnull()
        .sum()
        .to_dict()
    )

    missing_total_after = int(
        cleaned_df.isnull().sum().sum()
    )

    rows_removed = original_rows - final_rows
    columns_removed = original_columns - final_columns

    cleaning_report = {

        "original": {
            "total_rows": original_rows,
            "total_columns": original_columns,
            "missing_values": missing_total_before
        },

        "cleaning_operations": {
            "duplicate_rows_removed": duplicate_count,
            "missing_rows_removed": missing_rows_removed,
            "empty_columns_removed": empty_columns,
            "columns_standardized": True
        },

        "cleaned": {
            "total_rows": final_rows,
            "total_columns": final_columns,
            "missing_values": missing_total_after
        },

        "summary": {
            "total_rows_removed": rows_removed,
            "total_columns_removed": columns_removed,
            "total_missing_values_before": missing_total_before,
            "total_missing_values_after": missing_total_after
        }

    }

    return cleaned_df, cleaning_report