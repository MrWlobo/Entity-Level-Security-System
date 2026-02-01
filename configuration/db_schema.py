# els/configuration/db_schema.py
from els.configuration.config import Base

from sqlalchemy import CheckConstraint, Column, Integer, String, Boolean, ForeignKey, Text, event, update, insert, select, literal
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


def bump_users_with_role(connection, role_id):
    """
    Invalidates cache for all users who possess this role OR any parent role 
    that inherits from this role.
    """
    if role_id is None:
        return

    roles_table = Role.__table__

    hierarchy = (
        select(roles_table.c.id, roles_table.c.parent_role_id)
        .where(roles_table.c.id == role_id)
        .cte(name="role_ancestry", recursive=True)
    )
    
    role_alias = roles_table.alias()
    hierarchy = hierarchy.union_all(
        select(role_alias.c.id, role_alias.c.parent_role_id)
        .join(hierarchy, role_alias.c.id == hierarchy.c.parent_role_id)
    )

    stmt = (
        update(Version)
        .where(
            Version.user_id.in_(
                select(UserRole.user_id)
                .join(hierarchy, UserRole.role_id == hierarchy.c.id)
            )
        )
        .values(version=Version.version + 1)
    )
    connection.execute(stmt)


@event.listens_for(Permission, 'after_insert')
@event.listens_for(Permission, 'after_delete')
def receive_change(mapper, connection, target):
    """
    Listens for new or deleted permissions.
    """
    if target.user_id:
        bump_version_for_user(connection, target.user_id)
    
    if target.role_id:
        bump_users_with_role(connection, target.role_id)


@event.listens_for(Permission, 'after_update')
def receive_update(mapper, connection, target):
    """
    Listens for updates to existing permissions.
    """
    history_user = attributes.get_history(target, 'user_id')
    if history_user.has_changes():
        if target.user_id:
            bump_version_for_user(connection, target.user_id)
        if history_user.deleted and history_user.deleted[0]:
            bump_version_for_user(connection, history_user.deleted[0])

    history_role = attributes.get_history(target, 'role_id')
    if history_role.has_changes():
        if target.role_id:
            bump_users_with_role(connection, target.role_id)
        if history_role.deleted and history_role.deleted[0]:
            bump_users_with_role(connection, history_role.deleted[0])
            
    if not history_user.has_changes() and not history_role.has_changes():
        if target.user_id:
            bump_version_for_user(connection, target.user_id)
        if target.role_id:
            bump_users_with_role(connection, target.role_id)


@event.listens_for(UserRole, 'after_insert')
@event.listens_for(UserRole, 'after_delete')
def receive_user_role_change(mapper, connection, target):
    """
    Bumps the user version when a role is assigned or revoked.
    """
    bump_version_for_user(connection, target.user_id)


@event.listens_for(UserRole, 'after_update')
def receive_user_role_update(mapper, connection, target):
    bump_version_for_user(connection, target.user_id)
    
    history = attributes.get_history(target, 'user_id')
    if history.deleted:
        old_user_id = history.deleted[0]
        if old_user_id != target.user_id:
            bump_version_for_user(connection, old_user_id)


@event.listens_for(User, 'after_insert')
def create_initial_version(mapper, connection, target):
    """
    When a User is created, automatically create their Version row.
    """
    connection.execute(
        insert(Version).values(user_id=target.id, version=1)
    )