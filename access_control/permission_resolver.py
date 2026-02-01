# els/access_control/permission_resolver.py
from sqlalchemy import select
from sqlalchemy.orm import Session

from els.access_control.permission_cache import PermissionFlyweightFactory
from els.access_control.roles.role import RolePlain
from els.access_control.roles.role_group import RoleGroup
from els.configuration.db_schema import Permission, Role, UserRole
from els.configuration.helpers import get_session
from els.utils.patterns.composite import RoleComponent


class PermissionResolver:
    @staticmethod
    def get_accessible_row_ids(user_id: int, table: str, action: str) -> list[int]:
        if action == "INSERT":
            raise ValueError("Action cannot be INSERT for get_accessible_row_ids, use AccessChecker.")
        
        # Check if ids are cached
        cached_val = PermissionFlyweightFactory.get((user_id, table, action))
        if cached_val is not None:
            return cached_val
        
        # Build role tree
        role_roots = PermissionResolver.build_user_role_tree(user_id, table, action)

        # Get id list from tree
        ids = PermissionResolver.resolve_permissions(role_roots, action)

        # Cache ids
        PermissionFlyweightFactory.set((user_id, table, action), ids)

        return ids
    
    @staticmethod
    def build_user_role_tree(user_id: int, table_name: str, action: str) -> list[RoleComponent]:
        session = get_session()
        
        # Fetch Data
        roles_data = PermissionResolver._fetch_role_hierarchy(session, user_id)
        root_role_ids = PermissionResolver._get_user_direct_role_ids(session, user_id)
        
        all_role_ids = list(roles_data.keys())
        role_perms_map = PermissionResolver._fetch_role_permissions(
            session, all_role_ids, table_name, action
        )

        user_perms_list = PermissionResolver._fetch_user_permissions(
            session, user_id, table_name, action
        )

        # Build Tree
        result_components = []

        # Process direct User permissions
        for perm_data in user_perms_list:
            user_component = RolePlain(role_id=-1, action=action)
            PermissionResolver._hydrate_plain_role(user_component, perm_data, action)
            result_components.append(user_component)

        # Process Role hierarchies
        for rid in root_role_ids:
            if rid in roles_data:
                component = PermissionResolver._build_node(
                    rid, roles_data, role_perms_map, table_name, action
                )
                result_components.append(component)
        
        return result_components
    

    @staticmethod
    def resolve_permissions(components: list[RoleComponent], action: str) -> list[int] | bool:
        """
        Resolves the final permission set from a list of root components.
        
        - If action is INSERT: Returns True if ANY component allows insert.
        - If action is SELECT/UPDATE: Returns unique list of all allowed row_ids (Union).
        """
        if action == 'INSERT':
            for comp in components:
                result = comp.get_permissions()
                if result:
                    _, can_insert = result
                    if can_insert:
                        return True
            return False 
        else:
            final_ids: set[int] = set()
            for comp in components:
                result = comp.get_permissions()
                if result:
                    row_ids, _ = result
                    final_ids.update(row_ids)
            
            return list(final_ids)

    @staticmethod
    def _build_node(role_id: int, children_map: dict[int, list[int]], perm_map: dict[int, dict], table: str, action: str) -> RoleComponent:
        child_ids = children_map.get(role_id, [])
        role_perms = perm_map.get(role_id)

        if child_ids:
            group = RoleGroup(role_id, action)

            if role_perms:
                artificial_child = RolePlain(role_id, action)
                PermissionResolver._hydrate_plain_role(artificial_child, role_perms, action)
                group.add_child(artificial_child)
                artificial_child.set_parent(group)

            for child_id in child_ids:
                child_node = PermissionResolver._build_node(
                    child_id, children_map, perm_map, table, action
                )
                group.add_child(child_node)
                child_node.set_parent(group)
            
            return group
        else:
            plain = RolePlain(role_id, action)
            if role_perms:
                PermissionResolver._hydrate_plain_role(plain, role_perms, action)
            return plain

    @staticmethod
    def _hydrate_plain_role(role: "RolePlain", perms: dict, action: str) -> None:
        """
        Sets the permission_data.
        - INSERT: ([], bool)
        - SELECT/UPDATE: ([ids], None) -> Bool is unused/None
        """
        row_ids_str = perms.get('row_ids')

        row_ids = []
        if row_ids_str:
            row_ids = [
                int(x.strip()) 
                for x in row_ids_str.split(',') 
                if x.strip()
            ]

        if action == 'INSERT':
            role.permission_data = ([], True)
        else:
            role.permission_data = (row_ids, None)

    @staticmethod
    def _get_user_direct_role_ids(session: Session, user_id: int) -> list[int]:
        stmt = select(UserRole.role_id).where(UserRole.user_id == user_id)
        return session.execute(stmt).scalars().all()

    @staticmethod
    def _fetch_user_permissions(session: Session, user_id: int, table: str, action: str) -> list[dict]:
        stmt = (
            select(Permission.row_ids)
            .where(
                Permission.user_id == user_id,
                Permission.role_id.is_(None),
                Permission.table_name == table,
                Permission.action == action
            )
        )
        rows = session.execute(stmt).all()
        return [{'row_ids': row.row_ids} for row in rows]

    @staticmethod
    def _fetch_role_permissions(session: Session, role_ids: list[int], table: str, action: str) -> dict[int, dict]:
        if not role_ids:
            return {}

        stmt = (
            select(Permission.role_id, Permission.row_ids)
            .where(
                Permission.role_id.in_(role_ids),
                Permission.table_name == table,
                Permission.action == action
            )
        )
        rows = session.execute(stmt).all()
        
        perm_map = {}
        for row in rows:
            rid = row.role_id
            current_ids = row.row_ids or ""
            
            if rid not in perm_map:
                perm_map[rid] = {'row_ids': current_ids}
            else:
                existing_ids = perm_map[rid]['row_ids']
                if existing_ids and current_ids:
                    perm_map[rid]['row_ids'] = f"{existing_ids},{current_ids}"
                elif current_ids:
                    perm_map[rid]['row_ids'] = current_ids
                    
        return perm_map

    @staticmethod
    def _fetch_role_hierarchy(session: Session, user_id: int) -> dict[int, list[int]]:
        anchor = (
            select(Role.id, Role.parent_role_id)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
            .cte(name="role_tree", recursive=True)
        )

        role_alias = select(Role.id, Role.parent_role_id).subquery()
        recursive = (
            select(role_alias.c.id, role_alias.c.parent_role_id)
            .join(anchor, role_alias.c.parent_role_id == anchor.c.id)
        )

        cte = anchor.union_all(recursive)
        
        stmt = select(cte.c.id, cte.c.parent_role_id)
        rows = session.execute(stmt).all()

        adj_map = {}
        for rid, pid in rows:
            if rid not in adj_map:
                adj_map[rid] = []
            
            if pid is not None:
                if pid not in adj_map:
                    adj_map[pid] = []
                adj_map[pid].append(rid)
                
        return adj_map