import os

import falcon_support


def verify(required_opts):
    missing = [n for n in required_opts if not os.environ.get(n, None)]
    if len(missing) > 0:
        raise SystemExit('Missing options in environment: %s' % missing)


def root_error_handler():
    if os.environ.get('APP_ENV', 'development') == 'production':
        error_handler = falcon_support.prod_handler
    else:
        error_handler = falcon_support.dev_handler
    return error_handler


def database_connector():
    # in debug mode you might use mysql+pymysql or sqlite
    db_proto = os.environ.get('DB_PROTO', 'mysql')
    db_user = os.environ['DB_USER']
    db_pass = os.environ['DB_PASS']
    db_host = os.environ['DB_HOST']
    db_name = os.environ['DB_NAME']
    return '%s://%s:%s@%s/%s' % (db_proto, db_user, db_pass, db_host, db_name)
