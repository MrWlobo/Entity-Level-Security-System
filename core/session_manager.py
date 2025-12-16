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
            SessionManager.check_changes_before_commit(session)
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

        # UPDATE
        for obj in list(session.dirty):
            cls = str(type(obj))
            #ids = PermissionResolver.get_accessible_row_ids(user_id, cls ,"INSERT")
            ids = [1,2]
            if hasattr(obj, "id") and obj.id not in ids:
                session.expunge(obj)

        # DELETE
        for obj in list(session.deleted):
            cls = str(type(obj))
            # ids = PermissionResolver.get_accessible_row_ids(user_id, cls ,"DELETE")
            ids = [1, 2]
            if hasattr(obj, "id") and obj.id not in ids:
                session.expunge(obj)

        # INSERT
        for obj in list(session.new):
            cls = str(type(obj))
            #can_insert = AccessChecker.can_insert(user_id, cls)
            can_insert = True
            if hasattr(obj, "id") and not can_insert:
                session.expunge(obj)

class BaseManager:

    @staticmethod
    def set_base(base):
        _current_base.set(base)

    @staticmethod
    def get_base():
        return _current_base.get()