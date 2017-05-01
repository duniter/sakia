from PyQt5.QtWidgets import QApplication, QMessageBox, QDialog, QFileDialog
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest



def click_on_top_message_box_button(button):
    topWidgets = QApplication.topLevelWidgets()
    for w in topWidgets:
        if isinstance(w, QMessageBox):
            QTest.mouseClick(w.button(button), Qt.LeftButton)

def accept_dialog(title):
    topWidgets = QApplication.topLevelWidgets()
    for w in topWidgets:
        if isinstance(w, QDialog) and w.windowTitle() == title:
            w.accept()

def select_file_dialog(filename):
    topWidgets = QApplication.topLevelWidgets()
    for w in topWidgets:
        if isinstance(w, QFileDialog) and w.isVisible():
            w.hide()
            w.selectFile(filename)
            w.show()
            w.accept()
