import abc


class FlyweightFactory(abc.ABC):
    @staticmethod
    @abc.abstractmethod
    def get(key: tuple[int, str, str]) -> list[int] | bool | None:
        raise NotImplementedError()
    
    @staticmethod
    @abc.abstractmethod
    def set(key: tuple[int, str, str], value: list[int] | bool) -> None:
        raise NotImplementedError()
    
    @staticmethod
    @abc.abstractmethod
    def clear() -> None:
        raise NotImplementedError()