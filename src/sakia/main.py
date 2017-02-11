import asyncio
import logging
import signal
import sys
import traceback

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMessageBox

from sakia.helpers import single_instance_lock, cleanup_lock
from quamash import QSelectorEventLoop
from sakia.app import Application
from sakia.gui.dialogs.connection_cfg.controller import ConnectionConfigController
from sakia.gui.main_window.controller import MainWindowController


def async_exception_handler(loop, context):
    """
    An exception handler which exits the program if the exception
    was not catch
    :param loop: the asyncio loop
    :param context: the exception context
    """
    logging.debug('Exception handler executing')
    message = context.get('message')
    if not message:
        message = 'Unhandled exception in event loop'

    try:
        exception = context['exception']
    except KeyError:
        exc_info = False
    else:
        exc_info = (type(exception), exception, exception.__traceback__)

    log_lines = [message]
    for key in [k for k in sorted(context) if k not in {'message', 'exception'}]:
        log_lines.append('{}: {!r}'.format(key, context[key]))

    logging.error('\n'.join(log_lines), exc_info=exc_info)
    for line in log_lines:
        for ignored in ("Unclosed", "socket.gaierror"):
            if ignored in line:
                return

    if exc_info:
        for line in traceback.format_exception(*exc_info):
            for ignored in ("Unclosed", "socket.gaierror"):
                if ignored in line:
                    return
    exception_message(log_lines, exc_info)


def exception_handler(*exc_info):
    logging.error("An unhandled exception occured",
                  exc_info=exc_info)
    exception_message(["An unhandled exception occured"], exc_info)


def exception_message(log_lines, exc_info):
    stacktrace = traceback.format_exception(*exc_info) if exc_info else ""
    message = """
    {log_lines}

    ----
    {stacktrace}
    """.format(log_lines='\n'.join(log_lines), stacktrace='\n'.join(stacktrace))
    mb = QMessageBox(QMessageBox.Critical, "Critical error",
                    """A critical error occured. Select the details to display it.
                    Please report it to <a href='https://github.com/duniter/sakia/issues/new'>the developers github</a>""",
                     QMessageBox.Ok, QApplication.activeWindow())
    mb.setDetailedText(message)
    mb.setTextFormat(Qt.RichText)

    mb.setTextInteractionFlags(Qt.TextSelectableByMouse)
    mb.exec()

if __name__ == '__main__':
    # activate ctrl-c interrupt
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    sakia = QApplication(sys.argv)

    lock = single_instance_lock()
    if not lock:
        QMessageBox.critical(None, "Sakia is already running", "Sakia is already running.")
        sys.exit(1)

    sys.excepthook = exception_handler

    sakia.setStyle('Fusion')
    loop = QSelectorEventLoop(sakia)
    loop.set_exception_handler(async_exception_handler)
    asyncio.set_event_loop(loop)

    with loop:
        app = Application.startup(sys.argv, sakia, loop)
        app.start_coroutines()
        if not app.connection_exists():
            conn_controller = ConnectionConfigController.create_connection(None, app)
            loop.run_until_complete(conn_controller.async_exec())
        window = MainWindowController.startup(app)
        loop.run_forever()
        try:
            loop.set_exception_handler(None)
            loop.run_until_complete(app.stop_current_profile())
            logging.debug("Application stopped")
        except asyncio.CancelledError:
            logging.info('CancelledError')
    logging.debug("Exiting")
    cleanup_lock(lock)
    sys.exit()

