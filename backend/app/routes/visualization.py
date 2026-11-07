import base64
import logging

from fastapi import APIRouter, HTTPException

from app.utils.session_manager import get_session
from app.services.chart_visualizer import generate_chart_image, generate_chart_figure
from app.services.dashboard_builder import create_dashboard_image

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Chart Visualization"])


@router.post("/visualize/{session_id}")
def visualize_dataset(session_id: str):

    session = get_session(session_id)

    if session is None:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    chart_config = session.get("chart_config")

    if not chart_config:
        raise HTTPException(
            status_code=400, detail="Generate chart configurations first."
        )

    df = session["dataframe"]

    try:
        chart_images = []
        chart_results = []

        for index, chart in enumerate(chart_config["charts"]):

            try:
                logger.info("Generating chart %s: %s", index + 1, chart.get("title"))

                # Static PNG: still needed for the dashboard image sent to Gemini.
                image_bytes = generate_chart_image(df, chart)

                chart_images.append(image_bytes)

                # Interactive Plotly figure for the frontend.
                # If it fails, only this chart falls back to the PNG.
                try:
                    figure = generate_chart_figure(df, chart)
                except Exception:
                    logger.exception(
                        "Plotly figure failed for chart %s: %s",
                        index + 1,
                        chart.get("title"),
                    )
                    figure = None

                chart_results.append(
                    {
                        "chart_id": index + 1,
                        "title": chart["title"],
                        "chart_type": chart["chart_type"],
                        "image": (
                            "data:image/png;base64,"
                            + base64.b64encode(image_bytes).decode("utf-8")
                        ),
                        "plotly": figure,
                    }
                )

            except Exception:
                logger.exception(
                    "Failed to generate chart %s: %s", index + 1, chart.get("title")
                )
                raise

        dashboard_image = create_dashboard_image(chart_images)

        session["dashboard_image"] = dashboard_image
        session["chart_images"] = chart_images

        return {
            "success": True,
            "message": "Charts generated successfully.",
            "session_id": session_id,
            "total_charts": len(chart_results),
            "charts": chart_results,
        }

    except Exception as error:

        logger.exception("Visualization failed")

        raise HTTPException(
            status_code=500, detail=f"Visualization failed: {str(error)}"
        )