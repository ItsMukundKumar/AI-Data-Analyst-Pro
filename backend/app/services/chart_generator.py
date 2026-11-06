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


STRICT CHART GENERATION RULES:

1. Generate between 6 and 15 charts ONLY when the dataset contains enough valid columns and meaningful analytical opportunities. Never create meaningless charts just to reach the minimum.

2. Use ONLY columns explicitly listed in the provided metadata. Column names must match exactly, including spelling, capitalization, spaces, and special characters.

3. NEVER invent, rename, assume, or reference columns that do not exist in the metadata.

4. Supported chart types are strictly limited to:
   bar, line, pie, scatter, histogram, box.

5. COLUMN TYPE VALIDATION:
   - Numerical columns: only columns identified as numerical in metadata.
   - Categorical columns: only columns identified as categorical in metadata.
   - Boolean columns: only columns identified as boolean in metadata.
   - Datetime columns: only columns identified as datetime in metadata.
   - Never infer a column's type from its name.

6. HISTOGRAM RULES:
   - x_column MUST be numerical.
   - y_column MUST be null.
   - aggregation MUST be "none".
   - Use histograms to understand numerical distributions.
   - Do not use categorical, boolean, or datetime columns.

7. SCATTER RULES:
   - x_column MUST be numerical.
   - y_column MUST be numerical.
   - x_column and y_column MUST be different columns.
   - aggregation MUST be "none".
   - Use scatter charts to identify relationships, correlations, clusters, and outliers.
   - Never use categorical, boolean, or datetime columns.

8. LINE CHART RULES:
   - x_column MUST be numerical or datetime.
   - y_column MUST be numerical.
   - x_column and y_column MUST be different columns.
   - aggregation MUST be "none" unless the chart explicitly requires grouping or aggregation.
   - Use line charts only when the X-axis has a meaningful order or progression.
   - Sort datetime and numerical X values in ascending order.
   - Never use line charts for unordered categories.

9. BOX CHART RULES:
   - y_column MUST be numerical.
   - x_column MUST be a categorical, boolean, or numerical column.
   - x_column and y_column MUST be different columns.
   - aggregation MUST be "none".
   - Use a grouping column only when it produces meaningful comparisons.
   - Avoid grouping columns with excessive unique values.
   - Do not use datetime columns as grouping columns unless explicitly supported by the application.

10. PIE CHART RULES:
    - x_column MUST be categorical or boolean.
    - y_column MAY be null or numerical.
    - NEVER use numerical or datetime columns as x_column.
    - If y_column is null, aggregation MUST be "count".
    - If y_column is numerical, aggregation MUST be one of:
      sum, mean, median, min, max.
    - Categories must represent meaningful proportions of a whole.
    - Avoid pie charts when the number of unique categories exceeds 8.
    - Prefer bar charts when categories are numerous or difficult to compare.
    - Never generate a pie chart if no suitable categorical or boolean column exists.

11. BAR CHART RULES:
    - x_column MUST be categorical, boolean, datetime, or numerical.
    - y_column MAY be null or numerical.
    - If y_column is null, aggregation MUST be "count".
    - If y_column is numerical, aggregation MUST be one of:
      sum, mean, median, min, max.
    - Use "sum" for additive metrics.
    - Use "mean" for average comparisons.
    - Use "median" when the distribution may contain outliers.
    - Use "min" or "max" only when extreme values are analytically meaningful.
    - Use numerical X columns only when comparing meaningful numerical groups or ranges.
    - Avoid bar charts with excessive unique X values.
    - Never aggregate categorical or boolean Y columns.

12. AGGREGATION RULES:
    - The aggregation field MUST NEVER be null or omitted.
    - Allowed aggregation values are strictly:
      none, count, sum, mean, median, min, max.
    - Use "none" when no aggregation is required.
    - Use "count" when counting records or categories.
    - Use sum, mean, median, min, or max only when Y is numerical.
    - Histogram, scatter, line, and box charts MUST use "none".
    - Pie and bar charts MUST use "count" when Y is null.
    - Never use "count" when Y is a numerical column.
    - Never use "none" for bar or pie charts when aggregation is required.
    - Aggregation must always be logically consistent with chart type and Y column.

13. CHART QUALITY RULES:
    - Every chart MUST answer a meaningful analytical question.
    - Prioritize business insights, trends, comparisons, distributions, and relationships.
    - Avoid charts that merely repeat the same information.
    - Do not create multiple charts using identical X/Y combinations and different aggregation methods unless they reveal genuinely different insights.
    - Avoid meaningless charts using ID columns, unique identifiers, constant columns, or columns with excessive missing values.
    - Do not treat identifiers as meaningful numerical measures.
    - Avoid charts where almost every category has a unique value.
    - Prefer the most informative charts over the largest number of charts.

14. DATA VALIDITY RULES:
    - Never reference statistics that are not present in the metadata.
    - Never assume missing values are zero.
    - Never invent calculated columns.
    - Never assume that a numerical column represents revenue, profit, quantity, or any other business metric without supporting metadata.
    - Do not generate charts when the required columns are missing or incompatible.
    - Do not generate charts with identical X and Y columns.
    - If a chart cannot satisfy every rule, do not generate that chart.

15. CHART SELECTION PRIORITY:
    - First: meaningful datetime trends.
    - Second: important numerical comparisons across categories.
    - Third: numerical relationships using scatter charts.
    - Fourth: numerical distributions using histograms.
    - Fifth: numerical distributions and group comparisons using box charts.
    - Sixth: meaningful categorical proportions using pie charts.
    - Seventh: other useful comparisons using bar charts.
    - This is a priority guideline, not permission to create invalid charts.

16. FINAL VALIDATION BEFORE OUTPUT:
    Before returning JSON, validate EVERY chart independently.
    Check chart_type, x_column, y_column, column types, aggregation, and analytical usefulness.
    Remove every invalid, duplicate, redundant, or misleading chart.
    Never sacrifice data correctness to satisfy the requested chart count.

17. OUTPUT RULES:
    - Return valid JSON only.
    - Do not include Markdown code fences.
    - Do not include explanations, comments, or text outside JSON.
    - Follow the exact JSON schema provided.
    - Every chart must contain all required fields.
    - aggregation MUST always be present and MUST never be null.
    - Use null only for y_column when permitted by the chart type.
    - Never return unsupported chart types or aggregation values.

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
