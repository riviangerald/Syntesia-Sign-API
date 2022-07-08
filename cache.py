from collections import OrderedDict
from typing import Union

import constants


class Cache:
    def __init__(self):
        self._cache = OrderedDict()
        self.capacity = constants.CACHE_CAPACITY

    def get(self, key: str) -> Union[str, None]:
        if key not in self._cache:
            return None
        else:
            self._cache.move_to_end(key)
            return self._cache[key]

    def put(self, key: str, value: str) -> None:
        self._cache[key] = value
        self._cache.move_to_end(key)
        if len(self._cache) > self.capacity:
            self._cache.popitem(last=False)
