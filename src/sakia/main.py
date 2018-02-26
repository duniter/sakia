import locale
import asyncio
import logging
import signal
import sys
import traceback

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMessageBox

from duniterpy.api.errors import DuniterError
from sakia.helpers import single_instance_lock, cleanup_lock
from quamash import QSelectorEventLoop
from sakia.errors import NoPeerAvailable
from sakia.app import Application
from sakia.gui.dialogs.connection_cfg.controller import ConnectionConfigController
from sakia.gui.main_window.controller import MainWindowController
from sakia.gui.preferences import PreferencesDialog
from sakia.gui.widgets import QAsyncMessageBox



def exit_exception_handler(loop, context):
    """
    An exception handler which prints only on debug (used when exiting)
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

    logging.debug("An unhandled exception occured : {0}".format(message),
                  exc_info=exc_info)


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
        for ignored in ("Unclosed", "socket.gaierror", "[Errno 110]"):
            if ignored in line:
                return

    if exc_info:
        for line in traceback.format_exception(*exc_info):
            for ignored in ("Unclosed", "socket.gaierror", "[Errno 110]"):
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
    mb = QMessageBox(QMessageBox.Critical, "Critical error", """A critical error occured. Select the details to display it.
                  Please report it to <a href='https://github.com/duniter/sakia/issues/new/'>the developers github</a>""",
                     QMessageBox.Ok, QApplication.activeWindow())
    mb.setDetailedText(message)
    mb.setTextFormat(Qt.RichText)

    mb.exec()


def main():
    # activate ctrl-c interrupt
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    sakia = QApplication(sys.argv)

    sys.excepthook = exception_handler

    #sakia.setStyle('Fusion')
    loop = QSelectorEventLoop(sakia)
    loop.set_exception_handler(async_exception_handler)
    #loop.set_debug(True)
    asyncio.set_event_loop(loop)

    with loop:
        app = Application.startup(sys.argv, sakia, loop)

        lock = single_instance_lock(app.currency)
        if not lock:
            lock = single_instance_lock(app.currency)
            if not lock:
                QMessageBox.critical(None, "Sakia",
                                 "Sakia is already running.")

                sys.exit(1)
        app.start_coroutines()
        app.get_last_version()
        keep_trying = True
        while not app.blockchain_service.initialized():
            try:
                box = QMessageBox()
                box.setWindowTitle("Initialization")
                box.setText("Connecting to the network...")
                wFlags = box.windowFlags()
                if Qt.WindowCloseButtonHint == (wFlags & Qt.WindowCloseButtonHint):
                    wFlags = wFlags ^ Qt.WindowCloseButtonHint
                    box.setWindowFlags(wFlags)
                box.show()
                loop.run_until_complete(app.initialize_blockchain())
                box.hide()
            except (DuniterError, NoPeerAvailable) as e:
                reply = QMessageBox.critical(None, "Error", "Error connecting to the network : {:}. Keep Trying ?".format(str(e)),
                                             QMessageBox.Ok | QMessageBox.Abort)
                if reply == QMessageBox.Ok:
                    loop.run_until_complete(PreferencesDialog(app).async_exec())
                else:
                    break
        else:
            if not app.connection_exists():
                conn_controller = ConnectionConfigController.create_connection(None, app)
                loop.run_until_complete(conn_controller.async_exec())
            window = MainWindowController.startup(app)
            loop.run_forever()
        try:
            loop.set_exception_handler(exit_exception_handler)
            loop.run_until_complete(app.stop_current_profile())
            logging.debug("Application stopped")
        except asyncio.CancelledError:
            logging.info('CancelledError')
    logging.debug("Exiting")
    cleanup_lock(lock)
    sys.exit()


if __name__ == '__main__':
    main()
