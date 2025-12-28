
from configuration.helpers import get_session
from .config import Base
from .db_schema import User, Role, UserRole, Permission

def init_db():
    print(">>> Tworzenie tabel w bazie...")
    db = get_session()
    Base.metadata.create_all(bind=db.bind)  # używamy engine powiązanego z sesją
    print(">>> Gotowe.")
