from contextvars import ContextVar
from access_control.strategies.WhitelistStrategy import WhitelistStrategy

_current_user = ContextVar("els_current_user", default=None)
_current_session = ContextVar("els_current_session", default=None)
_current_base = ContextVar("els_current_base", default=None)
_current_strategy = ContextVar("els_current_strategy", default=WhitelistStrategy())
_filters_activated = ContextVar("els_filters_activated", default=False)

