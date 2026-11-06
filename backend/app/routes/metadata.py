
from fastapi import APIRouter, HTTPException

from app.utils.session_manager import get_session
from app.services.metadata_extractor import extract_metadata

router = APIRouter(
    prefix="/api",
    tags=["Dataset Metadata"]
)


@router.get("/metadata/{session_id}")
def get_dataset_metadata(session_id: str):

    session = get_session(session_id)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found or expired."
        )

    df = session["dataframe"]

    metadata = extract_metadata(df)

    session["metadata"] = metadata

    return {
        "success": True,
        "message": "Dataset metadata extracted successfully.",
        "session_id": session_id,
        "metadata": metadata
    }
