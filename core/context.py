from contextvars import ContextVar

_current_user = ContextVar("els_current_user", default=None)
_current_session = ContextVar("els_current_session", default=None)
_current_base = ContextVar("els_current_base", default=None)
