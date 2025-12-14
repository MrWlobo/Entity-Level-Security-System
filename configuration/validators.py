
from db_schema import Role

def validate_role_hierarchy(db):
    """Sprawdza czy role nie tworzą cykli w hierarchii."""
    roles = db.query(Role).all()
    visited = set()

    def dfs(role, path):
        if role.id in path:
            raise Exception(f"Cycle detected in role hierarchy at role {role.name}")
        path.add(role.id)
        for child in role.children:
            dfs(child, path.copy())

    for role in roles:
        dfs(role, set())
    return True
