import asyncio

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from sakia.decorators import asyncify, once_at_a_time
from sakia.gui.component.controller import ComponentController
from sakia.gui.sub.search_user.controller import SearchUserController
from sakia.gui.sub.user_information.controller import UserInformationController
from .model import CertificationModel
from .view import CertificationView


class CertificationController(ComponentController):
    """
    The Certification view
    """

    def __init__(self, parent, view, model, search_user, user_information):
        """
        Constructor of the Certification component

        :param sakia.gui.certification.view.CertificationView: the view
        :param sakia.gui.certification.model.CertificationModel model: the model
        :param sakia.gui.search_user.controller.SearchUserController search_user: the search user component
        :param sakia.gui.user_information.controller.UserInformationController search_user: the search user component
        """
        super().__init__(parent, view, model)
        self.view.button_box.accepted.connect(self.accept)
        self.view.button_box.rejected.connect(self.reject)
        self.view.combo_community.currentIndexChanged.connect(self.change_current_community)
        self.search_user = search_user
        self.user_information = user_information

    @classmethod
    def create(cls, parent, app, **kwargs):
        """
        Instanciate a Certification component
        :param sakia.gui.component.controller.ComponentController parent:
        :param sakia.app.Application app: sakia application
        :return: a new Certification controller
        :rtype: CertificationController
        """

        view = CertificationView(parent.view, None, None, communities_names, contacts_names)
        model = CertificationModel(None, app, account, community)
        certification = cls(parent, view, model, None, None)

        search_user = SearchUserController.create(certification, app,
                                                  account=model.account,
                                                  community=model.community)
        certification.set_search_user(search_user)

        user_information = UserInformationController.create(certification, app,
                                                            account=model.account,
                                                            community=model.community,
                                                            identity=None)
        certification.set_user_information(user_information)
        model.setParent(certification)
        return certification

    @classmethod
    def open_dialog(cls, parent, app, account, community, password_asker):
        """
        Certify and identity
        :param sakia.gui.component.controller.ComponentController parent: the parent
        :param sakia.core.Application app: the application
        :param sakia.core.Account account: the account certifying the identity
        :param sakia.core.Community community: the community
        :param sakia.gui.password_asker.PasswordAsker password_asker: the password asker
        :return:
        """
        dialog = cls.create(parent, app, account=account, community=community, password_asker=password_asker)
        if community:
            dialog.view.combo_community.setCurrentText(community.name)
        dialog.refresh()
        return dialog.exec()

    @classmethod
    async def certify_identity(cls, parent, app, account, password_asker, community, identity):
        """
        Certify and identity
        :param sakia.gui.component.controller.ComponentController parent: the parent
        :param sakia.core.Application app: the application
        :param sakia.core.Account account: the account certifying the identity
        :param sakia.gui.password_asker.PasswordAsker password_asker: the password asker
        :param sakia.core.Community community: the community
        :param sakia.core.registry.Identity identity: the identity certified
        :return:
        """
        dialog = cls.create(parent, app, account=account, community=community, password_asker=password_asker)
        dialog.view.combo_community.setCurrentText(community.name)
        dialog.view.edit_pubkey.setText(identity.pubkey)
        dialog.view.radio_pubkey.setChecked(True)
        dialog.refresh()
        return await dialog.async_exec()

    @property
    def view(self) -> CertificationView:
        return self._view

    @property
    def model(self) -> CertificationModel:
        return self._model

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

    @asyncify
    async def accept(self):
        """
        Validate the dialog
        """
        self.view.button_box.setDisabled(True)
        pubkey = self.selected_pubkey()
        if pubkey:
            password = await self.password_asker.async_exec()
            if password == "":
                self.view.button_box.setEnabled(True)
                return
            QApplication.setOverrideCursor(Qt.WaitCursor)
            result = await self.account.certify(password, self.community, pubkey)
            if result[0]:
                QApplication.restoreOverrideCursor()
                await self.view.show_success()
                self.view.accept()
            else:
                await self.view.show_error(result[1])
                QApplication.restoreOverrideCursor()
                self.view.button_box.setEnabled(True)

    def reject(self):
        self.view.reject()

    def selected_pubkey(self):
        """
        Get selected pubkey in the widgets of the window
        :return: the current pubkey
        :rtype: str
        """
        pubkey = None

        if self.view.recipient_mode() == CertificationView.RecipientMode.CONTACT:
            contact_name = self.view.selected_contact()
            pubkey = self.model.contact_name_pubkey(contact_name)
        elif self.view.recipient_mode() == CertificationView.RecipientMode.SEARCH:
            if self.search_user.current_identity():
                pubkey = self.search_user.current_identity().pubkey
        else:
            pubkey = self.view.pubkey_value()
        return pubkey

    @once_at_a_time
    @asyncify
    async def refresh(self):
        stock = self.model.get_cert_stock()
        written, pending = await self.model.nb_certifications()
        days, hours, minutes, seconds = await self.model.remaining_time()
        self.view.display_cert_stock(written, pending, stock, days, hours, minutes)

        if await self.model.could_certify():
            if written < stock or stock == 0:
                if days+hours+minutes > 0:
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
        pubkey = self.selected_pubkey()
        self.user_information.search_identity(pubkey)

    def change_current_community(self, index):
        self.model.change_community(index)
        self.search_user.set_community(self.community)
        self.user_information.change_community(self.community)
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
