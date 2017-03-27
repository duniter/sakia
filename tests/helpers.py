from PyQt5.QtWidgets import QApplication, QMessageBox, QDialog
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest


def click_on_top_message_box():
    topWidgets = QApplication.topLevelWidgets()
    for w in topWidgets:
        if isinstance(w, QMessageBox):
            QTest.keyClick(w, Qt.Key_Enter)
        elif isinstance(w, QDialog) and w.windowTitle() == "Registration":
            QTest.keyClick(w, Qt.Key_Enter)
