import asyncio

from PyQt5.QtCore import Qt, QObject
from PyQt5.QtWidgets import QApplication

from sakia.data.entities import Identity
from sakia.decorators import asyncify
from sakia.gui.sub.search_user.controller import SearchUserController
from sakia.gui.sub.user_information.controller import UserInformationController
from sakia.gui.password_asker import PasswordAskerDialog
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
    search_user = attr.ib(default=None)
    user_information = attr.ib(default=None)

    def __attrs_post_init__(self):
        super().__init__()
        self.view.button_box.accepted.connect(self.accept)
        self.view.button_box.rejected.connect(self.reject)
        self.view.combo_pubkey.currentIndexChanged.connect(self.change_connection)

    @classmethod
    def create(cls, parent, app):
        """
        Instanciate a Certification component
        :param sakia.gui.component.controller.ComponentController parent:
        :param sakia.app.Application app: sakia application
        :return: a new Certification controller
        :rtype: CertificationController
        """
        view = CertificationView(parent.view if parent else None, None, None)
        model = CertificationModel(app)
        certification = cls(view, model, None, None)

        search_user = SearchUserController.create(certification, app, "")
        certification.set_search_user(search_user)

        user_information = UserInformationController.create(certification, app, "", None)
        certification.set_user_information(user_information)

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
        if connection:
            dialog.view.combo_pubkey.setCurrentText(connection.title())
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
        dialog.view.combo_pubkey.setCurrentText(connection.title())
        dialog.refresh()
        return await dialog.async_exec()

    def set_search_user(self, search_user):
        """

        :param search_user:
        :return:
        """
        self.search_user = search_user
        self.view.set_search_user(search_user.view)
        search_user.identity_selected.connect(self.refresh_user_information)

    def set_user_information(self, user_information):
        """

        :param user_information:
        :return:
        """
        self.user_information = user_information
        self.view.set_user_information(user_information.view)
        self.user_information.identity_loaded.connect(self.refresh)

    @asyncify
    async def accept(self):
        """
        Validate the dialog
        """
        self.view.button_box.setDisabled(True)
        password = await PasswordAskerDialog(self.model.connection).async_exec()
        if not password:
            self.view.button_box.setEnabled(True)
            return
        QApplication.setOverrideCursor(Qt.WaitCursor)
        result = await self.model.certify_identity(password, self.user_information.model.identity)

        if result[0]:
            QApplication.restoreOverrideCursor()
            await self.view.show_success(self.model.notification())
            self.view.accept()
        else:
            await self.view.show_error(self.model.notification(), result[1])
            QApplication.restoreOverrideCursor()
            self.view.button_box.setEnabled(True)

    def reject(self):
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
                else:
                    self.view.set_button_box(CertificationView.ButtonBoxState.OK)
            else:
                    self.view.set_button_box(CertificationView.ButtonBoxState.NO_MORE_CERTIFICATION)
        else:
            self.view.set_button_box(CertificationView.ButtonBoxState.NOT_A_MEMBER)

    def refresh_user_information(self):
        """
        Refresh user information
        """
        self.user_information.search_identity(self.search_user.model.identity())

    def change_connection(self, index):
        self.model.set_connection(index)
        self.search_user.set_currency(self.model.connection.currency)
        self.user_information.set_currency(self.model.connection.currency)
        self.refresh()

    def async_exec(self):
        future = asyncio.Future()
        self.view.finished.connect(lambda r: future.set_result(r))
        self.view.open()
        self.refresh()
        return future

    def exec(self):
        self.refresh()
        self.view.exec()
