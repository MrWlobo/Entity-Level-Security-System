from .context import _current_user, _current_session

class CurrentUserContext:

    """
        Na razie użyłem typu str jako placeholder -> domyślnie typ User
    """
    @staticmethod
    def set_current_user(user : str):
        _current_user.set(user)

    @staticmethod
    def get_current_user() -> str:
        return _current_user.get()

class SessionManager:

    """
        Na razie użyłem typu str jako placeholder -> domyślnie typ Session
    """
    @staticmethod
    def set_session(session : str):
        _current_session.set(session)

    @staticmethod
    def get_session() -> str:
        return _current_session.get()