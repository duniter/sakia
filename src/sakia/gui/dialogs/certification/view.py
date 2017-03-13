from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QMessageBox
from PyQt5.QtCore import QT_TRANSLATE_NOOP, Qt
from .certification_uic import Ui_CertificationDialog
from sakia.gui.widgets import toast
from sakia.gui.widgets.dialogs import QAsyncMessageBox
from sakia.constants import ROOT_SERVERS
from enum import Enum


class CertificationView(QDialog, Ui_CertificationDialog):
    """
    The view of the certification component
    """

    class ButtonBoxState(Enum):
        NO_MORE_CERTIFICATION = 0
        NOT_A_MEMBER = 1
        REMAINING_TIME_BEFORE_VALIDATION = 2
        OK = 3
        SELECT_IDENTITY = 4
        WRONG_PASSWORD = 5

    _button_box_values = {
        ButtonBoxState.NO_MORE_CERTIFICATION: (False,
                                               QT_TRANSLATE_NOOP("CertificationView", "No more certifications")),
        ButtonBoxState.NOT_A_MEMBER: (False, QT_TRANSLATE_NOOP("CertificationView", "Not a member")),
        ButtonBoxState.SELECT_IDENTITY: (False, QT_TRANSLATE_NOOP("CertificationView", "Please select an identity")),
        ButtonBoxState.REMAINING_TIME_BEFORE_VALIDATION: (True,
                                                          QT_TRANSLATE_NOOP("CertificationView",
                                                                            "&Ok (Not validated before {remaining})")),
        ButtonBoxState.OK: (True, QT_TRANSLATE_NOOP("CertificationView", "&Ok")),
        ButtonBoxState.WRONG_PASSWORD: (False, QT_TRANSLATE_NOOP("CertificationView", "Please enter correct password"))
    }

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
        self.groupbox_certified.layout().addWidget(search_user_view)
        self.search_user_view.button_reset.hide()
        self.layout_password_input.addWidget(password_input_view)
        self.groupbox_certified.layout().addWidget(user_information_view)

    def set_keys(self, connections):
        self.combo_connection.clear()
        for c in connections:
            self.combo_connection.addItem(c.title())

    def set_selected_key(self, connection):
        """
        :param sakia.data.entities.Connection connection:
        """
        self.combo_connection.setCurrentText(connection.title())

    def pubkey_value(self):
        return self.edit_pubkey.text()

    def set_label_confirm(self, currency):
        self.label_confirm.setTextFormat(Qt.RichText)
        self.label_confirm.setText("""<b>Vous confirmez engager votre responsabilité envers la communauté Duniter {:}
    et acceptez de certifier le compte Duniter {:} ci-dessus.<br/><br/>
Pourconfirmer votre certification veuillez confirmer votre signature :</b>""".format(ROOT_SERVERS[currency]["display"],
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
