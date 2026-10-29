import httpx
import pytest
import respx

from app.config import get_settings
from app.services.chat_agent import llm_enabled, reply_freeform
from app.services.chat_sessions import ChatSession


@pytest.fixture
def gemini_key(monkeypatch):
    monkeypatch.setenv("GOOGLE_AI_STUDIO_API_KEY", "test-key")
    monkeypatch.setenv("GOOGLE_AI_STUDIO_MODEL", "gemini-2.5-flash")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_llm_enabled_with_gemini_key(gemini_key):
    assert llm_enabled() is True


async def test_gemini_reply(gemini_key):
    with respx.mock:
        respx.post("https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent").respond(
            json={"candidates": [{"content": {"parts": [{"text": "Rotasi kedelai bagus untuk tanah."}]}}]}
        )
        session = ChatSession(id="s1", lang="id", job_id=None)
        reply = await reply_freeform(session, "Kenapa kedelai?")
    assert "kedelai" in reply.lower()


async def test_gemini_error_returns_disabled_message(gemini_key):
    with respx.mock:
        respx.post(url__regex=r".*generateContent.*").respond(status_code=403)
        session = ChatSession(id="s1", lang="id")
        reply = await reply_freeform(session, "test")
    assert "belum aktif" in reply or "not enabled" in reply.lower()
