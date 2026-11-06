import uuid
import time

import pandas as pd

from app.config import settings


# Temporary in-memory session storage
sessions = {}


def create_session(df: pd.DataFrame, filename: str):

    session_id = str(uuid.uuid4())

    sessions[session_id] = {
        "dataframe": df,
        "filename": filename,
        "created_at": time.time(),
        "last_accessed": time.time()
    }

    return session_id


def get_session(session_id: str):

    session = sessions.get(session_id)

    if session is None:
        return None

    current_time = time.time()

    ttl = settings.SESSION_TTL_MINUTES * 60

    if current_time - session["last_accessed"] > ttl:

        del sessions[session_id]

        return None

    session["last_accessed"] = current_time

    return session


def delete_session(session_id: str):

    return sessions.pop(session_id, None) is not None


def cleanup_expired_sessions():

    current_time = time.time()

    ttl = settings.SESSION_TTL_MINUTES * 60

    expired_sessions = []

    for session_id, session in sessions.items():

        if current_time - session["last_accessed"] > ttl:
            expired_sessions.append(session_id)

    for session_id in expired_sessions:
        del sessions[session_id]

    return len(expired_sessions)