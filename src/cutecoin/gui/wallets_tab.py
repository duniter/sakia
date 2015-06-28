"""
Created on 15 févr. 2015

@author: inso
"""

import logging
from PyQt5.QtWidgets import QWidget, QMenu, QAction, QApplication, QDialog
from PyQt5.QtCore import QDateTime, QModelIndex, Qt, QLocale
from PyQt5.QtGui import QCursor
from ..core.registry import Identity
from ..core.wallet import Wallet
from ..gui.password_asker import PasswordAskerDialog
from ..models.wallets import WalletsTableModel, WalletsFilterProxyModel
from .transfer import TransferMoneyDialog
from ..tools.exceptions import MembershipNotFoundError
from ..gen_resources.wallets_tab_uic import Ui_WalletsTab


class WalletsTabWidget(QWidget, Ui_WalletsTab):
    """
    classdocs
    """

    def __init__(self, app, account, community, password_asker):
        """
        Init
        :param cutecoin.core.app.Application app: Application instance
        :param cutecoin.core.account.Account account: Account instance
        :param cutecoin.core.community.Community community: Community instance
        :param cutecoin.gui.password_asker.PasswordAskerDialog password_asker: PasswordAskerDialog instance
        """
        super().__init__()
        self.setupUi(self)
        self.app = app
        self.account = account
        self.community = community
        self.password_asker = password_asker
        self.setup_connections()

    def setup_connections(self):
        self.account.inner_data_changed.connect(self.refresh_informations_frame)
        self.community.inner_data_changed.connect(self.refresh_informations_frame)

    def refresh(self):
        self.refresh_informations_frame()
        self.refresh_wallets()

    def refresh_wallets(self):
        wallets_model = WalletsTableModel(self.account, self.community)
        proxy_model = WalletsFilterProxyModel()
        proxy_model.setSourceModel(wallets_model)
        wallets_model.dataChanged.connect(self.wallet_changed)
        self.table_wallets.setModel(proxy_model)
        self.table_wallets.resizeColumnsToContents()

    def refresh_informations_frame(self):
        parameters = self.community.parameters
        try:
            identity = self.account.identity(self.community)
            membership = identity.membership(self.community)
            renew_block = membership['blockNumber']
            last_renewal = self.community.get_block(renew_block)['medianTime']
            expiration = last_renewal + parameters['sigValidity']
        except MembershipNotFoundError:
            last_renewal = None
            expiration = None

        certified = identity.unique_valid_certified_by(self.community)
        certifiers = identity.unique_valid_certifiers_of(self.community)
        if last_renewal and expiration:
            date_renewal = QLocale.toString(
                QLocale(),
                QDateTime.fromTime_t(last_renewal).date(), QLocale.dateFormat(QLocale(), QLocale.LongFormat)
            )
            date_expiration = QLocale.toString(
                QLocale(),
                QDateTime.fromTime_t(expiration).date(), QLocale.dateFormat(QLocale(), QLocale.LongFormat)
            )
            # set infos in label
            self.label_general.setText(
                self.tr("""
                <table cellpadding="5">
                <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
                <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
                <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
                </table>
                """).format(
                    self.account.name, self.account.pubkey,
                    self.tr("Membership"),
                    self.tr("Last renewal on {:}, expiration on {:}").format(date_renewal, date_expiration),
                    self.tr("Your web of trust"),
                    self.tr("Certified by {:} members; Certifier of {:} members").format(len(certifiers),
                                                                                             len(certified))
                )
            )
        else:
            # set infos in label
            self.label_general.setText(
                self.tr("""
                <table cellpadding="5">
                <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
                <tr><td align="right"><b>{:}</b></td></tr>
                <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
                </table>
                """).format(
                    self.account.name, self.account.pubkey,
                    self.tr("Not a member"),
                    self.tr("Your web of trust"),
                    self.tr("Certified by {:} members; Certifier of {:} members").format(len(certifiers),
                                                                                             len(certified))
                )
            )

        amount = self.account.amount(self.community)
        maximum = self.community.monetary_mass
        # if referential type is quantitative...
        if self.account.ref_type() == 'q':
            # display int values
            localized_amount = QLocale().toString(float(self.get_referential_value(amount)), 'f', 0)
            localized_minimum = QLocale().toString(float(self.get_referential_value(0)), 'f', 0)
            localized_maximum = QLocale().toString(float(self.get_referential_value(maximum)), 'f', 0)
        else:
            # display float values
            localized_amount = QLocale().toString(float(self.get_referential_value(amount)), 'f', 6)
            localized_minimum = QLocale().toString(float(self.get_referential_value(0)), 'f', 6)
            localized_maximum = QLocale().toString(float(self.get_referential_value(maximum)), 'f', 6)

        # set infos in label
        self.label_balance.setText(
            self.tr("""
            <table cellpadding="5">
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            </table>
            """).format(
                self.tr("Your money share "),
                self.tr("{:.2f}%").format(amount / maximum * 100) if maximum != 0 else "0%",
                self.tr("Your part "),
                self.tr("{:} {:} in [{:} ; {:}] {:}")
                .format(
                    localized_amount,
                    self.get_referential_name(),
                    localized_minimum,
                    localized_maximum,
                    self.get_referential_name()
                )
            )
        )

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

            new_wallet = QAction(self.tr("New Wallet"), self)
            new_wallet.triggered.connect(self.new_wallet)

            rename = QAction(self.tr("Rename"), self)
            rename.triggered.connect(self.rename_wallet)
            rename.setData(name_index)

            copy_pubkey = QAction(self.tr("Copy pubkey to clipboard"), self)
            copy_pubkey.triggered.connect(self.copy_pubkey_to_clipboard)
            copy_pubkey.setData(pubkey)

            transfer_to = QMenu()
            transfer_to.setTitle(self.tr("Transfer to..."))
            for w in self.account.wallets:
                if w == self.account.wallets[source_index.row()]:
                    continue
                transfer_action = QAction(w.name, self)
                transfer_action.triggered.connect(self.transfer_to_wallet)
                wallets = (self.account.wallets[source_index.row()], w)
                transfer_action.setData(wallets)
                transfer_to.addAction(transfer_action)

            menu.addAction(new_wallet)
            menu.addAction(rename)
            menu.addAction(copy_pubkey)
            menu.addMenu(transfer_to)
            # Show the context menu.
            menu.exec_(QCursor.pos())

    def new_wallet(self):
        """
        Create a new wallet
        """
        password_asker = PasswordAskerDialog(self.app.current_account)
        password = password_asker.exec_()
        if password_asker.result() == QDialog.Rejected:
            return None
        # create new wallet by increasing wallet pool size
        self.account.set_walletpool_size(len(self.account.wallets) + 1, password)
        # capture new wallet
        wallet = self.account.wallets[len(self.account.wallets)-1]
        # feed cache data of the wallet
        wallet.refresh_cache(self.community, list())
        # save wallet cache on disk
        self.app.save_wallet(self.account, self.account.wallets[len(self.account.wallets)-1])
        # save account cache on disk (update number of wallets)
        self.app.save(self.account)
        # refresh wallet list in gui
        self.refresh()

    def rename_wallet(self):
        index = self.sender().data()
        self.table_wallets.edit(index)

    def wallet_changed(self):
        self.table_wallets.resizeColumnsToContents()
        self.app.save(self.app.current_account)

    def copy_pubkey_to_clipboard(self):
        data = self.sender().data()
        clipboard = QApplication.clipboard()
        if data.__class__ is Wallet:
            clipboard.setText(data.pubkey)
        elif data.__class__ is Identity:
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
