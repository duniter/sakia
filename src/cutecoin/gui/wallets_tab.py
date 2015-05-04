'''
Created on 15 févr. 2015

@author: inso
'''

import logging
from PyQt5.QtWidgets import QWidget, QMenu, QAction, QApplication, QDialog
from PyQt5.QtCore import QDateTime, QModelIndex, Qt
from PyQt5.QtGui import QCursor
from ..core.person import Person
from ..core.wallet import Wallet
from ..models.wallets import WalletsTableModel, WalletsFilterProxyModel
from .transfer import TransferMoneyDialog
from ..tools.exceptions import MembershipNotFoundError
from ..gen_resources.wallets_tab_uic import Ui_WalletsTab


class WalletsTabWidget(QWidget, Ui_WalletsTab):
    '''
    classdocs
    '''

    def __init__(self, app, account, community, password_asker):
        '''
        Constructor
        '''
        super().__init__()
        self.setupUi(self)
        self.app = app
        self.account = account
        self.community = community
        self.password_asker = password_asker

        self.refresh()

    def refresh(self):
        parameters = self.community.parameters
        last_renewal = ""
        expiration = ""
        try:
            person = Person.lookup(self.account.pubkey, self.community)
            membership = person.membership(self.community)
            renew_block = membership['blockNumber']
            last_renewal = self.community.get_block(renew_block).mediantime
            expiration = last_renewal + parameters['sigValidity']
        except MembershipNotFoundError:
            last_renewal = None
            expiration = None

        certified = person.unique_valid_certified_by(self.community)
        certifiers = person.unique_valid_certifiers_of(self.community)
        if last_renewal and expiration:
            date_renewal = QDateTime.fromTime_t(last_renewal).date().toString()
            date_expiration = QDateTime.fromTime_t(expiration).date().toString()
            # set infos in label
            self.label_general.setText(
                """
                <table cellpadding="5">
                <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
                <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
                <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
                </table>
                """.format(
                        self.account.name, self.account.pubkey,
                        "Membership",
                        "Last renewal on {:}, expiration on {:}".format(date_renewal, date_expiration),
                        "Your web of trust :",
                        "Certified by : {:} members; Certifier of : {:} members".format(len(certifiers),
                                                                         len(certified))
                )
            )
        else:
            # set infos in label
            self.label_general.setText(
                """
                <table cellpadding="5">
                <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
                <tr><td align="right"><b>{:}</b></td></tr>
                <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
                </table>
                """.format(
                        self.account.name, self.account.pubkey,
                        "Not a member",
                        "Your web of trust :",
                        "Certified by : {:} members; Certifier of : {:} members".format(len(certifiers),
                                                                         len(certified))
                )
            )

        amount = self.account.amount(self.community)
        maximum = self.community.monetary_mass

        # set infos in label
        self.label_balance.setText(
            """
            <table cellpadding="5">
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            </table>
            """.format("Your money share : ",
                       "{:.2f}%".format(amount/maximum*100) if maximum != 0 else "0%",
                       "Your part : ", "{:.2f} {:} in [{:.2f} - {:.2f}] {:}"
                       .format(self.get_referential_value(amount),
                            self.get_referential_name(),
                           self.get_referential_value(0),
                           self.get_referential_value(maximum),
                           self.get_referential_name())
            )
        )

        wallets_model = WalletsTableModel(self.account, self.community)
        proxy_model = WalletsFilterProxyModel()
        proxy_model.setSourceModel(wallets_model)
        wallets_model.dataChanged.connect(self.wallet_changed)
        self.table_wallets.setModel(proxy_model)

    def get_referential_value(self, value):
        return self.account.units_to_ref(value, self.community)

    def get_referential_diff_value(self, value):
        return self.account.units_to_diff_ref(value, self.community)

    def get_referential_name(self):
        return self.account.ref_name(self.community.short_currency)

    def wallet_context_menu(self, point):
        index = self.table_wallets.indexAt(point)
        model = self.table_wallets.model()
        if index.row() < model.rowCount(QModelIndex()):
            source_index = model.mapToSource(index)

            name_col = model.sourceModel().columns_types.index('name')
            name_index = model.index(index.row(),
                                    name_col)

            pubkey_col = model.sourceModel().columns_types.index('pubkey')
            pubkey_index = model.sourceModel().index(source_index.row(),
                                                   pubkey_col)

            pubkey = model.sourceModel().data(pubkey_index, Qt.DisplayRole)
            menu = QMenu(model.data(index, Qt.DisplayRole), self)

            rename = QAction("Rename", self)
            rename.triggered.connect(self.rename_wallet)
            rename.setData(name_index)

            copy_pubkey = QAction("Copy pubkey to clipboard", self)
            copy_pubkey.triggered.connect(self.copy_pubkey_to_clipboard)
            copy_pubkey.setData(pubkey)

            transfer_to = QMenu()
            transfer_to.setTitle("Transfer to...")
            for w in self.account.wallets:
                transfer_action = QAction(w.name, self)
                transfer_action.triggered.connect(self.transfer_to_wallet)
                wallets = (self.account.wallets[source_index.row()], w)
                transfer_action.setData(wallets)
                transfer_to.addAction(transfer_action)

            menu.addAction(rename)
            menu.addAction(copy_pubkey)
            menu.addMenu(transfer_to)
            # Show the context menu.
            menu.exec_(QCursor.pos())

    def rename_wallet(self):
        index = self.sender().data()
        self.table_wallets.edit(index)

    def wallet_changed(self):
        self.app.save(self.app.current_account)

    def copy_pubkey_to_clipboard(self):
        data = self.sender().data()
        clipboard = QApplication.clipboard()
        if data.__class__ is Wallet:
            clipboard.setText(data.pubkey)
        elif data.__class__ is Person:
            clipboard.setText(data.pubkey)
        elif data.__class__ is str:
            clipboard.setText(data)

    def transfer_to_wallet(self):
        wallets = self.sender().data()
        dialog = TransferMoneyDialog(self.account, self.password_asker)
        dialog.edit_pubkey.setText(wallets[1].pubkey)
        dialog.combo_community.setCurrentText(self.community.name)
        dialog.combo_wallets.setCurrentText(wallets[0].name)
        dialog.radio_pubkey.setChecked(True)
        if dialog.exec_() == QDialog.Accepted:
            currency_tab = self.window().currencies_tabwidget.currentWidget()
            currency_tab.tab_history.table_history.model().sourceModel().refresh_transfers()
