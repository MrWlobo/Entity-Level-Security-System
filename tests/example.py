from core.session_manager import CurrentUserContext, SessionManager
from runtime_modifier.decorator import secure

CurrentUserContext.set_current_user("admin")
SessionManager.set_session("session")

@secure
def test_fn():
    print("test_fn")

if __name__ == "__main__":
    test_fn()