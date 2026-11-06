from fastapi import HTTPException, UploadFile
from app.config import settings


ALLOWED_EXTENSIONS = {
    ".csv",
    ".xlsx",
    ".xls"
}


async def validate_file(file: UploadFile) -> bytes:

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is missing."
        )

    filename = file.filename.strip()

    if "." not in filename:
        raise HTTPException(
            status_code=400,
            detail="File extension is missing."
        )

    extension = "." + filename.rsplit(".", 1)[-1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only CSV, XLSX and XLS files are supported."
        )

    max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024

    # Read one byte beyond the limit to detect oversized files.
    content = await file.read(max_size + 1)

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )

    if len(content) > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"Maximum file size is {settings.MAX_FILE_SIZE_MB} MB."
        )

    return content