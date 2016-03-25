import basil_common.caching as caching

from tests import *


class TestFactCache(object):
    def test_loads_on_create(self, mocker):
        cache, engine = self._cache_with_mock_engine(mocker)
        self._wait_until_loaded(cache)
        assert_that(engine.setex.call_count, equal_to(20))
        engine.reset_mock()

    def test_is_available(self, mocker):
        cache, engine = self._cache_with_mock_engine(mocker)
        engine.ping.return_value = True
        self._wait_until_loaded(cache)
        assert_that(cache, has_property('is_available', equal_to(True)))
        assert_that(engine.ping.called, equal_to(True))
        engine.reset_mock()

    def test_get_hit_causes_no_load(self, mocker):
        cache, engine = self._cache_with_mock_engine(mocker)
        engine.get.return_value = 'hit'
        self._wait_until_loaded(cache)
        engine.reset_mock()
        assert_that(cache.get('7'), equal_to('hit'))
        assert_that(engine.setex.call_count, equal_to(0))

    def test_get_miss_causes_load(self, mocker):
        cache, engine = self._cache_with_mock_engine(mocker)
        engine.get.return_value = None
        self._wait_until_loaded(cache)
        engine.reset_mock()
        assert_that(cache.get('7'), equal_to('is 7'))
        assert_that(engine.setex.call_count, equal_to(20))

    def test_set(self, mocker):
        cache, engine = self._cache_with_mock_engine(mocker)
        self._wait_until_loaded(cache)
        engine.reset_mock()
        cache.set('7', 'is set')
        assert_that(engine.setex.call_count, equal_to(1))
        engine.setex.assert_called_with(name='test7', value='is set',
                                        time=3600)

    def test_load(self, mocker):
        cache, engine = self._cache_with_mock_engine(mocker)
        self._wait_until_loaded(cache)
        engine.reset_mock()
        cache.load({str(n): ' == ' + str(n) for n in range(0, 10)})
        assert_that(engine.setex.call_count, equal_to(10))

    @staticmethod
    def _cache_with_mock_engine(mocker):
        def loads():
            return {str(n): 'is ' + str(n) for n in range(0, 20)}
        engine = mocker.patch('redis.StrictRedis')
        cache = caching.FactCache(engine, prefix='test', loader=loads)
        return cache, engine

    @staticmethod
    def _wait_until_loaded(cache):
        # wait for loading to be complete
        with cache._load_lock:
            pass
