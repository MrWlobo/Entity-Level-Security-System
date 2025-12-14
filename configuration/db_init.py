
from config import Base
from db_schema import User, Role, UserRole, Permission
from core.session_manager import SessionManager

def init_db():
    print(">>> Tworzenie tabel w bazie...")
    db = SessionManager.get_session()
    Base.metadata.create_all(bind=db.bind)  # używamy engine powiązanego z sesją
    print(">>> Gotowe.")
