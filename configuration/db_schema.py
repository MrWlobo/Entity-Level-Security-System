# configuration/db_schema.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from .config import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True)
    password_hash = Column(String(255))
    email = Column(String(255), unique=True)
    is_active = Column(Boolean, default=True)

    roles = relationship("UserRole", back_populates="user")

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True)
    description = Column(Text)
    parent_role_id = Column(Integer, ForeignKey("roles.id"), nullable=True)

    children = relationship("Role", backref="parent", remote_side=[id])

class UserRole(Base):
    __tablename__ = "user_roles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    role_id = Column(Integer, ForeignKey("roles.id"))

    user = relationship("User", back_populates="roles")
    role = relationship("Role")

class Permission(Base):
    __tablename__ = "permissions"
    id = Column(Integer, primary_key=True, index=True)
    grantee_type = Column(String(50))   # "user" lub "role"
    grantee_id = Column(Integer)        # id użytkownika lub roli
    table_name = Column(String(255))
    action = Column(String(50))         # SELECT / UPDATE / DELETE / INSERT
    access_type = Column(String(50))    # WHITELIST / BLACKLIST
    row_ids = Column(Text, nullable=True)
    version = Column(Integer, default=1)
