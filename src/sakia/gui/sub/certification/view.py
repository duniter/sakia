from PyQt5.QtWidgets import QWidget, QDialogButtonBox, QFileDialog, QMessageBox
from PyQt5.QtCore import QT_TRANSLATE_NOOP, Qt, pyqtSignal
from .certification_uic import Ui_CertificationWidget
from sakia.gui.widgets import toast
from sakia.gui.widgets.dialogs import QAsyncMessageBox
from sakia.constants import ROOT_SERVERS, G1_LICENCE
from duniterpy.documents import Identity, MalformedDocumentError
from enum import Enum


class CertificationView(QWidget, Ui_CertificationWidget):
    """
    The view of the certification component
    """

    class ButtonsState(Enum):
        NO_MORE_CERTIFICATION = 0
        NOT_A_MEMBER = 1
        REMAINING_TIME_BEFORE_VALIDATION = 2
        OK = 3
        SELECT_IDENTITY = 4
        WRONG_PASSWORD = 5

    _button_process_values = {
        ButtonsState.NO_MORE_CERTIFICATION: (False,
                                             QT_TRANSLATE_NOOP("CertificationView", "No more certifications")),
        ButtonsState.NOT_A_MEMBER: (False, QT_TRANSLATE_NOOP("CertificationView", "Not a member")),
        ButtonsState.SELECT_IDENTITY: (False, QT_TRANSLATE_NOOP("CertificationView", "Please select an identity")),
        ButtonsState.REMAINING_TIME_BEFORE_VALIDATION: (True,
                                                        QT_TRANSLATE_NOOP("CertificationView",
                                                                            "&Ok (Not validated before {remaining})")),
        ButtonsState.OK: (True, QT_TRANSLATE_NOOP("CertificationView", "&Process Certification")),
    }

    _button_box_values = {
        ButtonsState.OK: (True, QT_TRANSLATE_NOOP("CertificationView", "&Ok")),
        ButtonsState.WRONG_PASSWORD: (False, QT_TRANSLATE_NOOP("CertificationView", "Please enter correct password"))
    }

    identity_document_imported = pyqtSignal(Identity)

    def __init__(self, parent, search_user_view, user_information_view, password_input_view):
        """

        :param parent:
        :param sakia.gui.search_user.view.SearchUserView search_user_view:
        :param sakia.gui.user_information.view.UserInformationView user_information_view:
        :param list[sakia.data.entities.Connection] connections:
        """
        super().__init__(parent)
        self.setupUi(self)

        self.search_user_view = search_user_view
        self.user_information_view = user_information_view
        self.password_input_view = password_input_view
        self.identity_select_layout.insertWidget(0, search_user_view)
        self.search_user_view.button_reset.hide()
        self.layout_password_input.addWidget(password_input_view)
        self.groupbox_certified.layout().addWidget(user_information_view)
        self.button_import_identity.clicked.connect(self.import_identity_document)
        self.button_process.clicked.connect(lambda c: self.stackedWidget.setCurrentIndex(1))
        self.button_accept.clicked.connect(lambda c: self.stackedWidget.setCurrentIndex(2))

        licence_text = self.tr(G1_LICENCE)
        self.text_licence.setText(licence_text)

    def clear(self):
        self.stackedWidget.setCurrentIndex(0)
        self.set_button_process(CertificationView.ButtonsState.SELECT_IDENTITY)
        self.password_input_view.clear()
        self.search_user_view.clear()
        self.user_information_view.clear()

    def set_keys(self, connections):
        self.combo_connections.clear()
        for c in connections:
            self.combo_connections.addItem(c.title())

    def set_selected_key(self, connection):
        """
        :param sakia.data.entities.Connection connection:
        """
        self.combo_connections.setCurrentText(connection.title())

    def pubkey_value(self):
        return self.edit_pubkey.text()

    def import_identity_document(self):
        file_name = QFileDialog.getOpenFileName(self,
                                                self.tr("Open identity document"), "",
                                                self.tr("Duniter documents (*.txt)"))
        if file_name and file_name[0]:
            with open(file_name[0], 'r') as open_file:
                raw_text = open_file.read()
                try:
                    identity_doc = Identity.from_signed_raw(raw_text)
                    self.identity_document_imported.emit(identity_doc)
                except MalformedDocumentError as e:
                    QMessageBox.warning(self, self.tr("Identity document"),
                                        self.tr("The imported file is not a correct identity document"),
                                        QMessageBox.Ok)

    def set_label_confirm(self, currency):
        self.label_confirm.setTextFormat(Qt.RichText)
        self.label_confirm.setText("""<b>Vous confirmez engager votre responsabilité envers la communauté Duniter {:}
    et acceptez de certifier le compte Duniter {:} sélectionné.<br/><br/>""".format(ROOT_SERVERS[currency]["display"],
                                                                                     ROOT_SERVERS[currency]["display"]))

    async def show_success(self, notification):
        if notification:
            toast.display(self.tr("Certification"),
                          self.tr("Success sending certification"))
        else:
            await QAsyncMessageBox.information(self, self.tr("Certification"),
                                         self.tr("Success sending certification"))

    async def show_error(self, notification, error_txt):

        if notification:
            toast.display(self.tr("Certification"), self.tr("Could not broadcast certification : {0}"
                                                            .format(error_txt)))
        else:
            await QAsyncMessageBox.critical(self, self.tr("Certification"),
                                            self.tr("Could not broadcast certification : {0}"
                                                    .format(error_txt)))

    def display_cert_stock(self, written, pending, stock,
                           remaining_days, remaining_hours, remaining_minutes):
        """
        Display values in informations label
        :param int written: number of written certifications
        :param int pending: number of pending certifications
        :param int stock: maximum certifications
        :param int remaining_days:
        :param int remaining_hours:
        :param int remaining_minutes:
        """
        cert_text = self.tr("Certifications sent : {nb_certifications}/{stock}").format(
            nb_certifications=written,
            stock=stock)
        if pending > 0:
            cert_text += " (+{nb_cert_pending} certifications pending)".format(nb_cert_pending=pending)

        if remaining_days > 0:
            remaining_localized = self.tr("{days} days").format(days=remaining_days)
        else:
            remaining_localized = self.tr("{hours} hours and {min} min.").format(hours=remaining_hours,
                                                                            min=remaining_minutes)
        cert_text += "\n"
        cert_text += self.tr("Remaining time before next certification validation : {0}".format(remaining_localized))
        self.label_cert_stock.setText(cert_text)

    def set_button_box(self, state, **kwargs):
        """
        Set button box state
        :param sakia.gui.certification.view.CertificationView.ButtonBoxState state: the state of te button box
        :param dict kwargs: the values to replace from the text in the state
        :return:
        """
        button_box_state = CertificationView._button_box_values[state]
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(button_box_state[0])
        self.button_box.button(QDialogButtonBox.Ok).setText(button_box_state[1].format(**kwargs))

    def set_button_process(self, state, **kwargs):
        """
        Set button box state
        :param sakia.gui.certification.view.CertificationView.ButtonBoxState state: the state of te button box
        :param dict kwargs: the values to replace from the text in the state
        :return:
        """
        button_process_state = CertificationView._button_process_values[state]
        self.button_process.setEnabled(button_process_state[0])
        self.button_process.setText(button_process_state[1].format(**kwargs))
