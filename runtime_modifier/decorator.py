from typing import Callable
from runtime_modifier.execution_handler import ExecutionHandler


def secure(fn: Callable):
    def wrapper(*args, **kwargs):
        return ExecutionHandler.apply_permission_filter(fn)(*args, **kwargs)
    return wrapper

