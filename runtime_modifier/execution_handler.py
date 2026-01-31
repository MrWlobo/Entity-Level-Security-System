from typing import Callable
import inspect
import textwrap

from els.runtime_modifier.query_modifier import QueryModifier
from els.core.context import _filters_activated

from els.core.session_manager import SessionManager


class ExecutionHandler:

    @staticmethod
    def apply_permission_filter(fn : Callable) -> Callable:
        """
            Creating the new function object with applied filters
        """
        try:
            func_code = inspect.getsource(fn)
        except (OSError, TypeError) as e:
            raise RuntimeError(f"Could not retrieve source code for {fn.__name__}") from e

        func_code = textwrap.dedent(func_code)
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
            session = SessionManager.get_session()
            prev = session.info.get('filters_activated', None)
            session.info['filters_activated'] = True
            try:
                result = new_func(*args, **kwargs)
            finally:
                if prev is None:
                    session.info.pop('filters_activated')
                else:
                    session.info['filters_activated'] = prev
            return result
        return wrapper