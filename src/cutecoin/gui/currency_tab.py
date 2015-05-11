'''
Created on 2 févr. 2014

@author: inso
'''

import time
import logging
from PyQt5.QtWidgets import QWidget, QMessageBox
from PyQt5.QtCore import QModelIndex, pyqtSlot, QDateTime
from PyQt5.QtGui import QIcon
from ..gen_resources.currency_tab_uic import Ui_CurrencyTabWidget

from .community_tab import CommunityTabWidget
from .wallets_tab import WalletsTabWidget
from .transactions_tab import TransactionsTabWidget
from .network_tab import NetworkTabWidget
from .informations_tab import InformationsTabWidget
from . import toast
from ..tools.exceptions import MembershipNotFoundError
from ..core.person import Person


class CurrencyTabWidget(QWidget, Ui_CurrencyTabWidget):

    '''
    classdocs
    '''

    def __init__(self, app, community, password_asker, status_label):
        '''
        Constructor
        '''
        super().__init__()
        self.setupUi(self)
        self.app = app
        self.community = community
        self.password_asker = password_asker
        self.status_label = status_label
        self.tab_community = CommunityTabWidget(self.app,
                                                self.app.current_account,
                                                    self.community,
                                                    self.password_asker,
                                                    self)

        self.tab_wallets = WalletsTabWidget(self.app,
                                            self.app.current_account,
                                            self.community,
                                            self.password_asker)

        self.tab_network = NetworkTabWidget(self.community)

        self.community.network.new_block_mined.connect(self.refresh_block)
        self.community.network.nodes_changed.connect(self.refresh_status)
        bc_watcher = self.app.monitor.blockchain_watcher(self.community)
        bc_watcher.error.connect(self.display_error)
        bc_watcher.watching_stopped.connect(self.refresh_data)
        bc_watcher.new_transfers.connect(self.notify_transfers)

        person = Person.lookup(self.app.current_account.pubkey, self.community)
        try:
            join_block = person.membership(self.community)['blockNumber']
            join_date = self.community.get_block(join_block).mediantime
            parameters = self.community.parameters
            expiration_date = join_date + parameters['sigValidity']
            current_time = time.time()
            sig_validity = self.community.parameters['sigValidity']
            warning_expiration_time = int(sig_validity / 3)
            will_expire_soon = (current_time > expiration_date - warning_expiration_time)

            logging.debug("Try")
            if will_expire_soon:
                days = QDateTime().currentDateTime().daysTo(QDateTime.fromTime_t(expiration_date))
                if days > 0:
                    toast.display(self.tr("Membership expiration"
"<b>Warning : Membership expiration in {0} days</b>").format(days))
        except MembershipNotFoundError as e:
            pass

    def refresh(self):
        if self.app.current_account is None:
            self.tabs_account.setEnabled(False)
        else:
            self.tabs_account.setEnabled(True)

            self.tab_wallets = WalletsTabWidget(self.app,
                                                self.app.current_account,
                                                self.community,
                                                self.password_asker)
            self.tabs_account.addTab(self.tab_wallets,
                                     QIcon(':/icons/wallet_icon'),
                                    self.tr("Wallets"))

            self.tab_history = TransactionsTabWidget(self.app,
                                                     self.community,
                                                     self.password_asker,
                                                     self)
            self.tabs_account.addTab(self.tab_history,
                                     QIcon(':/icons/tx_icon'),
                                    self.tr("Transactions"))

            self.tab_community = CommunityTabWidget(self.app,
                                                    self.app.current_account,
                                                    self.community,
                                                    self.password_asker,
                                                    self)
            self.tabs_account.addTab(self.tab_community,
                                     QIcon(':/icons/community_icon'),
                                    self.tr("Community"))

            self.tab_informations = InformationsTabWidget(self.app.current_account,
                                                    self.community)
            self.tabs_account.addTab(self.tab_informations,
                                     QIcon(':/icons/informations_icon'),
                                    self.tr("Informations"))

            # fix bug refresh_nodes launch on destroyed NetworkTabWidget
            logging.debug('Disconnect community.network.nodes_changed')
            try:
                self.community.network.nodes_changed.disconnect()
            except TypeError:
                logging.debug('No signals on community.network.nodes_changed')

            self.tab_network = NetworkTabWidget(self.community)
            self.tabs_account.addTab(self.tab_network,
                                     QIcon(":/icons/network_icon"),
                                     self.tr("Network"))
            self.tab_informations.refresh()
            self.refresh_status()
            self.refresh_wallets()

    @pyqtSlot(str)
    def display_error(self, error):
        QMessageBox.critical(self, ":(",
                    error,
                    QMessageBox.Ok)

    @pyqtSlot(int)
    def refresh_block(self, block_number):
        '''
        When a new block is found, start handling data.
        @param: block_number: The number of the block mined
        '''
        logging.debug("Refresh block")
        self.tab_history.start_progress()
        self.app.monitor.blockchain_watcher(self.community).thread().start()
        self.app.monitor.persons_watcher(self.community).thread().start()
        self.refresh_status()

    @pyqtSlot()
    def refresh_data(self):
        '''
        Refresh data when the blockchain watcher finished handling datas
        '''
        if self.tab_wallets:
            self.tab_wallets.refresh()

        if self.tab_history.table_history.model():
            self.tab_history.table_history.model().sourceModel().refresh_transfers()

        self.tab_history.refresh_balance()
        self.tab_history.stop_progress()
        self.refresh_status()

    @pyqtSlot()
    def refresh_status(self):
        '''
        Refresh status bar
        '''
        logging.debug("Refresh status")
        text = self.tr(" Block {0}").format(self.community.network.latest_block)
        if self.community.network_quality() > 0.66:
            icon = '<img src=":/icons/connected" width="12" height="12"/>'
        elif self.community.network_quality() > 0.33:
            icon = '<img src=":/icons/weak_connect" width="12" height="12"/>'
        else:
            icon = '<img src=":/icons/disconnected" width="12" height="12"/>'
        self.status_label.setText("{0}{1}".format(icon, text))

    @pyqtSlot(list)
    def notify_transfers(self, transfers_list):
        transfers_txt = ""
        amount = 0
        currency = self.community.name
        for t in transfers_list:
            amount += t.metadata['amount']

        logging.debug(transfers_txt)
        text = self.tr("Received {0} {1} from {2} transfers").format(amount,
                                                           currency,
                                                           len(transfers_list))
        text += transfers_txt
        toast.display(self.tr("New transactions received"), text)

    def refresh_wallets(self):
        if self.app.current_account:
            self.tab_wallets.refresh()

    def showEvent(self, event):
        self.refresh_status()

    def referential_changed(self):
        if self.tab_history.table_history.model():
            self.tab_history.table_history.model().dataChanged.emit(
                                                     QModelIndex(),
                                                     QModelIndex(),
                                                     [])
            self.tab_history.refresh_balance()

        if self.tab_wallets:
            self.tab_wallets.refresh()

        if self.tab_informations:
            self.tab_informations.refresh()
