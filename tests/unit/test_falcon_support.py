import datetime
import mock

import falcon

from basil_common import falcon_support
from tests import *


def test_is_error_false():
    from basil_common.falcon_support import is_error as is_error
    assert_that(is_error(falcon.HTTP_200), is_not(True))
    assert_that(is_error(falcon.HTTP_201), is_not(True))
    assert_that(is_error(falcon.HTTP_204), is_not(True))
    assert_that(is_error(falcon.HTTP_301), is_not(True))
    assert_that(is_error(falcon.HTTP_302), is_not(True))


def test_is_error_true():
    from basil_common.falcon_support import is_error as is_error
    assert_that(is_error(falcon.HTTP_400), is_(True))
    assert_that(is_error(falcon.HTTP_401), is_(True))
    assert_that(is_error(falcon.HTTP_403), is_(True))
    assert_that(is_error(falcon.HTTP_404), is_(True))
    assert_that(is_error(falcon.HTTP_405), is_(True))
    assert_that(is_error(falcon.HTTP_406), is_(True))
    assert_that(is_error(falcon.HTTP_409), is_(True))
    assert_that(is_error(falcon.HTTP_410), is_(True))
    assert_that(is_error(falcon.HTTP_500), is_(True))
    assert_that(is_error(falcon.HTTP_503), is_(True))


def test_is_cacheable_true():
    from basil_common.falcon_support import is_cacheable as is_cacheable
    assert_that(is_cacheable(falcon.HTTP_200), is_(True))
    assert_that(is_cacheable(falcon.HTTP_301), is_(True))
    assert_that(is_cacheable(falcon.HTTP_410), is_(True))


def test_is_cacheable_false():
    from basil_common.falcon_support import is_cacheable as is_cacheable
    assert_that(is_cacheable(falcon.HTTP_201), is_not(True))
    assert_that(is_cacheable(falcon.HTTP_204), is_not(True))
    assert_that(is_cacheable(falcon.HTTP_302), is_not(True))
    assert_that(is_cacheable(falcon.HTTP_400), is_not(True))
    assert_that(is_cacheable(falcon.HTTP_401), is_not(True))
    assert_that(is_cacheable(falcon.HTTP_403), is_not(True))
    assert_that(is_cacheable(falcon.HTTP_404), is_not(True))
    assert_that(is_cacheable(falcon.HTTP_405), is_not(True))
    assert_that(is_cacheable(falcon.HTTP_406), is_not(True))
    assert_that(is_cacheable(falcon.HTTP_409), is_not(True))
    assert_that(is_cacheable(falcon.HTTP_500), is_not(True))
    assert_that(is_cacheable(falcon.HTTP_503), is_not(True))


def test_respond_get():
    # a GET request
    get_resp = mock.Mock()
    falcon_support.respond(get_resp, body="Expected")
    assert_that(get_resp.body, equal_to("Expected"))
    assert_that(get_resp.status, equal_to(falcon.HTTP_OK))


def test_respond_head():
    # a HEAD request blocks body publishing
    head_resp = mock.Mock()
    falcon_support.respond(head_resp, method='HEAD', body="Not Expected")
    head_resp.body.assert_not_called()
    assert_that(head_resp.status, equal_to(falcon.HTTP_OK))


def test_respond_204():
    # a 204 response status blocks body publishing
    no_content_resp = mock.Mock()
    falcon_support.respond(no_content_resp, status=falcon.HTTP_NO_CONTENT)
    no_content_resp.body.assert_not_called()
    assert_that(no_content_resp.status, equal_to(falcon.HTTP_NO_CONTENT))


def test_respond_304():
    # a 304 response status blocks body publishing
    not_modified_resp = mock.Mock()
    falcon_support.respond(not_modified_resp, status=falcon.HTTP_NOT_MODIFIED)
    not_modified_resp.body.assert_not_called()
    assert_that(not_modified_resp.status, equal_to(falcon.HTTP_NOT_MODIFIED))


def test_respond_201():
    # a 201 response with additional response headers
    created_resp = mock.Mock()
    headers = {'Foo': '1', 'Bar': '2'}
    falcon_support.respond(created_resp, status=falcon.HTTP_CREATED,
                           headers=headers, body="Expected")
    assert_that(created_resp.body, equal_to("Expected"))
    assert_that(created_resp.set_header.call_count, equal_to(2))
    assert_that(created_resp.status, equal_to(falcon.HTTP_CREATED))


