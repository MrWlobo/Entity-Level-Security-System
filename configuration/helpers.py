from els.core.context import _current_session


# Required to avoid circular imports
def get_session():
    return _current_session.get()