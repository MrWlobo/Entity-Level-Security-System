from typing import Callable
from runtime_modifier.execution_handler import ExecutionHandler


def secure(fn: Callable):
    def wrapper():
        return ExecutionHandler.apply_permission_filter(fn)()
    return wrapper

