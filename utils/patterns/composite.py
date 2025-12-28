from __future__ import annotations
import abc


class RoleComponent(abc.ABC):
    def __init__(self, role_id: int, action: str):
        self.role_id = role_id
        self.action = action
        self._parent: RoleComponent | None = None
    
    def set_parent(self, parent: "RoleComponent") -> None:
        self._parent = parent

    @abc.abstractmethod
    def get_permissions(self) -> tuple[list[int], bool | None] | None:
        """
        Returns (row_ids, bool_flag) or None.
        - INSERT: ([], bool)
        - SELECT/UPDATE: ([ids], None)
        """
        raise NotImplementedError()