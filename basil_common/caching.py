import json
import threading

import redis


def bootstrap_cache(host='127.0.0.1', password=None):
    pool = redis.ConnectionPool(host=host, password=password)
    return redis.StrictRedis(connection_pool=pool)


def connect_to_cache():
    import os
    cache_host = os.environ['REDIS_HOST']
    cache_password = os.environ.get('REDIS_PASSWORD', None)
    return bootstrap_cache(cache_host, cache_password)


class FactCache(object):
    IS_JSON = '::^JSON^::'

    def __init__(self, redis_conn, prefix, timeout_seconds=3600, loader=None,
                 preload=False):
        self._redis = redis_conn
        self._prefix = prefix
        self.timeout_seconds = timeout_seconds
        self._loader = loader or self.noop
        self._load_lock = threading.BoundedSemaphore()
        if redis_conn and preload:
            self._load_in_background()

    @property
    def is_available(self):
        return self._redis.ping()

    def get(self, key):
        found = self._redis.get(self._prefix + str(key))
        if not found:
            payload = self._load_in_background()
            # TODO figure out the bug here when cache misses
            found = payload[key]
        if isinstance(found, str) and found.startswith(self.IS_JSON):
            found = json.loads(found[10:])
        return found

    def set(self, key, value):
        if not isinstance(value, str):
            value = self.IS_JSON + json.dumps(value)
        return self._redis.setex(name=self._prefix + str(key), value=value,
                                 time=self.timeout_seconds)

    def load(self, payload):
        self._load(payload, locked=False)

    def _load(self, payload, locked):
        try:
            for key in payload:
                self.set(key, payload[key])
        finally:
            if locked:
                self._load_lock.release()

    def _load_in_background(self):
        self._load_lock.acquire()
        payload = self._loader()

        def _load_this():
            self._load(payload, locked=True)

        thread_name = 'FactCache_Loading[%s]' % self._prefix
        self._load_op = threading.Thread(target=_load_this,
                                         name=thread_name)
        self._load_op.start()
        return payload

    @staticmethod
    def noop():
        return {}
