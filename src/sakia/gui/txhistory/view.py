from PyQt5.QtWidgets import QWidget, QAbstractItemView, QHeaderView
from PyQt5.QtCore import QDateTime, QEvent
from .txhistory_uic import Ui_TxHistoryWidget


class TxHistoryView(QWidget, Ui_TxHistoryWidget):
    """
    The view of TxHistory component
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)
        self.busy_balance.hide()
        self.progressbar.hide()

        self.table_history.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_history.setSortingEnabled(True)
        self.table_history.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_history.resizeColumnsToContents()

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
        model.modelAboutToBeReset.connect(lambda: self.table_history.setEnabled(False))
        model.modelReset.connect(lambda: self.table_history.setEnabled(True))

    async def set_minimum_maximum_datetime(self, minimum, maximum):
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

    def set_progress_bar(self, value, maximum):
        """
        Set progress bar value
        :param int value:
        :param maximum:
        :return:
        """
        if value >= maximum:
            self.progressbar.hide()
        else:
            self.view.progressbar.show()
            self.view.progressbar.setValue(value)
            self.view.progressbar.setMaximum(maximum)

    def resizeEvent(self, event):
        self.busy_balance.resize(event.size())
        super().resizeEvent(event)

    def changeEvent(self, event):
        """
        Intercepte LanguageChange event to translate UI
        :param QEvent QEvent: Event
        :return:
        """
        if event.type() == QEvent.LanguageChange:
            self.retranslateUi(self)
            self.refresh()
            return True
        super().changeEvent(event)