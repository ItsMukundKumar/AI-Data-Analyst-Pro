from fastapi import APIRouter, UploadFile, File, HTTPException

from app.utils.file_validation import validate_file
from app.services.data_loader import load_dataset
from app.utils.session_manager import create_session, cleanup_expired_sessions
from app.utils.session_manager import get_session, delete_session

router = APIRouter(
    prefix="/api",
    tags=["Dataset Upload"]
)


@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):

    # Remove expired sessions
    cleanup_expired_sessions()

    # Validate and read uploaded file
    content = await validate_file(file)

    # Load dataset using Pandas
    df = load_dataset(file.filename, content)

    # Create temporary session
    session_id = create_session(
        df=df,
        filename=file.filename
    )

    return {
        "success": True,
        "message": "Dataset uploaded successfully.",
        "session_id": session_id,
        "filename": file.filename,
        "file_size_bytes": len(content),
        "dataset": {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "column_names": df.columns.tolist()
        }
    }
    
@router.get("/session/{session_id}")
def get_dataset_session(session_id: str):

    session = get_session(session_id)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found or expired."
        )

    df = session["dataframe"]

    return {
        "success": True,
        "session_id": session_id,
        "filename": session["filename"],
        "total_rows": len(df),
        "total_columns": len(df.columns)
    }


@router.delete("/session/{session_id}")
def remove_dataset_session(session_id: str):

    deleted = delete_session(session_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Session not found."
        )

    return {
        "success": True,
        "message": "Dataset session deleted successfully."
    }