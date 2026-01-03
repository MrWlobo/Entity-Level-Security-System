from typing import Iterator, Tuple
import re
from access_control.access_checker import AccessChecker
from core.session_manager import BaseManager, CurrentUserContext, StrategyManager
from runtime_modifier.filter_generator import FilterGenerator


class QueryModifier:

    @staticmethod
    def find(keyword: str, code: str, orm_classes: list[str]) -> Iterator[Tuple[int, int, str]]:
        """
            Searching for keyword functions that have to be treated with a custom filter
            Returning its position & argument in it - queried table
        """
        pattern = keyword + r"\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)"
        for m in re.finditer(pattern, code):
            cls_name = m.group(1)
            if cls_name in orm_classes:
                yield m.start(), m.end(), cls_name


    @staticmethod
    def modify_function(code: str):
        """
            Searching for keyword functions that have to be treated with a custom filter
        """
        all_orm_classes = [mapper.class_.__name__ for mapper in BaseManager.get_base().registry.mappers]
        current_user = CurrentUserContext.get_current_user()

        #Handling select & query functions + bulk functions for update and delete
        keywords = ["select", "query", "update", "delete"]
        for keyword in keywords:
            matches = list(QueryModifier.find(keyword, code, all_orm_classes))
            for start, end, cls in reversed(matches):
                filter_clause = FilterGenerator.generate_where_clause({
                    "user_id": current_user.id,
                    "table": cls,
                    "action": keyword.upper() if keyword != "query" else "SELECT"
                })
                code = code[:start] + f"{keyword}({cls}).where({filter_clause})" + code[end:]


        #Checking insert permissions
        matches_insert = list(QueryModifier.find("insert", code, all_orm_classes))
        for start, end, cls in reversed(matches_insert):
            can_insert = AccessChecker.can_insert(current_user.id, cls)
            if not StrategyManager.get_strategy().apply(can_insert):
                raise PermissionError()

        return code
