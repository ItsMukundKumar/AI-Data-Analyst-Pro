
from io import BytesIO
import json

from PIL import Image
from google import genai

from app.config import settings


def analyze_dashboard(
    dashboard_image: bytes,
    metadata: dict
) -> str:

    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is missing.")

    if not settings.GEMINI_MODEL:
        raise RuntimeError("GEMINI_MODEL is missing.")

    client = genai.Client(
        api_key=settings.GEMINI_API_KEY
    )

    image = Image.open(
        BytesIO(dashboard_image)
    ).convert("RGB")

    prompt = f"""
You are an experienced professional data analyst.

Analyze the attached dashboard image and dataset metadata.

DATASET METADATA:
{json.dumps(metadata, default=str)}

Write a detailed analytical report with these sections:

1. Executive Summary
2. Important Findings
3. Trends and Patterns
4. Relationships Between Variables
5. Unusual Observations and Potential Outliers
6. Business Insights
7. Recommendations
8. Data Limitations

Instructions:
- Use the supplied metadata and chart image together.
- Explain important chart patterns in plain language.
- Include numerical values only when supported by the metadata.
- Do not invent facts or statistics.
- Clearly distinguish observations from possible explanations.
- Mention when the chart image does not provide enough information.
- Do not claim causation from correlation.
- Provide actionable recommendations where appropriate.
"""

    try:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=[
                prompt,
                image
            ]
        )

        if not response.text:
            raise ValueError("Gemini returned an empty analysis.")

        return response.text

    finally:
        image.close()
