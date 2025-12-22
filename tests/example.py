from configuration.db_schema import User
from core.session_manager import CurrentUserContext, SessionManager, BaseManager
from runtime_modifier.decorator import secure
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base
from sqlalchemy import select, update, delete, insert

engine = create_engine("sqlite:///users2.db", echo=False)
Base = declarative_base()


class TestUser(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    salary = Column(Float, nullable=False)

    def __init__(self, name, salary):
        self.name = name
        self.salary = salary

def test_select():

    users = session.query(TestUser).all()
    for user in users:
        print(user.id, user.name, user.salary)

@secure
def test_update():

    stmt = (
        update(TestUser)
        .where(TestUser.id == 8)
        .values(salary=6700)
    )
    session.execute(stmt)
    session.commit()

@secure
def test_delete():

    stmt = (
        delete(TestUser)
        .where(TestUser.id == 1)
    )
    session.execute(stmt)
    session.commit()

def test_insert():

    stmt = insert(TestUser).values([
        {"id": 1, "name": "Anna", "salary": 3000},
        {"id": 3, "name": "Jonasz", "salary": 5000},
    ])

    session.execute(stmt)
    session.commit()

def create():
    user1 = TestUser("Adam", 1300)
    user2 = TestUser( "Ewa", 1500)
    user3 = TestUser("Jan", 1200)

    session.add_all([user1, user2, user3])
    session.commit()

@secure
def test_update_orm():
    stmt = select(TestUser).where(TestUser.id == 3)
    user = session.execute(stmt).scalar_one()
    user.name = "Jonasz"
    session.add(user)
    session.commit()
    stmt = select(TestUser).where(TestUser.id == 8)
    user = session.execute(stmt).scalar_one()
    user.name = "Danuta"
    session.add(user)
    session.commit()

@secure
def test_delete_orm():
    stmt = select(TestUser).where(TestUser.id == 3)
    user1 = session.execute(stmt).scalar_one()
    session.delete(user1)
    session.commit()
    stmt = select(TestUser).where(TestUser.id == 2)
    user2 = session.execute(stmt).scalar_one()
    session.delete(user2)
    session.commit()

@secure
def test_insert_orm():
    new_user = TestUser("Monika2", 1600)
    session.add(new_user)
    session.commit()

if __name__ == "__main__":
    CurrentUserContext.set_current_user(User())
    session = Session(engine)
    SessionManager.set_session(session)
    BaseManager.set_base(Base)
    test_update_orm()
    test_select()