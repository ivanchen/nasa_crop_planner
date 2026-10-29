import json

import httpx

from app.config import get_settings
from app.i18n.messages import t
from app.services.chat_sessions import ChatSession
from app.services.jobs import get_job

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

SYSTEM_PROMPT = """You are TaniPilot, a friendly crop rotation advisor for Indonesian farmers.
Rules:
- Answer in simple {lang_name}. Use local crop names when lang is Indonesian.
- NEVER invent numbers. Only cite data from the provided context.
- Always mention data source and when it was fetched if citing numbers.
- Keep answers under 120 words.
- If you don't have data, say so and suggest starting a new analysis.
"""


def llm_enabled() -> bool:
    return bool(get_settings().google_ai_studio_api_key)


async def reply_freeform(session: ChatSession, text: str) -> str:
    if not llm_enabled():
        return t(session.lang, "llm_disabled")

    job = get_job(session.job_id) if session.job_id else None
    context = {}
    if job:
        context = {
            "location": job.location.model_dump(),
            "climate": job.climate.model_dump(mode="json"),
            "soil": job.soil.model_dump(mode="json"),
            "vegetation": job.vegetation.model_dump(mode="json") if job.vegetation else None,
            "moisture": job.moisture.model_dump(mode="json") if job.moisture else None,
            "recommendations": [r.model_dump() for r in job.recommendations[:3]],
            "last_crop": session.last_crop,
        }

    lang_name = "Bahasa Indonesia" if session.lang == "id" else "English"
    user_content = f"Context:\n{json.dumps(context, default=str)}\n\nFarmer question: {text}"

    settings = get_settings()
    url = GEMINI_URL.format(model=settings.google_ai_studio_model)
    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT.format(lang_name=lang_name)}]},
        "contents": [{"role": "user", "parts": [{"text": user_content}]}],
        "generationConfig": {"maxOutputTokens": 512, "temperature": 0.4},
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                url,
                params={"key": settings.google_ai_studio_api_key},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            parts = data["candidates"][0]["content"]["parts"]
            return "".join(p.get("text", "") for p in parts).strip()
    except (httpx.HTTPError, KeyError, IndexError):
        return t(session.lang, "llm_disabled")
