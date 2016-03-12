import threading

import redis


def bootstrap_cache(host='127.0.0.1', password=None):
    pool = redis.ConnectionPool(host=host, password=password)
    return redis.StrictRedis(connection_pool=pool)

ENGINE = None


class FactCache(object):

    def __init__(self, redis_conn, prefix, timeout_seconds=3600, loader=None):
        self._redis = redis_conn
        self._prefix = prefix
        self.timeout_seconds = timeout_seconds
        self._loader = loader or self.noop
        self._load_lock = threading.BoundedSemaphore()
        self._load_in_background()

    @property
    def is_available(self):
        return self._redis.ping()

    def get(self, key):
        found = self._redis.get(self._prefix + key)
        if not found:
            payload = self._load_in_background()
            found = payload[key]
        return found

    def set(self, key, value):
        return self._redis.setex(name=self._prefix + key, value=value,
                                 time=self.timeout_seconds)

    def load(self, payload):
        self._load(payload, locked=False)

    def _load(self, payload, locked):
        for key in payload:
            self.set(key, payload[key])
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
