import time
import uuid
from dataclasses import dataclass, field
from typing import Literal

from app.models.schemas import ChatMessage, Location, Priorities

Lang = Literal["id", "en"]
Step = Literal[
    "ask_location",
    "confirm_location",
    "ask_last_crop",
    "ask_priorities",
    "analyzing",
    "show_results",
    "free_chat",
]

RETENTION_SECONDS = 24 * 3600


@dataclass
class ChatSession:
    id: str
    lang: Lang
    step: Step = "ask_location"
    location: Location | None = None
    location_label: str = ""
    last_crop: str | None = None
    priorities: Priorities | None = None
    job_id: str | None = None
    messages: list[ChatMessage] = field(default_factory=list)
    created_at: float = field(default_factory=time.monotonic)
    analyzing: bool = False


_sessions: dict[str, ChatSession] = {}


def _purge() -> None:
    cutoff = time.monotonic() - RETENTION_SECONDS
    for sid in [s.id for s in _sessions.values() if s.created_at < cutoff]:
        del _sessions[sid]


def create(lang: Lang) -> ChatSession:
    _purge()
    session = ChatSession(id=uuid.uuid4().hex, lang=lang)
    _sessions[session.id] = session
    return session


def get(session_id: str) -> ChatSession | None:
    return _sessions.get(session_id)


def add_message(session: ChatSession, message: ChatMessage) -> None:
    session.messages.append(message)
