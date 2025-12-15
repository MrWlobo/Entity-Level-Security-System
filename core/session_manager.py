from sqlalchemy.orm import Session

from configuration.db_schema import User
from .context import _current_user, _current_session, _current_base

class CurrentUserContext:

    @staticmethod
    def set_current_user(user : User):
        _current_user.set(user)

    @staticmethod
    def get_current_user() -> User:
        return _current_user.get()

class SessionManager:

    @staticmethod
    def set_session(session : Session):
        _current_session.set(session)

    @staticmethod
    def get_session() -> Session:
        return _current_session.get()

class BaseManager:

    @staticmethod
    def set_base(base):
        _current_base.set(base)

    @staticmethod
    def get_base():
        return _current_base.get()