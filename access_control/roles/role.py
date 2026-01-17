from els.utils.patterns.composite import RoleComponent


class RolePlain(RoleComponent):
    def __init__(self, role_id: int, action: str):
        super().__init__(role_id, action)
        self.permission_data: tuple[list[int], bool | None] | None = None

    def get_permissions(self) -> tuple[list[int], bool | None] | None:
        return self.permission_data