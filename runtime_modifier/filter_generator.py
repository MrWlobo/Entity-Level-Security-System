from access_control.permission_resolver import PermissionResolver


class FilterGenerator:

    @staticmethod
    def generate_where_clause(filter_info : dict) -> str:
        ids = PermissionResolver.get_accessible_row_ids(filter_info["user_id"], filter_info["table"], filter_info["action"])
        # plus tu będzie jeszcze handling strategi: in_ lub notin_
        return f"{filter_info['table']}.id.in_({ids})"
