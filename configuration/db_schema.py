# configuration/db_schema.py
from els.configuration.config import Base

from sqlalchemy import CheckConstraint, Column, Integer, String, Boolean, ForeignKey, Text, event, update, insert
from sqlalchemy.orm import relationship, attributes

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True)
    password_hash = Column(String(255))
    email = Column(String(255), unique=True)
    is_active = Column(Boolean, default=True)

    roles = relationship("UserRole", back_populates="user")
    permissions = relationship("Permission", back_populates="user")
    versions = relationship("Version", back_populates="user", uselist=False)


class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True)
    description = Column(Text)
    parent_role_id = Column(Integer, ForeignKey("roles.id"), nullable=True)

    children = relationship("Role", backref="parent", remote_side=[id])
    permissions = relationship("Permission", back_populates="role")


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
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True)
    table_name = Column(String(255))
    action = Column(String(50))         # SELECT / UPDATE / DELETE / INSERT
    row_ids = Column(Text, nullable=True)

    user = relationship("User", back_populates="permissions")
    role = relationship("Role", back_populates="permissions")

    # Ensure only one is set (User or Role, not both)
    __table_args__ = (
        CheckConstraint(
            '(user_id IS NOT NULL AND role_id IS NULL) OR (user_id IS NULL AND role_id IS NOT NULL)',
            name='check_grantee_set'
        ),
    )


class Version(Base):
    __tablename__ = "versions"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    version = Column(Integer, nullable=False)

    user = relationship("User", back_populates="versions")


def bump_version_for_user(connection, user_id):
    """Helper function to atomically increment version."""
    if user_id is not None:
        connection.execute(
            update(Version)
            .where(Version.user_id == user_id)
            .values(version=Version.version + 1)
        )


@event.listens_for(Permission, 'after_insert')
@event.listens_for(Permission, 'after_delete')
def receive_change(mapper, connection, target):
    """
    Listens for new or deleted permissions.
    Target is the Permission instance being inserted/deleted.
    """
    bump_version_for_user(connection, target.user_id)


@event.listens_for(Permission, 'after_update')
def receive_update(mapper, connection, target):
    """
    Listens for updates to existing permissions.
    Handles the edge case where a permission might be reassigned to a different user.
    """
    bump_version_for_user(connection, target.user_id)

    history = attributes.get_history(target, 'user_id')
    
    if history.deleted:
        old_user_id = history.deleted[0]
        if old_user_id != target.user_id:
            bump_version_for_user(connection, old_user_id)


@event.listens_for(UserRole, 'after_insert')
@event.listens_for(UserRole, 'after_delete')
def receive_user_role_change(mapper, connection, target):
    """
    Bumps the user version when a role is assigned or revoked.
    Target is the UserRole instance.
    """
    bump_version_for_user(connection, target.user_id)


@event.listens_for(UserRole, 'after_update')
def receive_user_role_update(mapper, connection, target):
    """
    Handle edge case if a UserRole row is updated (rare, but safe to handle).
    """
    bump_version_for_user(connection, target.user_id)
    
    # If the user_id itself changed (e.g. reassigning a role entry to another user)
    history = attributes.get_history(target, 'user_id')
    if history.deleted:
        old_user_id = history.deleted[0]
        if old_user_id != target.user_id:
            bump_version_for_user(connection, old_user_id)


@event.listens_for(User, 'after_insert')
def create_initial_version(mapper, connection, target):
    """
    When a User is created, automatically create their Version row
    starting at 1.
    """
    connection.execute(
        insert(Version).values(user_id=target.id, version=1)
    )