import json

import falcon


class InjectorMiddleware:
    """Injects all arguments into each Falcon session
    """
    def __init__(self, args):
        self._injectables = args

    def process_request(self, req, resp):
        req.context.update(self._injectables)


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
        raise ex

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
        raise ex

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
