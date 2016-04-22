import json
import logging
import threading

import redis
import time


LOG = logging.getLogger(__name__)


def bootstrap_cache(host='127.0.0.1', password=None):
    pool = redis.ConnectionPool(host=host, password=password)
    return redis.StrictRedis(connection_pool=pool)


def connect_to_cache():
    import os
    cache_host = os.environ['REDIS_HOST']
    cache_password = os.environ.get('REDIS_PASSWORD', None)
    return bootstrap_cache(cache_host, cache_password)


class FactCache(object):
    IS_JSON = 'JSON::'

    def __init__(self, redis_conn, prefix, timeout_seconds=3600, loader=None,
                 preload=False, debug=False):
        self._redis = redis_conn
        self._prefix = prefix
        self.timeout_seconds = timeout_seconds
        self._loader = loader or self.noop
        self._load_op = None
        self._loading_lock = threading.BoundedSemaphore()
        self._debug = debug

        if redis_conn and preload:
            self.get('')

    @property
    def is_available(self):
        return self._redis.ping()

    @property
    def is_loading(self):
        acquired_lock = False
        try:
            acquired_lock = self._loading_lock.acquire(blocking=False)
            return not acquired_lock or (self._is_load_op_alive())
        finally:
            if acquired_lock:
                self._loading_lock.release()

    def __setitem__(self, key, value):
        self.set(key, value)

    def set(self, key, value):
        cache_key = self._compound_key(key)
        value = self._pickle(value)
        return self._redis.setex(cache_key, self.timeout_seconds, value)

    def load(self, payload):
        self._load(payload)

    def get(self, key, blocking=False):
        compound_key = self._compound_key(key)
        found = self._redis.get(compound_key)
        if found:
            if self._debug:
                LOG.info('Cache Hit [%s] for key [%s]', self._prefix, key)
            return self._unpickle(found)

        if self._debug:
            LOG.info('Cache Miss [%s] for key [%s]', self._prefix, key)
        found = self._locked_get(key)

        if blocking:
            self._wait_for_loading_op()
            return self.get(key)
        else:
            return found

    def __getitem__(self, item):
        return self.get(item)

    def _compound_key(self, key):
        return self._prefix + str(key)

    def _locked_get(self, key):
        with self._loading_lock:
            self._wait_for_loading_op()

            # Try one more time to find the key in the cache
            compound_key = self._compound_key(key)
            found = self._redis.get(compound_key)
            if found:
                return self._unpickle(found)

            # Load the data and send to the cache
            payload = self._loader()

            def _load_this():
                self._load(payload)

            named = 'FactCache_Loading[%s]' % self._prefix
            self._load_op = threading.Thread(target=_load_this, name=named)
            self._load_op.start()

        # TODO figure out the bug here when payload does not include
        #   the key but it still ends up in the cache somehow
        return payload.get(key, None)

    def _wait_for_loading_op(self):
        if self._is_load_op_alive():
            while self._load_op.is_alive():
                time.sleep(0.01)  # 10ms

    def _is_load_op_alive(self):
        return self._load_op and self._load_op.is_alive()

    def _load(self, payload):
        for key in payload:
            self.set(key, payload[key])

    def _pickle(self, value):
        if not isinstance(value, str):
            value = self.IS_JSON + json.dumps(value)
        return value

    def _unpickle(self, found):
        if isinstance(found, str) and found.startswith(self.IS_JSON):
            found = json.loads(found[6:])
        return found

    @staticmethod
    def noop():
        return {}
