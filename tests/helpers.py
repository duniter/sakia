from PyQt5.QtWidgets import QApplication, QMessageBox, QDialog, QFileDialog
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest



def click_on_top_message_box_button(button):
    topWidgets = QApplication.topLevelWidgets()
    for w in topWidgets:
        if isinstance(w, QMessageBox):
            QTest.mouseClick(w.button(button), Qt.LeftButton)

def click_on_top_message_box():
    topWidgets = QApplication.topLevelWidgets()
    for w in topWidgets:
        if isinstance(w, QMessageBox):
            QTest.keyClick(w, Qt.Key_Enter)
        elif isinstance(w, QDialog) and w.windowTitle() == "Registration":
            QTest.keyClick(w, Qt.Key_Enter)

def yes_on_top_message_box():
    topWidgets = QApplication.topLevelWidgets()
    for w in topWidgets:
        if isinstance(w, QMessageBox):
            QTest.mouseClick(w.button(QMessageBox.Yes), Qt.LeftButton)


def select_file_dialog(filename):
    topWidgets = QApplication.topLevelWidgets()
    for w in topWidgets:
        if isinstance(w, QFileDialog) and w.isVisible():
            w.hide()
            w.selectFile(filename)
            w.show()
            w.accept()
