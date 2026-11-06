from fastapi import APIRouter, HTTPException
from google.genai.errors import APIError

from app.utils.session_manager import get_session
from app.services.ai_analyzer import analyze_dashboard
from app.services.metadata_extractor import extract_metadata

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["AI Analytics"])


@router.post("/analyze/{session_id}")
def analyze_dataset(session_id: str):

    session = get_session(session_id)

    if session is None:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    dashboard_image = session.get("dashboard_image")

    if not dashboard_image:
        raise HTTPException(
            status_code=400, detail="Generate the dashboard charts first."
        )

    metadata = session.get("metadata")

    if metadata is None:
        metadata = extract_metadata(session["dataframe"])
        session["metadata"] = metadata

    try:
        report = analyze_dashboard(dashboard_image=dashboard_image, metadata=metadata)

        session["analysis_report"] = report

        return {
            "success": True,
            "message": "AI analysis generated successfully.",
            "session_id": session_id,
            "analysis_report": report,
        }

    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error))
    except Exception as error:
        logger.exception("Gemini API error")
        raise HTTPException(status_code=502, detail=f"Gemini API error: {str(error)}")
    except (APIError, ValueError):
        raise HTTPException(
            status_code=502,
            detail="Gemini analysis failed. Check the API configuration and try again.",
        )

    except Exception:
        raise HTTPException(
            status_code=500, detail="An unexpected error occurred during AI analysis."
        )
