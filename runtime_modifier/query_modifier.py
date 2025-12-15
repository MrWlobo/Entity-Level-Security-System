from typing import Iterator, Tuple
import re
from core.session_manager import *
from runtime_modifier.filter_generator import FilterGenerator


class QueryModifier:

    """
        Searching for keyword functions that have to be treated with a custom filter
        Returning its position + argument in it - queried table
    """

    @staticmethod
    def find(keyword: str, code: str, orm_classes: list[str]) -> Iterator[Tuple[int, int, str]]:
        pattern = keyword + r"\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)"
        for m in re.finditer(pattern, code):
            cls_name = m.group(1)
            if cls_name in orm_classes:
                yield m.start(), m.end(), cls_name

    @staticmethod
    def remove_commit_calls_str(code: str) -> str:

        lines = code.splitlines()
        new_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.endswith(".commit()"):
                continue
            else:
                new_lines.append(line)
        return "\n".join(new_lines)

    @staticmethod
    def modify_function(code: str):
        all_orm_classes = [mapper.class_.__name__ for mapper in BaseManager.get_base().registry.mappers]
        current_user = CurrentUserContext.get_current_user()

        """
            Handling select & query functions + bulk functions for update and delete
        """
        keywords = ["select", "query", "update", "delete"]
        for keyword in keywords:
            matches = list(QueryModifier.find(keyword, code, all_orm_classes))
            for start, end, cls in reversed(matches):
                filter_dict = FilterGenerator.generate_where_clause({
                    "user_id": current_user.id,
                    "table": cls,
                    "action": keyword.upper() if keyword != "query" else "SELECT"
                })
                code = code[:start] + f"{keyword}({cls}).where({filter_dict})" + code[end:]

        """
        Checking insert permissions
        """
        matches_insert = list(QueryModifier.find("insert", code, all_orm_classes))
        for start, end, cls in reversed(matches_insert):
            #can_insert = AccessChecker.can_insert(current_user.id, cls)
            can_insert = False
            if not can_insert:
                raise PermissionError()

        code = QueryModifier.remove_commit_calls_str(code)
        return code
