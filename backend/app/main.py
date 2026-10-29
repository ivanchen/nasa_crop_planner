from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import appeears, chat, location

settings = get_settings()

app = FastAPI(title="Crop Rotation Decision-Support API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(location.router, prefix="/api")
app.include_router(appeears.router, prefix="/api")
app.include_router(chat.router, prefix="/api")


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "earthdata_configured": settings.earthdata_configured,
        "llm_enabled": bool(settings.google_ai_studio_api_key),
    }
