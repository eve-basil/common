import basil_common.caching as caching
import time

from tests import *


class TestFactCache(object):
    def test_get_hit_causes_no_load(self, mocker):
        with mocker.patch('redis.StrictRedis') as engine:
            cache = self._cache_with_mock_engine(engine)
            engine.get.return_value = 'hit'
            self._wait_until_loaded(cache)
            engine.reset_mock()
            assert_that(cache.get('7'), equal_to('hit'))
            assert_that(engine.setex.call_count, equal_to(0))

    def test_get_miss_causes_load(self, mocker):
        with mocker.patch('redis.StrictRedis') as engine:
            cache = self._cache_with_mock_engine(engine)
            engine.get.return_value = None
            self._wait_until_loaded(cache)
            engine.reset_mock()
            # Cache returns data from the loader, so we don't have to wait
            assert_that(cache.get('7'), equal_to('is 7'))
            # Meanwhile the background loading is still running
            self._wait_until_loaded(cache)
            assert_that(engine.setex.call_count, equal_to(20))

    def test_set(self, mocker):
        with mocker.patch('redis.StrictRedis') as engine:
            cache = self._cache_with_mock_engine(engine, preload=False)
            cache.set('7', 'is set')
            assert_that(engine.setex.call_count, equal_to(1))
            engine.setex.assert_called_once_with('test_7', 3600, 'is set')

    def test_load(self, mocker):
        with mocker.patch('redis.StrictRedis') as engine:
            cache = self._cache_with_mock_engine(engine, preload=False)
            cache.load({str(n): ' == ' + str(n) for n in range(0, 10)})
            assert_that(engine.setex.call_count, equal_to(10))

    @staticmethod
    def _cache_with_mock_engine(engine, preload=True):
        def loads():
            return {str(n): 'is ' + str(n) for n in range(0, 20)}
        cache = caching.FactCache(engine, prefix='test_', loader=loads,
                                  preload=preload)
        return cache

    @staticmethod
    def _wait_until_loaded(cache):
        while cache.is_loading:
            time.sleep(0.01)  # 10 ms
