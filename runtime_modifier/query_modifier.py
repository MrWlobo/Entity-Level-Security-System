from typing import Iterator, Tuple
import re
from els.access_control.access_checker import AccessChecker
from els.core.session_manager import BaseManager, CurrentUserContext, StrategyManager
from els.runtime_modifier.filter_generator import FilterGenerator


class QueryModifier:

    @staticmethod
    def find(keyword: str, code: str, orm_classes: list[str]) -> Iterator[Tuple[int, int, str, str]]:
        pattern = keyword + r"\s*\(\s*([A-Za-z_][A-Za-z0-9_.]*)\s*\)"
        for m in re.finditer(pattern, code):
            full_name = m.group(1)
            
            if "." in full_name:
                cls_name = full_name.split(".")[-1]
            else:
                cls_name = full_name

            if cls_name in orm_classes:
                yield m.start(), m.end(), full_name, cls_name


    @staticmethod
    def modify_function(code: str):
        all_orm_classes = [mapper.class_.__name__ for mapper in BaseManager.get_base().registry.mappers]
        current_user = CurrentUserContext.get_current_user()

        keywords = ["select", "query", "update", "delete"]
        for keyword in keywords:
            matches = list(QueryModifier.find(keyword, code, all_orm_classes))
            for start, end, full_name, cls_name in reversed(matches):
                filter_clause = FilterGenerator.generate_where_clause({
                    "user_id": current_user.id,
                    "table": cls_name,
                    "variable_name": full_name,
                    "action": keyword.upper() if keyword != "query" else "SELECT"
                })
                code = code[:start] + f"{keyword}({full_name}).where({filter_clause})" + code[end:]


        matches_insert = list(QueryModifier.find("insert", code, all_orm_classes))
        for start, end, full_name, cls_name in reversed(matches_insert):
            can_insert = AccessChecker.can_insert(current_user.id, cls_name)
            if not StrategyManager.get_strategy().apply(can_insert):
                raise PermissionError()

        return code