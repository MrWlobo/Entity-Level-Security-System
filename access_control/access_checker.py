from els.access_control.permission_cache import PermissionFlyweightFactory
from els.access_control.permission_resolver import PermissionResolver


class AccessChecker:
    @staticmethod
    def can_insert(user_id: int, table: str) -> bool:
        # Check if ids are cached
        cached_val = PermissionFlyweightFactory.get((user_id, table, "INSERT"))
        if cached_val is not None:
            return cached_val
        
        # Build role tree
        role_roots = PermissionResolver.build_user_role_tree(user_id, table, "INSERT")

        # Get id list from tree
        can_insert = PermissionResolver.resolve_permissions(role_roots, "INSERT")

        # Cache value
        PermissionFlyweightFactory.set((user_id, table, "INSERT"), can_insert)

        return can_insert