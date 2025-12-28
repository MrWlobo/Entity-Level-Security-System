from sqlalchemy.orm import Session

from access_control.access_checker import AccessChecker
from access_control.permission_resolver import PermissionResolver
from configuration.db_schema import User
from .context import _current_user, _current_session, _current_base, _filters_activated

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
        SessionManager.modify_session()

    """
        Modifying the session so that before every commit all of the changed objects are checked 
        and optionally excluded from the update 
    """
    @staticmethod
    def modify_session():
        session = SessionManager.get_session()
        session.autoflush = False
        original_commit = session.commit

        def modified_commit():
            if _filters_activated.get(): SessionManager.check_changes_before_commit(session)
            original_commit()

        session.commit = modified_commit


    @staticmethod
    def get_session() -> Session:
        return _current_session.get()

    """
        Checking all of the objects before commits, necessary if user uses orm functions to change the DB
    """
    @staticmethod
    def check_changes_before_commit(session):
        current_user = CurrentUserContext.get_current_user()

        # UPDATE
        for obj in list(session.dirty):
            cls = str(type(obj))
            ids = PermissionResolver.get_accessible_row_ids(current_user.id, cls, "UPDATE")
            if hasattr(obj, "id") and obj.id not in ids:
                session.expunge(obj)

        # DELETE
        for obj in list(session.deleted):
            cls = str(type(obj))
            ids = PermissionResolver.get_accessible_row_ids(current_user.id, cls, "DELETE")
            if hasattr(obj, "id") and obj.id not in ids:
                session.expunge(obj)

        # INSERT
        for obj in list(session.new):
            cls = str(type(obj))
            can_insert = AccessChecker.can_insert(current_user.id, cls)
            if hasattr(obj, "id") and not can_insert:
                session.expunge(obj)

class BaseManager:

    @staticmethod
    def set_base(base):
        _current_base.set(base)

    @staticmethod
    def get_base():
        return _current_base.get()