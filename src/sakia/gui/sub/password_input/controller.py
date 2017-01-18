import asyncio
from duniterpy.key import SigningKey
from .view import PasswordInputView
from sakia.helpers import detect_non_printable
from sakia.gui.widgets.dialogs import dialog_async_exec
from PyQt5.QtCore import QObject, pyqtSignal, QMetaObject
from PyQt5.QtWidgets import QDialog, QVBoxLayout


class PasswordInputController(QObject):

    """
    A dialog to get password.
    """
    password_changed = pyqtSignal(bool)

    def __init__(self, view, connection):
        """

        :param PasswordInputView view:
        :param sakia.data.entities.Connection connection: a given connection
        """
        super().__init__()
        self.view = view
        self._password = ""
        self.connection = connection
        self.remember = False
        self.set_connection(connection)

    def set_info_visible(self, visible):
        self.view.label_info.setVisible(visible)

    @classmethod
    def create(cls, parent, connection):
        view = PasswordInputView(parent.view if parent else None)
        password_input = cls(view, connection)
        view.edit_password.textChanged.connect(password_input.handle_text_change)
        return password_input

    @classmethod
    async def open_dialog(cls, parent, connection):
        dialog = QDialog(parent.view)
        dialog.setLayout(QVBoxLayout(dialog))
        password_input = cls.create(parent, connection)
        dialog.setWindowTitle(password_input.tr("Please enter your password"))
        dialog.layout().addWidget(password_input.view)
        password_input.view.button_box.accepted.connect(dialog.accept)
        password_input.view.button_box.rejected.connect(dialog.reject)
        password_input.view.setParent(dialog)
        password_input.view.button_box.show()
        result = await dialog_async_exec(dialog)
        if result == QDialog.Accepted:
            return password_input.get_password()
        else:
            return ""

    def valid(self):
        return self._password is not ""

    def handle_text_change(self, password):
        self._password = ""
        if detect_non_printable(password):
            self.view.error(self.tr("Non printable characters in password"))
            self.password_changed.emit(False)
            return

        if SigningKey(self.connection.salt, password, self.connection.scrypt_params).pubkey != self.connection.pubkey:
            self.view.error(self.tr("Wrong password typed. Cannot open the private key"))
            self.password_changed.emit(False)
            return

        self.view.valid()
        self._password = password
        self.password_changed.emit(True)

    def get_password(self):
        if self.view.check_remember.isChecked():
            self.connection.password = self._password
        return self._password

    def set_connection(self, connection):
        if connection:
            self.connection = connection
            self.view.edit_password.setText(connection.password)
