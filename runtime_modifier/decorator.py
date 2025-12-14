from core.session_manager import CurrentUserContext,SessionManager

def secure(fn):
     def wrapper(*args, **kwargs):
        user = CurrentUserContext.get_current_user()
        session = SessionManager.get_session()
        print(f"CurrentUser: {user}, session: {session}")
        return  fn(*args, **kwargs)
     return wrapper