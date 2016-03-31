import time

import basil_common.caching as caching
import pytest

from tests import *


def test_is_available(engine, loader):
    fact_cache = _cache(engine, loader)
    cache = fact_cache
    assert_that(cache.is_available, equal_to(True))


def test_get_miss(engine, loader):
    cache = caching.FactCache(engine, 'test', loader=loader, preload=True)
    wait_for(cache)
    assert_that(cache.get('miss'), none())


def test_get_hit(engine, loader):
    cache = caching.FactCache(engine, 'test', loader=loader, preload=True)
    wait_for(cache)
    assert_that(cache.get('hit'), equal_to(True))


def test_get_list(engine, loader):
    cache = caching.FactCache(engine, 'test', loader=loader, preload=True)
    wait_for(cache)
    assert_that(cache.get('list'), equal_to([1, 2, 3]))


def test_get_dict(engine, loader):
    cache = caching.FactCache(engine, 'test', loader=loader, preload=True)
    wait_for(cache)
    assert_that(cache.get('dict'), equal_to({'foo': 'bar'}))


def test_without_preload(engine, loader):
    cache = caching.FactCache(engine, 'test', loader=loader, preload=False)
    # Check the engine with the compound key, expecting None
    assert_that(engine.get('testempty'), none())
    # On get, the data is loaded in background, key returned immediately
    assert_that(cache.get('empty'), equal_to(False))

    wait_for(cache)
    assert_that(engine.get('testhit'), not_none())


def test_with_preload(engine, loader):
    cache = caching.FactCache(engine, 'test', loader=loader, preload=True)
    wait_for(cache)
    assert_that(engine.get('testhit'), not_none())


def wait_for(cache):
    while cache.is_loading:
        time.sleep(0.01)  # 10 ms


def _cache(engine, loader, preload=True):
    return caching.FactCache(engine, 'test', loader=loader, preload=preload)


@pytest.fixture(scope="function")
def engine():
    cache = caching.connect_to_cache()
    cache.flushdb()
    return cache


@pytest.fixture(scope="module")
def loader():
    def loads():
            return {'hit': True, 'empty': False, 'list': [1, 2, 3],
                    'dict': {'foo': 'bar'}}
    return loads
