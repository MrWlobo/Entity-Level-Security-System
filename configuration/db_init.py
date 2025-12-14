
from config import Base, engine
from db_schema import User, Role, UserRole, Permission

def init_db():
    print(">>> Tworzenie tabel w bazie...")
    Base.metadata.create_all(bind=engine)
    print(">>> Gotowe.")
