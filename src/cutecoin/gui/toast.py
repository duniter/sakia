"""
Created on 1 mai 2015

@author: inso
"""
import sys, time
import logging
from PyQt5.QtCore import Qt, QThread
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtGui import QImage, QPixmap
from ..gen_resources.toast_uic import Ui_Toast

window = None   # global


def display(title, msg):
    logging.debug("NOTIFY DISPLAY")
    if sys.platform == "linux":
        import notify2
        import dbus
        if not notify2.is_initted():
            logging.debug("Initialising notify2")
            notify2.init("cutecoin")
        n = notify2.Notification(title,
                         msg)

# fixme: https://bugs.python.org/issue11587
        # # Not working... Empty icon at the moment.
        # icon = QPixmap(":/icons/cutecoin_logo/").toImage()
        # if icon.isNull():
        #     logging.debug("Error converting logo")
        # else:
        #     icon.convertToFormat(QImage.Format_ARGB32)
        #     icon_bytes = icon.bits().asstring(icon.byteCount())
        #     icon_struct = (
        #         icon.width(),
        #         icon.height(),
        #         icon.bytesPerLine(),
        #         icon.hasAlphaChannel(),
        #         32,
        #         4,
        #         dbus.ByteArray(icon_bytes)
        #         )
        #     n.set_hint('icon_data', icon_struct)
        #     n.set_timeout(5000)
        n.show()
    else:
        _Toast(title, msg)


class _Toast(QMainWindow, Ui_Toast):
    def __init__(self, title, msg):
        global window               # some space outside the local stack
        window = self               # save pointer till killed to avoid GC
        super().__init__()
        rect = QApplication.desktop().availableGeometry()
        height = rect.height()
        width = rect.width()
        self.setWindowFlags(Qt.FramelessWindowHint |Qt.NoDropShadowWindowHint)
        self.setupUi(self)
        x = width - self.width()
        y = height - self.height()
        self.move(x, y)
        self.display.setText("""<h1>{0}</h1>
<p>{1}</p>""".format(title, msg))

        self.toastThread = _ToastThread()    # start thread to remove display
        self.toastThread.finished.connect(self.toastDone)
        self.toastThread.start()
        self.show()

    def toastDone(self):
        global window
        window = None               # kill pointer to window object to close it and GC


class _ToastThread(QThread):
    def __init__(self):
        QThread.__init__(self)

    def run(self):
        time.sleep(2.0)
