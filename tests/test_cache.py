import pytest

from cache import Cache


def test_cache_base():
    cache = Cache()
    assert cache.is_empty()
    cache.put('foo', 'bar')
    assert not cache.is_empty()


def test_put_get():
    cache = Cache()
    assert cache.is_empty()
    cache.put('foo', 'bar')
    assert cache.get('foo') == 'bar'


def test_capacity(monkeypatch):
    monkeypatch.setattr('constants.CACHE_CAPACITY', 10)
    cache = Cache()
    for i in range(11):
        cache.put('foo' + str(i), 'bar' + str(i))
    assert cache.get_size() == 10
    assert cache.get('foo0') is None


# TODO: Add Redis mock tests