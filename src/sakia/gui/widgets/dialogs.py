import sys
from PyQt5.QtWidgets import QMessageBox, QFileDialog
import asyncio


def dialog_async_exec(dialog):
    future = asyncio.Future()
    dialog.finished.connect(lambda r: future.set_result(r))
    dialog.open()
    return future


class QAsyncFileDialog:
    @staticmethod
    async def get_save_filename(parent, title, url, filtr):
        dialog = QFileDialog(parent, title, url, filtr)
        # Fix linux crash if not native QFileDialog is async...
        if sys.platform != 'linux':
            dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        result = await dialog_async_exec(dialog)
        if result == QFileDialog.AcceptSave:
            return dialog.selectedFiles()
        else:
            return []


class QAsyncMessageBox:
    @staticmethod
    def critical(parent, title, label, buttons=QMessageBox.Ok):
        dialog = QMessageBox(QMessageBox.Critical, title, label, buttons, parent)
        return dialog_async_exec(dialog)

    @staticmethod
    def information(parent, title, label, buttons=QMessageBox.Ok):
        dialog = QMessageBox(QMessageBox.Information, title, label, buttons, parent)
        return dialog_async_exec(dialog)

    @staticmethod
    def warning(parent, title, label, buttons=QMessageBox.Ok):
        dialog = QMessageBox(QMessageBox.Warning, title, label, buttons, parent)
        return dialog_async_exec(dialog)

    @staticmethod
    def question(parent, title, label, buttons=QMessageBox.Yes|QMessageBox.No):
        dialog = QMessageBox(QMessageBox.Question, title, label, buttons, parent)
        return dialog_async_exec(dialog)