def test_respond_a():
    pass
#  and other tests


@mock.patch.object(datetime, 'datetime', mock.Mock(wraps=datetime.datetime))
def test_cache_control_middleware_sets_headers_by_status():
    expected_date = 'Tue, 15 Nov 1994 12:45:26 GMT'
    now = datetime.datetime(1994, 11, 15, 11, 45, 26, 0,
                            falcon.util.TimezoneGMT())
    datetime.datetime.utcnow.return_value = now

    ccm = falcon_support.CacheControlMiddleware()
    req = mock.Mock()
    req.context.get.return_value = False
    resp = mock.Mock()
    resp.body = "!"

    with mock.patch('basil_common.falcon_support.is_cacheable') as key:
        key.return_value = True
        ccm.process_response(req, resp, None)

    assert_that(resp.cache_control, equal_to(['public', 'max-age=3600']))
    assert_that(resp.vary, equal_to('Accept-Encoding'))
    resp.set_header.assert_called_once_with('Expires', expected_date)


@mock.patch.object(datetime, 'datetime', mock.Mock(wraps=datetime.datetime))
def test_cache_control_middleware_sets_headers_by_context():
    expected_date = 'Tue, 15 Nov 1994 12:45:26 GMT'
    now = datetime.datetime(1994, 11, 15, 11, 45, 26, 0,
                            falcon.util.TimezoneGMT())
    datetime.datetime.utcnow.return_value = now

    ccm = falcon_support.CacheControlMiddleware()
    req = mock.Mock()
    req.context.get.return_value = falcon_support.USE_CACHE_CONTROL
    resp = mock.Mock()
    resp.status.return_value = falcon.HTTP_503

    ccm.process_response(req, resp, None)

    assert_that(resp.cache_control, equal_to(['public', 'max-age=3600']))
    assert_that(resp.vary, equal_to('Accept-Encoding'))
    resp.set_header.assert_called_once_with('Expires', expected_date)


def test_cache_control_middleware_uncachable_status():
    ccm = falcon_support.CacheControlMiddleware()
    req = mock.Mock()
    req.context.get.return_value = None
    resp = mock.MagicMock()
    resp.status.return_value = falcon.HTTP_503

    ccm.process_response(req, resp, None)

    assert_that(resp.cache_control, is_not(['public', 'max-age=3600']))
    assert_that(resp.vary, is_not('Accept-Encoding'))
    resp.set_header.assert_not_called()


def test_etag_middleware_sets_headers_by_status_no_cache_update():
    expected_tag = falcon_support.EtagResponseMiddleware.etag('ERROR!!')
    cache = mock.MagicMock()
    cache.__getitem__.return_value = expected_tag
    erm = falcon_support.EtagResponseMiddleware(cache)
    req = mock.Mock()
    req.relative_uri = '/some/url'
    resp = mock.Mock()
    resp.status.return_value = falcon.HTTP_200
    resp.body = 'ERROR!!'

    erm.process_response(req, resp, None)

    assert_that(resp.etag, equal_to(expected_tag))
    cache.__setitem__.assert_not_called()


def test_etag_middleware_sets_headers_by_context_update_cache():
    cache = mock.MagicMock()
    cache.get.return_value = None
    erm = falcon_support.EtagResponseMiddleware(cache)
    req = mock.Mock()
    req.relative_uri = '/some/url'
    req.context.get.return_value = falcon_support.USE_ETAG
    resp = mock.MagicMock()
    resp.status.return_value = falcon.HTTP_503
    resp.body = 'ERROR!!'

    erm.process_response(req, resp, None)

    expected_tag = falcon_support.EtagResponseMiddleware.etag('ERROR!!')
    assert_that(resp.etag, equal_to(expected_tag))
    cache.__setitem__.assert_called_once_with('/some/url', expected_tag)


def test_etag_middleware_uncachable_status():
    erm = falcon_support.EtagResponseMiddleware(None)
    req = mock.Mock()
    req.relative_uri = '/some/url'
    req.context.get.return_value = None
    resp = mock.MagicMock()
    resp.status.return_value = falcon.HTTP_503
    resp.body = 'ERROR!!'

    erm.process_response(req, resp, None)

    assert_that(resp.etag, has_length(0))
    resp.set_header.assert_not_called()
