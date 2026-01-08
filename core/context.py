from contextvars import ContextVar
import threading
from typing import Any
from access_control.strategies.WhitelistStrategy import WhitelistStrategy


class ThreadVar:
    def __init__(self, name: str, default=None) -> None:
        self.name: str = name
        self._state: Any = default
        self._lock: threading.Lock = threading.Lock()
    
    def set(self, value) -> None:
        with self._lock:
            self._state = value
    
    def get(self) -> Any:
        with self._lock:
            return self._state


_current_user = ThreadVar("els_current_user", default=None)
_current_session = ThreadVar("els_current_session", default=None)
_current_base = ThreadVar("els_current_base", default=None)
_current_strategy = ThreadVar("els_current_strategy", default=WhitelistStrategy())
_filters_activated = ThreadVar("els_filters_activated", default=False)

