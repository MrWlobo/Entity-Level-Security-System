
from els.configuration.db_schema import User, Role, Permission, UserRole
from els.configuration.helpers import get_session

class UserManager:
    def create_user(self, username, password_hash, email):
        db = get_session()
        user = User(username=username, password_hash=password_hash, email=email)
        db.add(user)
        db.commit()
        return user

class RoleManager:
    def create_role(self, name, description=None, parent_role_id=None):
        db = get_session()
        role = Role(name=name, description=description, parent_role_id=parent_role_id)
        db.add(role)
        db.commit()
        return role

    def assign_role(self, user_id, role_id):
        db = get_session()
        user_role = UserRole(user_id=user_id, role_id=role_id)
        db.add(user_role)
        db.commit()
        return user_role


class PermissionManager:
    def grant_permission(self, user_id, role_id, table_name, action, row_ids=None):
        db = get_session()
        perm = Permission(
            user_id=user_id,
            role_id=role_id,
            table_name=table_name,
            action=action,
            row_ids=row_ids
        )
        db.add(perm)
        db.commit()
        return perm
