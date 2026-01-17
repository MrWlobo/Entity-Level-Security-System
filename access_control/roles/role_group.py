from els.utils.patterns.composite import RoleComponent


class RoleGroup(RoleComponent):
    def __init__(self, role_id: int, action: str):
        super().__init__(role_id, action)
        self.children: list[RoleComponent] = []

    def add_child(self, child: RoleComponent):
        self.children.append(child)

    def get_permissions(self) -> tuple[list[int], bool | None] | None:
        if self.action == 'INSERT':
            return self._resolve_insert()
        else:
            return self._resolve_row_level_access()

    def _resolve_insert(self) -> tuple[list[int], bool | None] | None:
        """
        INSERT Logic: Additive (Any True is True).
        """
        can_insert = False
        has_data = False

        for child in self.children:
            result = child.get_permissions()
            if result is None:
                continue
            
            has_data = True
            _, child_can_insert = result
            if child_can_insert:
                can_insert = True
                break
        
        if not has_data:
            return None
            
        return [], can_insert

    def _resolve_row_level_access(self) -> tuple[list[int], bool | None] | None:
        """
        SELECT/UPDATE Logic: Pure Additive Union.
        The bool flag is ignored.
        """
        combined_ids: set[int] = set()
        has_data = False

        for child in self.children:
            result = child.get_permissions()
            if result is None:
                continue

            has_data = True
            row_ids, _ = result # Ignore bool flag
            combined_ids.update(row_ids)

        if not has_data:
            return None

        return list(combined_ids), None