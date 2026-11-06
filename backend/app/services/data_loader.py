from io import BytesIO
from pathlib import Path

import pandas as pd
from fastapi import HTTPException


def load_dataset(filename: str, content: bytes) -> pd.DataFrame:
    extension = Path(filename).suffix.lower()
    try:
        file_buffer = BytesIO(content)
        if extension == ".csv":
            try:
                df = pd.read_csv(file_buffer, encoding="utf-8-sig")
            except UnicodeDecodeError:
                file_buffer.seek(0)
                df = pd.read_csv(file_buffer, encoding="latin-1")
        elif extension in [".xlsx", ".xls"]:
            df = pd.read_excel(file_buffer)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format.")
        if df.empty and len(df.columns) == 0:
            raise HTTPException(status_code=400, detail="Dataset contains no columns.")
        return df
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=422,
            detail="Unable to read dataset. Check whether the file is valid.",
        )
