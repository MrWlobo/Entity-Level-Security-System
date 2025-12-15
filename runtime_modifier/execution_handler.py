import sys
from typing import Callable
import ast, astor

from core.session_manager import SessionManager
from runtime_modifier.query_modifier import QueryModifier
from sqlalchemy.orm.exc import NoResultFound


class ExecutionHandler:

    """
        Extracting the code of searched function
    """
    @staticmethod
    def extract_function(code_str: str, function_name: str) -> str:
        tree = ast.parse(code_str)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                return astor.to_source(node)
        raise RuntimeError(f"Function {function_name} not found")

    @staticmethod
    def apply_permission_filter(fn : Callable) -> Callable:
        with open(fn.__code__.co_filename, "r") as f:
            file_src = f.read()
        func_code = ExecutionHandler.extract_function(file_src, fn.__name__)
        func_lines = func_code.splitlines()
        while func_lines and func_lines[0].strip().startswith("@"):
            func_lines.pop(0)
        func_code_no_decorator = "\n".join(func_lines)
        modified_code = QueryModifier.modify_function(func_code_no_decorator)
        ns = {}
        exec(modified_code, fn.__globals__, ns)
        new_func = ns[fn.__name__]
        new_func.__name__ = fn.__name__
        new_func.__doc__ = fn.__doc__
        new_func.__annotations__ = fn.__annotations__
        new_func.__module__ = fn.__module__
        print(modified_code)


        def wrapper(*args, **kwargs):
            session = SessionManager.get_session()
            original_commit = session.commit

            def blocked_commit():
                pass

            session.commit = blocked_commit
            try:
                result = new_func(*args, **kwargs)
            except NoResultFound:
                session.rollback()
                raise PermissionError("You don't have access to desired rows")

            ExecutionHandler.check_changes_before_commit()
            session.commit = original_commit
            session.commit()
            return result

        return wrapper

    """
        Checking all of the objects before commits, because user can use simple orm to make changes instead
        of for ex. update() func -> new_user.salary = 1500, session.add(new_user)
    """
    @staticmethod
    def check_changes_before_commit():
        session = SessionManager.get_session()

        # Update
        for obj in list(session.dirty):
            cls = str(type(obj))
            #ids = PermissionResolver.get_accessible_row_ids(user_id, cls ,"INSERT")
            ids = [1,2]
            if hasattr(obj, "id") and obj.id not in ids:
                session.expunge(obj)

        # Delete
        print("Deleted:", list(session.deleted))
        print("All in session:", list(session.identity_map.values()))
        for obj in list(session.deleted):
            print(obj, obj.id)
            cls = str(type(obj))
            # ids = PermissionResolver.get_accessible_row_ids(user_id, cls ,"DELETE")
            ids = [1, 2]
            if hasattr(obj, "id") and obj.id not in ids:
                session.expunge(obj)

        # Insert
        for obj in list(session.new):
            cls = str(type(obj))
            #can_insert = AccessChecker.can_insert(user_id, cls)
            can_insert = False
            if hasattr(obj, "id") and not can_insert:
                session.expunge(obj)