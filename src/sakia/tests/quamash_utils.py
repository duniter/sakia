import asyncio
import quamash
import socket
from aiohttp import web, log

_application_ = []


class QuamashTest:
    def setUpQuamash(self):
        self.qapplication = get_application()
        self.lp = quamash.QEventLoop(self.qapplication)
        asyncio.set_event_loop(self.lp)
        self.lp.set_exception_handler(lambda l, c: unitttest_exception_handler(self, l, c))
        self.exceptions = []
        self.handler = None

    def tearDownQuamash(self):
        try:
            self.lp.close()
        finally:
            asyncio.set_event_loop(None)

        for exc in self.exceptions:
            raise exc


def unitttest_exception_handler(test, loop, context):
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
    test.exceptions.append(exception)


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

