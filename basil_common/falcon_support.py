import datetime
import hashlib
import json

import falcon


USE_CACHE_CONTROL = 'USE_CACHE_CONTROL'
USE_ETAG = 'USE_ETAG'


def is_error(status):
    """Determine if the response has an error status

    :param status: HTTP Status string to inspect
    :return: True if the status code is 400 or greater, otherwise False
    """
    return int(status.split(' ', 1)[0]) >= 400


def is_cacheable(status):
    """Determine if the response has a cacheable status

    :param status: HTTP Status string to inspect
    :return: True if the status code is 302 or greater and not 410, otherwise
     False
    """
    code = int(status.split(' ', 1)[0])
    return code in [200, 203, 206, 300, 301, 410]


def respond(resp, method='GET', status=falcon.HTTP_200, headers=None, body=None):
    resp.status = status
    if headers:
        for key, value in headers.iteritems():
            resp.set_header(key, value)
    if status not in [falcon.HTTP_204, falcon.HTTP_304]:
        if method != 'HEAD':
            resp.body = body
    # else MUST not include body in any other cases


def prod_handler(ex, req, resp, params):
    """Handle exceptions thrown during request processing

    :param ex: exception to optionally handle
    :param req: request being processed
    :param resp: response being formulated
    :param params: parameters to the request
    :return: None
    """
    # Pass on any HTTP Error that has already been determined
    if isinstance(ex, falcon.HTTPError):
        raise

    raise falcon.HTTPInternalServerError("500 Internal Server Error",
                                         "Sorry. My bad.")


def dev_handler(ex, req, resp, params):
    """Handle exceptions thrown during request processing

    :param ex: exception to optionally handle
    :param req: request being processed
    :param resp: response being formulated
    :param params: parameters to the request
    :return: None
    """
    # Pass on any HTTP Error that has already been determined
    if isinstance(ex, falcon.HTTPError):
        raise

    resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR

    import traceback
    trace = traceback.format_exc()

    if req.client_accepts('text/html'):
        resp.content_type = 'text/html'
        content = ('<!DOCTYPE html><h2>%s</h2>%s<hr><pre>%s</pre>'
                   % (resp.status, ex.message, trace))
    else:
        error = {'status': resp.status, 'message': ex.message,
                 'description': trace.split('\n')}
        content = json.dumps(error)
    resp.body = content


class InjectorMiddleware(object):
    """Injects all arguments into each Falcon session
    """
    def __init__(self, args):
        self._injectables = args

    def process_request(self, req, resp):
        req.context.update(self._injectables)


class CacheControlMiddleware(object):
    def __init__(self, duration_seconds=3600):
        self.duration_seconds = duration_seconds

    def process_response(self, req, resp, resource):
        if self._include_cache_control_headers(req, resp):
            resp.cache_control = ['public', 'max-age=' + self.cache_seconds]
            resp.set_header('Expires', self.expires)
            resp.vary = 'Accept-Encoding'

    @property
    def cache_seconds(self):
        return str(self.duration_seconds)

    @property
    def expires(self):
        now = datetime.datetime.utcnow()
        duration = datetime.timedelta(seconds=self.duration_seconds)
        return falcon.dt_to_http(now + duration)

    @staticmethod
    def _include_cache_control_headers(req, resp):
        return resp.body and (req.context.get(USE_CACHE_CONTROL, None) or
                              is_cacheable(resp.status))


class EtagResponseMiddleware(object):
    def __init__(self, cache):
        self._cache = cache

    def process_response(self, req, resp, resource):
        if self._include_etag_header(req, resp):
            etag = self.etag(resp.body)
            resp.etag = etag

            # Ensure current Etag is cached
            req_key = req.relative_uri
            if self._cache[req_key] != etag:
                self._cache[req_key] = etag

    @staticmethod
    def etag(body):
        return hashlib.md5(body).hexdigest()

    @staticmethod
    def _include_etag_header(req, resp):
        return resp.body and (req.context.get(USE_ETAG, None) or
                              is_cacheable(resp.status))
