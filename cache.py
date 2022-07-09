import redis
from collections import OrderedDict
from typing import Union

import constants


class Cache:
    def __init__(self):
        self._cache = OrderedDict()
        self.capacity = constants.CACHE_CAPACITY
        self.__redis = None
        try:
            self.__redis = redis.Redis(host=constants.REDIS_HOST,
                                       port=constants.REDIS_PORT,
                                       password=constants.REDIS_PASSWORD)
        except:
            print("Redis db is not present.")
        self.__build_cache()

    def __build_cache(self) -> None:
        try:
            data = self.__redis.hgetall(constants.REDIS_FIELD)
            for key, value in data.items():
                self.put(key.decode('UTF-8'), value.decode('UTF-8'))
        except:
            print("Redis db is not present.")

    def get(self, key: str) -> Union[str, None]:
        if key not in self._cache:
            return None
        else:
            self._cache.move_to_end(key)
            return self._cache[key]

    def put(self, key: str, value: str) -> None:
        self._cache[key] = value
        self._cache.move_to_end(key)
        if self.__redis is not None:
            try:
                self.__redis.hset(constants.REDIS_FIELD, key, value)
            except redis.exceptions.ConnectionError:
                pass
        if len(self._cache) > self.capacity:
            del_key, _ = self._cache.popitem(last=False)
            if self.__redis is not None:
                try:
                    self.__redis.hdel(constants.REDIS_FIELD, del_key)
                except redis.exceptions.ConnectionError:
                    pass

