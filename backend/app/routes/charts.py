
from fastapi import APIRouter, HTTPException
from groq import GroqError
from pydantic import ValidationError

from app.utils.session_manager import get_session
from app.services.metadata_extractor import extract_metadata
from app.services.chart_generator import generate_chart_config

router = APIRouter(
    prefix="/api",
    tags=["AI Chart Generation"]
)


@router.post("/generate-charts/{session_id}")
def generate_charts(session_id: str):

    session = get_session(session_id)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found or expired."
        )

    df = session["dataframe"]

    # Reuse Phase 4 metadata when available.
    metadata = session.get("metadata")

    if metadata is None:
        metadata = extract_metadata(df)
        session["metadata"] = metadata

    try:
        chart_config = generate_chart_config(metadata)

        session["chart_config"] = chart_config

        return {
            "success": True,
            "message": "AI chart configurations generated successfully.",
            "session_id": session_id,
            "chart_config": chart_config
        }

    except (ValidationError, ValueError) as error:
        raise HTTPException(
            status_code=502,
            detail=f"Invalid chart configuration from AI: {str(error)}"
        )

    except GroqError:
        raise HTTPException(
            status_code=502,
            detail="Unable to generate chart configurations using the AI provider."
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error)
        )

    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Chart generation failed. Please try again."
        )
