from PyQt5.QtCore import Qt, QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout

from sakia.constants import ROOT_SERVERS
from sakia.decorators import asyncify
from sakia.gui.sub.search_user.controller import SearchUserController
from sakia.gui.sub.user_information.controller import UserInformationController
from sakia.gui.sub.password_input import PasswordInputController
from sakia.gui.widgets import dialogs
from sakia.data.entities import Identity
from .model import CertificationModel
from .view import CertificationView
import attr


@attr.s()
class CertificationController(QObject):
    """
    The Certification view
    """
    accepted = pyqtSignal()
    rejected = pyqtSignal()

    view = attr.ib()
    model = attr.ib()
    search_user = attr.ib()
    user_information = attr.ib()
    password_input = attr.ib()

    def __attrs_post_init__(self):
        super().__init__()
        self.view.button_box.accepted.connect(self.accept)
        self.view.button_box.rejected.connect(self.reject)
        self.view.button_cancel.clicked.connect(self.reject)
        self.view.button_cancel_licence.clicked.connect(self.reject)
        self.view.combo_connections.currentIndexChanged.connect(self.change_connection)

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
        view.set_label_confirm(app.currency)
        certification = cls(view, model, search_user, user_information, password_input)
        search_user.identity_selected.connect(certification.refresh_user_information)
        password_input.password_changed.connect(certification.refresh)

        user_information.identity_loaded.connect(certification.refresh)

        view.set_keys(certification.model.available_connections())
        view.identity_document_imported.connect(certification.load_identity_document)
        return certification

    @classmethod
    def integrate_to_main_view(cls, parent, app, connection):
        certification = cls.create(parent, app)
        certification.view.combo_connections.setCurrentText(connection.title())
        certification.view.groupbox_identity.hide()
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

        dialog = QDialog(parent)
        dialog.setWindowTitle(dialog.tr("Certification"))
        dialog.setLayout(QVBoxLayout(dialog))
        certification = cls.create(parent, app)
        certification.set_connection(connection)
        certification.refresh()
        dialog.layout().addWidget(certification.view)
        certification.accepted.connect(dialog.accept)
        certification.rejected.connect(dialog.reject)
        return dialog.exec()

    @classmethod
    def certify_identity(cls, parent, app, connection, identity):
        """
        Certify and identity
        :param sakia.gui.component.controller.ComponentController parent: the parent
        :param sakia.core.Application app: the application
        :param sakia.data.entities.Connection connection: the connection
        :param sakia.data.entities.Identity identity: the identity certified
        :return:
        """
        dialog = QDialog(parent)
        dialog.setWindowTitle(dialog.tr("Certification"))
        dialog.setLayout(QVBoxLayout(dialog))
        certification = cls.create(parent, app)
        if connection:
            certification.view.combo_connections.setCurrentText(connection.title())
        certification.user_information.change_identity(identity)
        certification.refresh()
        dialog.layout().addWidget(certification.view)
        certification.accepted.connect(dialog.accept)
        certification.rejected.connect(dialog.reject)
        return dialog.exec()

    def change_connection(self, index):
        self.model.set_connection(index)
        self.password_input.set_connection(self.model.connection)
        self.refresh()

    def set_connection(self, connection):
        if connection:
            self.view.combo_connections.setCurrentText(connection.title())
            self.password_input.set_connection(connection)

    @asyncify
    async def accept(self):
        """
        Validate the dialog
        """

        if not self.user_information.model.identity.member:
            result = await dialogs.QAsyncMessageBox.question(self.view, "Certifying a non-member",
"""
Did you ensure that :<br>
<br/>
1°) <b>You know the person declaring owning this pubkey
well enough and to personally verify that it is the correct key you are going to certify.</b><br/>
2°) To physically meet her to ensure that it is the person you know who owns this pubkey.<br/>
3°) Or did you ensure by contacting her using multiple communications means,
like forum + mail + videoconferencing + phone (to recognize voice)<br/>
Because if one can hack 1 mail account or 1 forum account, it will be way more difficult to hack multiple
communication means and imitate the voice of the person.<br/>
<br/>
The 2°) is however preferable to the 3°)... whereas <b>1°) is mandatory in any case.</b><br/>
<br/>
<b>Reminder</b> : Certifying is not only uniquely ensuring  that you met the person, its ensuring the {:} community
that you know her well enough and that you will know how to find a double account done by a person certified by you
using cross checking which will help to reveal the problem if needs to be.</br>""".format(
    ROOT_SERVERS[self.model.app.currency]["display"]))
            if result == dialogs.QMessageBox.No:
                return

        self.view.button_box.setDisabled(True)
        secret_key, password = self.password_input.get_salt_password()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        result = await self.model.certify_identity(secret_key, password, self.user_information.model.identity)
#
        if result[0]:
            QApplication.restoreOverrideCursor()
            await self.view.show_success(self.model.notification())
            self.search_user.clear()
            self.user_information.clear()
            self.view.clear()
            self.accepted.emit()
        else:
            await self.view.show_error(self.model.notification(), result[1])
            QApplication.restoreOverrideCursor()
            self.view.button_box.setEnabled(True)

    def reject(self):
        self.search_user.clear()
        self.user_information.clear()
        self.view.clear()
        self.rejected.emit()

    def refresh(self):
        stock = self.model.get_cert_stock()
        written, pending = self.model.nb_certifications()
        days, hours, minutes, seconds = self.model.remaining_time()
        self.view.display_cert_stock(written, pending, stock, days, hours, minutes)

        if self.model.could_certify():
            if written < stock or stock == 0:
                if not self.user_information.model.identity:
                    self.view.set_button_process(CertificationView.ButtonsState.SELECT_IDENTITY)
                elif days+hours+minutes > 0:
                    if days > 0:
                        remaining_localized = self.tr("{days} days").format(days=days)
                    else:
                        remaining_localized = self.tr("{hours}h {min}min").format(hours=hours, min=minutes)
                    self.view.set_button_process(CertificationView.ButtonsState.REMAINING_TIME_BEFORE_VALIDATION,
                                                 remaining=remaining_localized)
                else:
                    self.view.set_button_process(CertificationView.ButtonsState.OK)
                    if self.password_input.valid():
                        self.view.set_button_box(CertificationView.ButtonsState.OK)
                    else:
                        self.view.set_button_box(CertificationView.ButtonsState.WRONG_PASSWORD)
            else:
                self.view.set_button_process(CertificationView.ButtonsState.NO_MORE_CERTIFICATION)
        else:
            self.view.set_button_process(CertificationView.ButtonsState.NOT_A_MEMBER)

    def load_identity_document(self, identity_doc):
        """
        Load an identity document
        :param  duniterpy.documents.Identity identity_doc:
        """
        identity = Identity(currency=identity_doc.currency,
                            pubkey=identity_doc.pubkey,
                            uid=identity_doc.uid,
                            blockstamp=identity_doc.timestamp,
                            signature=identity_doc.signatures[0])
        self.user_information.change_identity(identity)

    def refresh_user_information(self):
        """
        Refresh user information
        """
        self.user_information.search_identity(self.search_user.model.identity())
