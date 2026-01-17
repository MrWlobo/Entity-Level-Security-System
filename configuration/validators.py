
from els.configuration.helpers import get_session
from els.configuration.db_schema import Role

def validate_role_hierarchy():
    """Sprawdza czy role nie tworzą cykli w hierarchii."""
    db = get_session()
    roles = db.query(Role).all()

    def dfs(role, path):
        if role.id in path:
            raise Exception(f"Cycle detected in role hierarchy at role {role.name}")
        path.add(role.id)
        for child in role.children:
            dfs(child, path.copy())

    for role in roles:
        dfs(role, set())
    return True
