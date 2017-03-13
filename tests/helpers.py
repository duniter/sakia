from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest


def click_on_top_message_box():
    topWidgets = QApplication.topLevelWidgets()
    for w in topWidgets:
        if type(w) is QMessageBox:
            QTest.keyClick(w, Qt.Key_Enter)
