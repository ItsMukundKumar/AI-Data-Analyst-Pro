from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class ChartConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chart_type: Literal["bar", "line", "pie", "scatter", "histogram", "box"]

    title: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=300)

    x_column: str
    y_column: str | None = None

    aggregation: (
        Literal["none", "count", "sum", "mean", "median", "min", "max"] | None
    ) = "none"


class ChartPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    charts: list[ChartConfig] = Field(min_length=4, max_length=15)