import pytest
import asyncio
import quamash
import sqlite3
from duniterpy.documents import BlockUID
from sakia.data.repositories.meta import SakiaDatabase


_application_ = []


@pytest.yield_fixture()
def event_loop():
    qapplication = get_application()
    loop = quamash.QSelectorEventLoop(qapplication)
    exceptions = []
    loop.set_exception_handler(lambda l, c: unitttest_exception_handler(exceptions, l, c))
    yield loop
    try:
        loop.close()
    finally:
        asyncio.set_event_loop(None)

    for exc in exceptions:
        raise exc


@pytest.fixture()
def meta_repo():
    sqlite3.register_adapter(BlockUID, str)
    sqlite3.register_adapter(bool, int)
    sqlite3.register_converter("BOOLEAN", lambda v: bool(int(v)))
    meta_repo = SakiaDatabase(sqlite3.connect(":memory:", detect_types=sqlite3.PARSE_DECLTYPES))
    meta_repo.prepare()
    meta_repo.upgrade_database()
    return meta_repo


def unitttest_exception_handler(exceptions, loop, context):
    """
    An exception handler which exists the program if the exception
    was not catch
    :param loop: the asyncio loop
    :param context: the exception context
    """
    if 'exception' in context:
        exception = context['exception']
    else:
        exception = BaseException(context['message'])
    exceptions.append(exception)


def get_application():
    """Get the singleton QApplication"""
    from quamash import QApplication
    if not len(_application_):
        application = QApplication.instance()
        if not application:
            import sys
            application = QApplication(sys.argv)
        _application_.append( application )
    return _application_[0]

