from configuration.db_schema import Version
from configuration.helpers import get_session
from utils.patterns.flyweight import FlyweightFactory


class PermissionFlyweightFactory(FlyweightFactory):
    _cache: dict[tuple[int, str, str], tuple[int, tuple[list[int], bool]]] = {} # Vals are tuples of (version, ids) or (version, can_insert)
    
    @staticmethod
    def get(key: tuple[int, str, str]) -> list[int] | bool | None:
        cache_val = PermissionFlyweightFactory._cache.get(key) # Get value from cache
        # Check for cache miss
        if cache_val is None:
            return None
        
        user_id, _, _ = key
        cache_version, ids = cache_val

        # Check if cache is up to date
        session = get_session()
        user_version = session.query(Version.version).filter(Version.user_id == user_id).scalar()
        if user_version != cache_version:
            return None

        # If cache hit and cache is up to date, return the cached ids
        return ids
    
    @staticmethod
    def set(key: tuple[int, str, str], value: list[int] | bool) -> None:
        user_id, _, _ = key
    
        session = get_session()
        user_version = session.query(Version.version).filter(Version.user_id == user_id).scalar()

        PermissionFlyweightFactory._cache[key] = (user_version, value)

    @staticmethod
    def clear() -> None:
        PermissionFlyweightFactory._cache = {}