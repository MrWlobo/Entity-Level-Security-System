from typing import Callable
import ast, astor
from runtime_modifier.query_modifier import QueryModifier
from sqlalchemy.orm.exc import NoResultFound
from core.context import _filters_activated

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

    """
        Creating the new function object with applied filters
    """
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

        def wrapper(*args, **kwargs):
            try:
                _filters_activated.set(True)
                result = new_func(*args, **kwargs)
                _filters_activated.set(False)
            except NoResultFound:
                raise PermissionError("You don't have access to desired rows")
            return result
        return wrapper
