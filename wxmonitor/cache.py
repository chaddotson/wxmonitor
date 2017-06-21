from logging import getLogger
from threading import RLock
from uuid import uuid4

from cachetools import TTLCache

logger = getLogger(__name__)


class Cache(object):
    """Thread-safe cache composed of TTLCache."""
    # TODO: Investigate actual need for this class given the usage and underlying TTLCache implementation.
    # The dict type may provice an appropriate level of thread-safety.
    def __init__(self, ttl=3600, timer=None):
        logger.debug("Setting up processed cache, ttl=%d", ttl)

        if timer is None:
            self._cache = TTLCache(maxsize=10000000, ttl=ttl)
        else:
            self._cache = TTLCache(maxsize=10000000, ttl=ttl, timer=timer)

        self._lock = RLock()

    def __len__(self):
        return len(self._cache)

    def add(self, processed_status):
        with self._lock:
            self._cache[uuid4()] = processed_status

    def get_statuses(self):
        statuses = []
        with self._lock:
            statuses = list(self._cache.values())

        return statuses

    def expire(self):
        with self._lock:
            self._cache.expire()