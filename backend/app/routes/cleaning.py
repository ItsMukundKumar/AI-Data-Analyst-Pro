from fastapi import APIRouter, HTTPException

from app.utils.session_manager import get_session
from app.services.data_cleaner import clean_dataset


router = APIRouter(
    prefix="/api",
    tags=["Data Cleaning"]
)


@router.post("/clean/{session_id}")
def clean_uploaded_dataset(
    session_id: str,
    drop_rows_with_missing: bool = True
):

    # 1. Retrieve session
    session = get_session(session_id)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found or expired."
        )

    # 2. Retrieve original DataFrame
    original_df = session["dataframe"]

    # 3. Clean dataset
    cleaned_df, report = clean_dataset(
        original_df,
        drop_rows_with_missing=drop_rows_with_missing
    )

    # 4. Update session with cleaned DataFrame
    session["dataframe"] = cleaned_df

    # 5. Save cleaning report
    session["cleaning_report"] = report

    # 6. Return response
    return {
        "success": True,
        "message": "Dataset cleaned successfully.",
        "session_id": session_id,
        "cleaning_report": report
    }