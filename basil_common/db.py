from sqlalchemy import create_engine
from sqlalchemy import exc
from sqlalchemy.orm import scoping
from sqlalchemy.orm import sessionmaker


class SessionManager:
    """Falcon Middleware to manage SQLAlchemy Sessions

    SessionManager starts a new :class:`sqlalchemy.orm.Session` on each
    request and injects that session into the request.context.

    SessionManager then attempts to commit the transaction on any request
    which sets a response status of 201, 202, or 204 and for which the value
    of the 'commit' key in the request.context is set to any True value.

    :param sessionmaker: A configurable :class:`sqlalchemy.orm.Session`
        factory.
    """
    def __init__(self, sessionmaker):
        self._session_source = sessionmaker
        self._is_scoped = isinstance(sessionmaker, scoping.ScopedSession)

    def process_request(self, req, resp):
        req.context['session'] = self._session_source()

    def process_response(self, req, resp, resource):
        session = req.context['session']
        if not self._commit_requested(req) or self._is_failure(resp):
            session.rollback()
        else:
            session.commit()

        if self._is_scoped:
            self._session_source.remove()
        else:
            session.close()

    @staticmethod
    def _commit_requested(req):
        return 'commit' in req.context and req.context['commit']

    @staticmethod
    def _is_failure(resp):
        resp_status = int(resp.status.split(' ', 1)[0])
        return resp_status not in [201, 202, 204]


def prepare_storage(connect_str, conn_timeout, scoped=False):
    engine = prepare_storage_engine(conn_timeout, connect_str)
    return prepare_storage_for_engine(engine, scoped)


def prepare_storage_engine(conn_timeout, connect_str):
    engine = create_engine(connect_str, pool_recycle=conn_timeout)
    return engine


def prepare_storage_for_engine(engine, scoped=False):
    session_maker = sessionmaker(bind=engine)
    if scoped:
        return scoping.scoped_session(session_maker)
    else:
        return session_maker


def rollback_on_exception(app):
    """Falcon Error Handler to Rollback the transaction in a current session.

    The original exception which triggered the error handler will be emitted
    by this error handler after the transaction is rolled back.

    The request.context is expected to contain a session such as created by
    a SessionManager.

    :param app: A Falcon API to add the error handler to.
    :return:
    """
    def rollback_handler(ex, req, resp, params):
        # TODO If rollback fails we hit the default falcon error handler
        req.context['session'].rollback()
        raise

    app.add_error_handler(exc.SQLAlchemyError, rollback_handler)
