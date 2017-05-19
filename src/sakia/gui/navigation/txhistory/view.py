from PyQt5.QtCore import QDateTime, QEvent
from PyQt5.QtWidgets import QWidget, QAbstractItemView, QHeaderView
from .delegate import TxHistoryDelegate

from .txhistory_uic import Ui_TxHistoryWidget


class TxHistoryView(QWidget, Ui_TxHistoryWidget):
    """
    The view of TxHistory component
    """

    def __init__(self, parent, transfer_view):
        super().__init__(parent)
        self.transfer_view = transfer_view
        self.setupUi(self)
        self.stacked_widget.insertWidget(1, transfer_view)
        self.button_send.clicked.connect(lambda c: self.stacked_widget.setCurrentWidget(self.transfer_view))
        self.spin_page.setMinimum(1)

    def get_time_frame(self):
        """
        Get the time frame of date filters
        :return: the timestamps of the date filters
        """
        return self.date_from.dateTime().toTime_t(), self.date_to.dateTime().toTime_t()

    def set_table_history_model(self, model):
        """
        Define the table history model
        :param QAbstractItemModel model:
        :return:
        """
        self.table_history.setModel(model)
        self.table_history.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_history.setSortingEnabled(True)
        self.table_history.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_history.setItemDelegate(TxHistoryDelegate())
        self.table_history.resizeRowsToContents()
        self.table_history.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    def set_minimum_maximum_datetime(self, minimum, maximum):
        """
        Configure minimum and maximum datetime in date filter
        :param PyQt5.QtCore.QDateTime minimum: the minimum
        :param PyQt5.QtCore.QDateTime maximum: the maximum
        """
        self.date_from.setMinimumDateTime(minimum)
        self.date_from.setDateTime(minimum)
        self.date_from.setMaximumDateTime(QDateTime().currentDateTime())

        self.date_to.setMinimumDateTime(minimum)
        self.date_to.setDateTime(maximum)
        self.date_to.setMaximumDateTime(maximum)

    def set_max_pages(self, pages):
        self.spin_page.setSuffix(self.tr(" / {:} pages").format(pages + 1))
        self.spin_page.setMaximum(pages + 1)

    def set_balance(self, balance):
        """
        Display given balance
        :param balance: the given balance to display
        :return:
        """
        # set infos in label
        self.label_balance.setText(
            "{:}".format(balance)
        )

    def clear(self):
        self.stacked_widget.setCurrentWidget(self.page_history)

    def changeEvent(self, event):
        """
        Intercepte LanguageChange event to translate UI
        :param QEvent QEvent: Event
        :return:
        """
        if event.type() == QEvent.LanguageChange:
            self.retranslateUi(self)
        super().changeEvent(event)