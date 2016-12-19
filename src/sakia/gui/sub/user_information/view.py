from PyQt5.QtCore import QLocale, QDateTime
from PyQt5.QtWidgets import QWidget
from .user_information_uic import Ui_UserInformationWidget
from sakia.gui.widgets.busy import Busy


class UserInformationView(QWidget, Ui_UserInformationWidget):
    """
    User information view
    """

    def __init__(self, parent):
        """
        Constructor
        """
        super().__init__(parent)
        self.setupUi(self)
        self.busy = Busy(self)
        self.busy.hide()

    def display_identity_timestamps(self, pubkey, publish_time, join_date):
        """
        Display identity timestamps in localized format
        :param str pubkey:
        :param int publish_time:
        :param int join_date:
        :return:
        """
        if join_date:
            localized_join_date = QLocale.toString(
                QLocale(),
                QDateTime.fromTime_t(join_date),
                QLocale.dateTimeFormat(QLocale(), QLocale.ShortFormat)
            )
        else:
            localized_join_date = "###"

        if publish_time:
            localized_publish_date = QLocale.toString(
                QLocale(),
                QDateTime.fromTime_t(publish_time),
                QLocale.dateTimeFormat(QLocale(), QLocale.ShortFormat)
            )
        else:
            localized_publish_date = "###"

        text = self.tr("""
            <table cellpadding="5">
            <tr><td align="right"><b>{:}</b></div></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></div></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></div></td><td>{:}</td></tr>
            """).format(
            self.tr('Public key'),
            pubkey,
            self.tr('UID Published on'),
            localized_publish_date,
            self.tr('Join date'),
            localized_join_date
        )
        # close html text
        text += "</table>"

        # set text in label
        self.label_properties.setText(text)

    def display_uid(self, uid):
        """
        Display the uid in the label
        :param str uid:
        """
        self.label_uid.setText(uid)

    def show_busy(self):
        self.busy.show()

    def hide_busy(self):
        self.busy.hide()

    def resizeEvent(self, event):
        self.busy.resize(event.size())
        super().resizeEvent(event)