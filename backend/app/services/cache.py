import time
from typing import Any, Hashable

from app.config import get_settings


class TTLCache:
    def __init__(self, ttl_seconds: int | None = None) -> None:
        self._ttl = ttl_seconds
        self._items: dict[Hashable, tuple[float, Any]] = {}

    def _ttl_seconds(self) -> int:
        return self._ttl if self._ttl is not None else get_settings().cache_ttl_seconds

    def get(self, key: Hashable) -> Any | None:
        entry = self._items.get(key)
        if entry is None:
            return None
        stored_at, value = entry
        if time.monotonic() - stored_at > self._ttl_seconds():
            del self._items[key]
            return None
        return value

    def set(self, key: Hashable, value: Any) -> None:
        self._items[key] = (time.monotonic(), value)
