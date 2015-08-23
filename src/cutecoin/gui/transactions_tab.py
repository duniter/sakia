from PyQt5.QtWidgets import QWidget, QAbstractItemView, QHeaderView, QDialog, \
    QMenu, QAction, QApplication, QMessageBox
from PyQt5.QtCore import Qt, QDateTime, QTime, QModelIndex, QCoreApplication, pyqtSlot, QEvent
from PyQt5.QtGui import QCursor
from ..gen_resources.transactions_tab_uic import Ui_transactionsTabWidget
from ..models.txhistory import HistoryTableModel, TxFilterProxyModel
from ..core.transfer import Transfer
from ..core.wallet import Wallet
from ..core.registry import Identity
from .transfer import TransferMoneyDialog
from . import toast

import logging


class TransactionsTabWidget(QWidget, Ui_transactionsTabWidget):
    """
    classdocs
    """

    def __init__(self, app, community, password_asker, currency_tab):
        """
        Init

        :param cutecoin.core.app.Application app: Application instance
        :param cutecoin.core.community.Community community: Community instance
        :param cutecoin.gui.password_asker.PasswordAskerDialog password_asker: Password dialog instance
        :param cutecoin.gui.currency_tab.CurrencyTabWidget currency_tab: Currency tab widget
        :return:
        """

        super().__init__()
        self.setupUi(self)
        self.app = app
        self.community = community
        self.password_asker = password_asker
        self.currency_tab = currency_tab
        self.progressbar.hide()
        self.community.inner_data_changed.connect(self.refresh_minimum_maximum)
        self.refresh()

    def refresh_minimum_maximum(self):
        block = self.community.get_block(1)
        minimum_datetime = QDateTime()
        minimum_datetime.setTime_t(block['medianTime'])
        minimum_datetime.setTime(QTime(0, 0))

        self.date_from.setMinimumDateTime(minimum_datetime)
        self.date_from.setDateTime(minimum_datetime)
        self.date_from.setMaximumDateTime(QDateTime().currentDateTime())

        self.date_to.setMinimumDateTime(minimum_datetime)
        tomorrow_datetime = QDateTime().currentDateTime().addDays(1)
        self.date_to.setDateTime(tomorrow_datetime)
        self.date_to.setMaximumDateTime(tomorrow_datetime)

    def refresh(self):
        #TODO: Use resetmodel instead of destroy/create
        self.refresh_minimum_maximum()
        ts_from = self.date_from.dateTime().toTime_t()
        ts_to = self.date_to.dateTime().toTime_t()

        model = HistoryTableModel(self.app, self.community)
        proxy = TxFilterProxyModel(ts_from, ts_to)
        proxy.setSourceModel(model)
        proxy.setDynamicSortFilter(True)
        proxy.setSortRole(Qt.DisplayRole)

        self.table_history.setModel(proxy)
        self.table_history.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_history.setSortingEnabled(True)
        self.table_history.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_history.resizeColumnsToContents()

        self.refresh_balance()

    def start_progress(self):
        def progressing(value, maximum):
            self.progressbar.setValue(value)
            self.progressbar.setMaximum(maximum)
        self.app.current_account.loading_progressed.connect(progressing)
        self.app.current_account.loading_finished.connect(self.stop_progress)
        self.app.current_account.refresh_transactions(self.app, self.community)
        self.progressbar.show()

    @pyqtSlot(list)
    def stop_progress(self, received_list):
        amount = 0
        for r in received_list:
            amount += r.metadata['amount']
        self.progressbar.hide()
        if len(received_list) > 0:
            text = self.tr("Received {0} {1} from {2} transfers").format(amount,
                                                               self.community.currency,
                                                               len(received_list))
            if self.app.preferences['notifications']:
                toast.display(self.tr("New transactions received"), text)

        self.table_history.model().sourceModel().refresh_transfers()
        self.table_history.resizeColumnsToContents()

    def refresh_balance(self):
        # if referential is "units"
        if self.app.current_account._current_ref == 0:
            self.label_balance.show()
            self.label_deposit.show()
            self.label_payment.show()
        else:
            self.label_balance.hide()
            self.label_deposit.hide()
            self.label_payment.hide()

        proxy = self.table_history.model()
        balance = proxy.deposits - proxy.payments
        localized_deposits = self.app.current_account.current_ref(proxy.deposits, self.community, self.app).diff_localized()
        localized_payments = self.app.current_account.current_ref(proxy.payments, self.community, self.app).diff_localized()
        localized_balance = self.app.current_account.current_ref(balance, self.community, self.app).diff_localized()

        self.label_deposit.setText(QCoreApplication.translate("TransactionsTabWidget", "<b>Deposits</b> {:} {:}").format(
            localized_deposits,
            self.app.current_account.current_ref.units(self.community.short_currency)
        ))
        self.label_payment.setText(QCoreApplication.translate("TransactionsTabWidget", "<b>Payments</b> {:} {:}").format(
            localized_payments,
            self.app.current_account.current_ref.units(self.community.short_currency)
        ))
        self.label_balance.setText(QCoreApplication.translate("TransactionsTabWidget", "<b>Balance</b> {:} {:}").format(
            localized_balance,
            self.app.current_account.current_ref.units(self.community.short_currency)
        ))

    def history_context_menu(self, point):
        index = self.table_history.indexAt(point)
        model = self.table_history.model()
        if index.row() < model.rowCount(QModelIndex()):
            menu = QMenu(self.tr("Actions"), self)
            source_index = model.mapToSource(index)
            state_col = model.sourceModel().columns_types.index('state')
            state_index = model.sourceModel().index(source_index.row(),
                                                   state_col)
            state_data = model.sourceModel().data(state_index, Qt.DisplayRole)

            pubkey_col = model.sourceModel().columns_types.index('pubkey')
            identity_index = model.sourceModel().index(source_index.row(),
                                                    pubkey_col)
            identity = model.sourceModel().data(identity_index, Qt.DisplayRole)
            transfer = model.sourceModel().transfers[source_index.row()]
            if state_data == Transfer.REFUSED or state_data == Transfer.TO_SEND:
                send_back = QAction(self.tr("Send again"), self)
                send_back.triggered.connect(self.send_again)
                send_back.setData(transfer)
                menu.addAction(send_back)

                cancel = QAction(self.tr("Cancel"), self)
                cancel.triggered.connect(self.cancel_transfer)
                cancel.setData(transfer)
                menu.addAction(cancel)
            else:
                if isinstance(identity, Identity):
                    informations = QAction(self.tr("Informations"), self)
                    informations.triggered.connect(self.currency_tab.tab_community.menu_informations)
                    informations.setData(identity)
                    menu.addAction(informations)

                    add_as_contact = QAction(self.tr("Add as contact"), self)
                    add_as_contact.triggered.connect(self.currency_tab.tab_community.menu_add_as_contact)
                    add_as_contact.setData(identity)
                    menu.addAction(add_as_contact)

                send_money = QAction(self.tr("Send money"), self)
                send_money.triggered.connect(self.currency_tab.tab_community.menu_send_money)
                send_money.setData(identity)
                menu.addAction(send_money)

                if isinstance(identity, Identity):
                    view_wot = QAction(self.tr("View in Web of Trust"), self)
                    view_wot.triggered.connect(self.currency_tab.tab_community.view_wot)
                    view_wot.setData(identity)
                    menu.addAction(view_wot)

            copy_pubkey = QAction(self.tr("Copy pubkey to clipboard"), self)
            copy_pubkey.triggered.connect(self.copy_pubkey_to_clipboard)
            copy_pubkey.setData(identity)
            menu.addAction(copy_pubkey)

            # Show the context menu.
            menu.exec_(QCursor.pos())

    def copy_pubkey_to_clipboard(self):
        data = self.sender().data()
        clipboard = QApplication.clipboard()
        if data.__class__ is Wallet:
            clipboard.setText(data.pubkey)
        elif data.__class__ is Identity:
            clipboard.setText(data.pubkey)
        elif data.__class__ is str:
            clipboard.setText(data)

    def send_again(self):
        transfer = self.sender().data()
        dialog = TransferMoneyDialog(self.app, self.app.current_account,
                                     self.password_asker)
        dialog.accepted.connect(self.currency_tab.refresh_wallets)
        sender = transfer.metadata['issuer']
        wallet_index = [w.pubkey for w in self.app.current_account.wallets].index(sender)
        dialog.combo_wallets.setCurrentIndex(wallet_index)
        dialog.edit_pubkey.setText(transfer.metadata['receiver'])
        dialog.combo_community.setCurrentText(self.community.name)
        dialog.spinbox_amount.setValue(transfer.metadata['amount'])
        dialog.radio_pubkey.setChecked(True)
        dialog.edit_message.setText(transfer.metadata['comment'])
        result = dialog.exec_()
        if result == QDialog.Accepted:
            transfer.drop()
            self.table_history.model().sourceModel().refresh_transfers()

    def cancel_transfer(self):
        reply = QMessageBox.warning(self, self.tr("Warning"),
                             self.tr("""Are you sure ?
This money transfer will be removed and not sent."""),
QMessageBox.Ok | QMessageBox.Cancel)
        if reply == QMessageBox.Ok:
            transfer = self.sender().data()
            transfer.drop()
            self.table_history.model().sourceModel().refresh_transfers()

    def dates_changed(self):
        logging.debug("Changed dates")
        if self.table_history.model():
            qdate_from = self.date_from
            qdate_from.setTime(QTime(0, 0, 0))
            qdate_to = self.date_to
            qdate_to.setTime(QTime(0, 0, 0))
            ts_from = qdate_from.dateTime().toTime_t()
            ts_to = qdate_to.dateTime().toTime_t()

            self.table_history.model().set_period(ts_from, ts_to)

            self.refresh_balance()

    def changeEvent(self, event):
        """
        Intercepte LanguageChange event to translate UI
        :param QEvent QEvent: Event
        :return:
        """
        if event.type() == QEvent.LanguageChange:
            self.retranslateUi(self)
            self.refresh()
        return super(TransactionsTabWidget, self).changeEvent(event)
