import json

from groq import Groq
from pydantic import ValidationError

from app.config import settings
from app.schemas.chart_schema import ChartPlan


def validate_chart_columns(chart_plan: ChartPlan, metadata: dict):
    columns = metadata["columns"]

    for chart in chart_plan.charts:
        if chart.x_column not in columns:
            raise ValueError(f"Unknown X-axis column: {chart.x_column}")

        if chart.y_column is not None and chart.y_column not in columns:
            raise ValueError(f"Unknown Y-axis column: {chart.y_column}")

        x_type = columns[chart.x_column]["column_type"]

        y_type = (
            columns[chart.y_column]["column_type"]
            if chart.y_column is not None
            else None
        )

        if chart.chart_type == "histogram":
            if x_type != "numerical":
                raise ValueError("Histogram requires a numerical X-axis column.")
            if chart.y_column is not None:
                raise ValueError("Histogram must not have a Y-axis column.")

        elif chart.chart_type == "scatter":
            if x_type != "numerical" or y_type != "numerical":
                raise ValueError("Scatter charts require numerical X and Y columns.")

        elif chart.chart_type == "line":
            if x_type not in ["numerical", "datetime"]:
                raise ValueError("Line chart requires a numerical or datetime X-axis.")
            if y_type != "numerical":
                raise ValueError("Line chart requires a numerical Y-axis.")

        elif chart.chart_type == "box":
            if y_type != "numerical":
                raise ValueError("Box chart requires a numerical Y-axis.")

        elif chart.chart_type == "pie":

            if x_type not in ["categorical", "boolean"]:
                raise ValueError(
                    f"Invalid pie chart: '{chart.x_column}' "
                    f"is {x_type}, not categorical."
                )

            if chart.y_column is not None and y_type != "numerical":
                raise ValueError("Pie chart Y-axis must be numerical.")

        elif chart.chart_type == "bar":
            if x_type not in ["categorical", "boolean", "datetime", "numerical"]:
                raise ValueError("Unsupported X-axis type for bar chart.")

            if chart.y_column is not None and y_type != "numerical":
                raise ValueError("Bar chart Y-axis must be numerical when provided.")

        if chart.chart_type in ["bar", "pie"] and chart.y_column is None:
            if chart.aggregation != "count":
                raise ValueError(
                    "Bar and pie charts without a Y-axis must use count aggregation."
                )


def generate_chart_config(metadata: dict) -> dict:
    if not settings.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is missing.")

    if not settings.GROQ_MODEL:
        raise RuntimeError("GROQ_MODEL is missing.")

    client = Groq(api_key=settings.GROQ_API_KEY)

    prompt = f"""
You are an expert data analyst.

Analyze the dataset metadata below and recommend useful charts.

DATASET METADATA:
{json.dumps(metadata, default=str)}

Return ONLY valid JSON using this exact structure:

{{
    "charts": [
    {{
        "chart_type": "bar",
        "title": "Chart title",
        "description": "What this chart helps explain",
        "x_column": "column_name",
        "y_column": "numeric_column_or_null",
        "aggregation": "mean"
    }}
    ]
}}

RULES:
1. Generate between 6 and 15 useful charts.
2. Use only columns that exist in the metadata.
3. Supported chart types: bar, line, pie, scatter, histogram, box.
4. Histogram: numerical X column, null Y column.
5. Scatter: numerical X and numerical Y.
6. Line: numerical or datetime X and numerical Y.
7. Box: numerical Y; X may be a categorical grouping column or a numerical column.
8. Pie: categorical or boolean X. Use count if Y is null.
9. Bar: use a categorical, boolean, datetime or numerical X.
10. If Y is null for a bar chart, use count aggregation.
11. For numerical Y, choose a suitable aggregation:
    sum, mean, median, min, max, or none.
12. Do not invent columns or statistics.
13. Avoid redundant charts.
14. Prioritize charts that reveal useful patterns and comparisons.
15. Do not include Markdown fences or explanatory text outside the JSON.
16. The aggregation field must NEVER be null.
17. Always use "none" when no aggregation is required.
18. Use "count" when counting records or categories.
19. Use "sum", "mean", "median", "min", or "max"
    when aggregating numerical values.
20. Pie charts MUST use categorical or boolean columns for x_column.
21. NEVER use numerical or datetime columns for pie charts.
22. If no suitable categorical column exists, do not generate a pie chart.
23. Use bar charts or histograms for numerical distributions.
24. Avoid generating pie charts when there are too many unique categories.
"""

    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You generate data visualization configurations. "
                    "Return valid JSON only."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    response_text = response.choices[0].message.content

    if not response_text:
        raise ValueError("The AI returned an empty response.")

    response_data = json.loads(response_text)

    chart_plan = ChartPlan.model_validate(response_data)

    validate_chart_columns(chart_plan, metadata)

    return chart_plan.model_dump()
