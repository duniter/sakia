from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QMessageBox
from PyQt5.QtCore import QT_TRANSLATE_NOOP, pyqtSignal
from .certification_uic import Ui_CertificationDialog
from ..widgets import toast
from ..widgets.dialogs import QAsyncMessageBox
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

    class RecipientMode(Enum):
        CONTACT = 0
        PUBKEY = 1
        SEARCH = 2

    _button_box_values = {
        ButtonBoxState.NO_MORE_CERTIFICATION: (False,
                                               QT_TRANSLATE_NOOP("CertificationView", "No more certifications")),
        ButtonBoxState.NOT_A_MEMBER: (False, QT_TRANSLATE_NOOP("CertificationView", "Not a member")),
        ButtonBoxState.REMAINING_TIME_BEFORE_VALIDATION: (True,
                                                          QT_TRANSLATE_NOOP("CertificationView",
                                                                            "&Ok (Not validated before {remaining})")),
        ButtonBoxState.OK: (True, QT_TRANSLATE_NOOP("CertificationView", "&Ok"))
    }

    pubkey_changed = pyqtSignal()

    def __init__(self, parent, search_user_view, user_information_view, communities_names, contacts_names):
        """

        :param parent:
        :param sakia.gui.search_user.view.SearchUserView search_user_view:
        :param sakia.gui.user_information.view.UserInformationView user_information_view:
        :param list[str] communities_names:
        :param list[str] contacts_names:
        """
        super().__init__(parent)
        self.setupUi(self)

        self.radio_contact.toggled.connect(lambda c, radio=CertificationView.RecipientMode.CONTACT: self.recipient_mode_changed(radio))
        self.radio_pubkey.toggled.connect(lambda c, radio=CertificationView.RecipientMode.PUBKEY: self.recipient_mode_changed(radio))
        self.radio_search.toggled.connect(lambda c, radio=CertificationView.RecipientMode.SEARCH: self.recipient_mode_changed(radio))

        for name in communities_names:
            self.combo_community.addItem(name)

        for name in sorted(contacts_names):
            self.combo_contact.addItem(name)

        if len(contacts_names) == 0:
            self.radio_pubkey.setChecked(True)
            self.radio_contact.setEnabled(False)

        self.search_user = search_user_view
        self.user_information_view = user_information_view

        self.combo_contact.currentIndexChanged.connect(self.pubkey_changed)
        self.edit_pubkey.textChanged.connect(self.pubkey_changed)
        self.radio_contact.toggled.connect(self.pubkey_changed)
        self.radio_search.toggled.connect(self.pubkey_changed)
        self.radio_pubkey.toggled.connect(self.pubkey_changed)

    def set_search_user(self, search_user_view):
        """

        :param sakia.gui.search_user.view.SearchUserView search_user_view:
        :return:
        """
        self.search_user = search_user_view
        self.layout_mode_search.addWidget(search_user_view)
        self.search_user.button_reset.hide()

    def set_user_information(self, user_information_view):
        self.user_information_view = user_information_view
        self.layout_target_choice.addWidget(user_information_view)

    def recipient_mode(self):
        if self.radio_contact.isChecked():
            return CertificationView.RecipientMode.CONTACT
        elif self.radio_search.isChecked():
            return CertificationView.RecipientMode.SEARCH
        else:
            return CertificationView.RecipientMode.PUBKEY

    def selected_contact(self):
        return self.combo_contact.currentText()

    def pubkey_value(self):
        return self.edit_pubkey.text()

    async def show_success(self):
        if self.app.preferences['notifications']:
            toast.display(self.tr("Certification"),
                          self.tr("Success sending certification"))
        else:
            await QAsyncMessageBox.information(self.widget, self.tr("Certification"),
                                         self.tr("Success sending certification"))

    async def show_error(self, error_txt):

        if self.app.preferences['notifications']:
            toast.display(self.tr("Certification"), self.tr("Could not broadcast certification : {0}"
                                                            .format(error_txt)))
        else:
            await QAsyncMessageBox.critical(self.widget, self.tr("Certification"),
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

    def recipient_mode_changed(self, radio):
        """
        :param str radio:
        """
        self.edit_pubkey.setEnabled(radio == CertificationView.RecipientMode.PUBKEY)
        self.combo_contact.setEnabled(radio == CertificationView.RecipientMode.CONTACT)
        self.search_user.setEnabled(radio == CertificationView.RecipientMode.SEARCH)
