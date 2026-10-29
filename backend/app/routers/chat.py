from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.models.schemas import CreateSessionRequest, MessageResponse, SendMessageRequest, SessionResponse
from app.services import chat_flow, chat_sessions
from app.services.chat_agent import llm_enabled

router = APIRouter(prefix="/chat")


@router.post("/session", response_model=SessionResponse)
async def create_session(body: CreateSessionRequest) -> SessionResponse:
    session = chat_flow.start_session(body.lang)
    return SessionResponse(
        session_id=session.id,
        lang=session.lang,
        step=session.step,
        messages=session.messages,
        llm_enabled=llm_enabled(),
    )


@router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str) -> SessionResponse:
    session = chat_sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    return SessionResponse(
        session_id=session.id,
        lang=session.lang,
        step=session.step,
        messages=session.messages,
        llm_enabled=llm_enabled(),
    )


@router.post("/session/{session_id}/message", response_model=MessageResponse)
async def send_message(session_id: str, body: SendMessageRequest) -> MessageResponse:
    session = chat_sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    before = len(session.messages)
    await chat_flow.handle_message(
        session,
        text=body.text,
        action_id=body.action_id,
        gps_location=body.location,
    )
    new_messages = session.messages[before:]
    return MessageResponse(messages=new_messages, step=session.step, processing=session.analyzing)


@router.patch("/session/{session_id}/lang")
async def set_language(session_id: str, lang: str) -> SessionResponse:
    session = chat_sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    if lang not in ("id", "en"):
        raise HTTPException(status_code=400, detail="lang must be 'id' or 'en'")
    session.lang = lang  # type: ignore[assignment]
    return SessionResponse(
        session_id=session.id,
        lang=session.lang,
        step=session.step,
        messages=session.messages,
        llm_enabled=llm_enabled(),
    )
