import asyncio

from PyQt5.QtCore import Qt, QObject
from PyQt5.QtWidgets import QApplication

from sakia.decorators import asyncify
from sakia.gui.sub.search_user.controller import SearchUserController
from sakia.gui.sub.user_information.controller import UserInformationController
from sakia.gui.sub.password_input import PasswordInputController
from .model import CertificationModel
from .view import CertificationView
import attr


@attr.s()
class CertificationController(QObject):
    """
    The Certification view
    """

    view = attr.ib()
    model = attr.ib()
    search_user = attr.ib()
    user_information = attr.ib()
    password_input = attr.ib()

    def __attrs_post_init__(self):
        super().__init__()
        self.view.button_box.accepted.connect(self.accept)
        self.view.button_box.rejected.connect(self.reject)
        self.view.combo_connection.currentIndexChanged.connect(self.change_connection)

    @classmethod
    def create(cls, parent, app):
        """
        Instanciate a Certification component
        :param sakia.gui.component.controller.ComponentController parent:
        :param sakia.app.Application app: sakia application
        :return: a new Certification controller
        :rtype: CertificationController
        """

        search_user = SearchUserController.create(None, app)
        user_information = UserInformationController.create(None, app, None)
        password_input = PasswordInputController.create(None, None)

        view = CertificationView(parent.view if parent else None, search_user.view, user_information.view,
                                 password_input.view)
        model = CertificationModel(app)
        certification = cls(view, model, search_user, user_information, password_input)
        search_user.identity_selected.connect(certification.refresh_user_information)
        password_input.password_changed.connect(certification.refresh)

        user_information.identity_loaded.connect(certification.refresh)

        view.set_keys(certification.model.available_connections())
        return certification

    @classmethod
    def open_dialog(cls, parent, app, connection):
        """
        Certify and identity
        :param sakia.gui.component.controller.ComponentController parent: the parent
        :param sakia.core.Application app: the application
        :param sakia.core.Account account: the account certifying the identity
        :param sakia.core.Community community: the community
        :return:
        """
        dialog = cls.create(parent, app)
        dialog.set_connection(connection)
        dialog.refresh()
        return dialog.exec()

    @classmethod
    async def certify_identity(cls, parent, app, connection, identity):
        """
        Certify and identity
        :param sakia.gui.component.controller.ComponentController parent: the parent
        :param sakia.core.Application app: the application
        :param sakia.data.entities.Connection connection: the connection
        :param sakia.data.entities.Identity identity: the identity certified
        :return:
        """
        dialog = cls.create(parent, app)
        dialog.view.combo_connection.setCurrentText(connection.title())
        dialog.user_information.change_identity(identity)
        dialog.refresh()
        return await dialog.async_exec()

    def change_connection(self, index):
        self.model.set_connection(index)
        self.password_input.set_connection(self.model.connection)
        self.refresh()

    def set_connection(self, connection):
        if connection:
            self.view.combo_connection.setCurrentText(connection.title())
            self.password_input.set_connection(connection)

    @asyncify
    async def accept(self):
        """
        Validate the dialog
        """
        self.view.button_box.setDisabled(True)
        secret_key, password = self.password_input.get_salt_password()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        result = await self.model.certify_identity(secret_key, password, self.user_information.model.identity)

        if result[0]:
            QApplication.restoreOverrideCursor()
            await self.view.show_success(self.model.notification())
            self.view.accept()
        else:
            await self.view.show_error(self.model.notification(), result[1])
            QApplication.restoreOverrideCursor()
            self.view.button_box.setEnabled(True)

    @asyncify
    async def reject(self):
        self.view.reject()

    def refresh(self):
        stock = self.model.get_cert_stock()
        written, pending = self.model.nb_certifications()
        days, hours, minutes, seconds = self.model.remaining_time()
        self.view.display_cert_stock(written, pending, stock, days, hours, minutes)

        if self.model.could_certify():
            if written < stock or stock == 0:
                if not self.user_information.model.identity:
                    self.view.set_button_box(CertificationView.ButtonBoxState.SELECT_IDENTITY)
                elif days+hours+minutes > 0:
                    if days > 0:
                        remaining_localized = self.tr("{days} days").format(days=days)
                    else:
                        remaining_localized = self.tr("{hours}h {min}min").format(hours=hours, min=minutes)
                    self.view.set_button_box(CertificationView.ButtonBoxState.REMAINING_TIME_BEFORE_VALIDATION,
                                             remaining=remaining_localized)
                elif self.password_input.valid():
                    self.view.set_button_box(CertificationView.ButtonBoxState.OK)
                else:
                    self.view.set_button_box(CertificationView.ButtonBoxState.WRONG_PASSWORD)
            else:
                    self.view.set_button_box(CertificationView.ButtonBoxState.NO_MORE_CERTIFICATION)
        else:
            self.view.set_button_box(CertificationView.ButtonBoxState.NOT_A_MEMBER)

    def refresh_user_information(self):
        """
        Refresh user information
        """
        self.user_information.search_identity(self.search_user.model.identity())

    def async_exec(self):
        future = asyncio.Future()
        self.view.finished.connect(lambda r: future.set_result(r))
        self.view.open()
        self.refresh()
        return future

    def exec(self):
        self.refresh()
        self.view.exec()
