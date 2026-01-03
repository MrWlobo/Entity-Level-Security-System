from access_control.permission_resolver import PermissionResolver
from core.session_manager import StrategyManager


class FilterGenerator:

    @staticmethod
    def generate_where_clause(filter_info : dict) -> str:
        """
            Constructing a WHERE clause for a filter based on the current strategy
        """
        ids = PermissionResolver.get_accessible_row_ids(filter_info["user_id"], filter_info["table"], filter_info["action"])
        if StrategyManager.get_strategy().apply(True):
            return f"{filter_info['table']}.id.in_({ids})"
        else :
            return f"{filter_info['table']}.id.notin_({ids})"
