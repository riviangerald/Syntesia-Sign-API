import redis
from collections import OrderedDict
from typing import Union

import constants
from logger import Logger


class Cache:
    def __init__(self):
        self.__logger = Logger()
        self._cache = OrderedDict()
        self.capacity = constants.CACHE_CAPACITY
        self.__redis = None
        try:
            self.__redis = redis.Redis(host=constants.REDIS_HOST,
                                       port=constants.REDIS_PORT,
                                       password=constants.REDIS_PASSWORD)
        except:
            self.__logger.error('Redis could not be initialised. Check if it is up. '
                                'And if the connection settings are valid.')
        self.__build_cache()

    def __build_cache(self) -> None:
        try:
            data = self.__redis.hgetall(constants.REDIS_FIELD)
            for key, value in data.items():
                self.put(key.decode('UTF-8'), value.decode('UTF-8'))
        except:
            self.__logger.error('Build cache error. Redis is down or connection is broken.')

    def is_empty(self) -> bool:
        return not bool(self._cache)

    def get_size(self) -> int:
        return len(self._cache)

    def get(self, key: str) -> Union[str, None]:
        if key not in self._cache:
            return None
        else:
            self._cache.move_to_end(key)
            return self._cache[key]

    def put(self, key: str, value: str) -> None:
        self.__logger.info('The key = {}, value = {} pair was placed in cache'.format(key, value))
        self._cache[key] = value
        self._cache.move_to_end(key)
        if self.__redis is not None:
            try:
                self.__redis.hset(constants.REDIS_FIELD, key, value)
            except redis.exceptions.ConnectionError:
                pass
        if len(self._cache) > self.capacity:
            del_key, _ = self._cache.popitem(last=False)
            self.__logger.info('Cache is full. Recently deleted item: {}'.format(del_key))
            if self.__redis is not None:
                try:
                    self.__redis.hdel(constants.REDIS_FIELD, del_key)
                except redis.exceptions.ConnectionError:
                    pass

