from els.access_control.permission_resolver import PermissionResolver
from els.core.session_manager import StrategyManager


class FilterGenerator:

    @staticmethod
    def generate_where_clause(filter_info : dict) -> str:
        ids = PermissionResolver.get_accessible_row_ids(filter_info["user_id"], filter_info["table"], filter_info["action"])
        code_var = filter_info.get("variable_name", filter_info["table"])

        if StrategyManager.get_strategy().apply(True):
            return f"{code_var}.id.in_({ids})"
        else :
            return f"{code_var}.id.notin_({ids})"