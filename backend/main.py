from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import upload, cleaning, metadata, charts, visualization, analytics


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("AI Data Analyst API starting...")
    yield
    print("AI Data Analyst API shutting down...")


app = FastAPI(
    title="AI Data Analyst Pro",
    description=(
        "An AI-powered data analysis platform "
        "for automated data cleaning, visualization, "
        "and intelligent insights."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

app.include_router(upload.router)
app.include_router(cleaning.router)
app.include_router(metadata.router)
app.include_router(charts.router)
app.include_router(visualization.router)
app.include_router(analytics.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    return {
        "success": True,
        "message": "Welcome to AI Data Analyst V2 API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "application": "AI Data Analyst V2",
        "version": "2.0.0",
    }


@app.get("/api/v1/status", tags=["System"])
async def api_status():
    return {
        "success": True,
        "message": "API is running",
        "services": {
            "backend": "online",
            "database": "not_configured",
            "ai_engine": "not_configured",
            "data_engine": "ready",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
