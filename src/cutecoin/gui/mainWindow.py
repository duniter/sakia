'''
Created on 1 févr. 2014

@author: inso
'''
from cutecoin.gen_resources.mainwindow_uic import Ui_MainWindow
from PyQt5.QtWidgets import QMainWindow, QAction, QErrorMessage
from PyQt5.QtCore import QSignalMapper
from cutecoin.gui.addAccountDialog import AddAccountDialog
from cutecoin.gui.communityTabWidget import CommunityTabWidget
from cutecoin.models.account.wallets.listModel import WalletsListModel
from cutecoin.models.wallet.listModel import WalletListModel
from cutecoin.models.transaction.sentListModel import SentListModel
from cutecoin.models.transaction.receivedListModel import ReceivedListModel
from cutecoin.core.exceptions import KeyAlreadyUsed

import logging

class MainWindow(QMainWindow, Ui_MainWindow):
    '''
    classdocs
    '''


    def __init__(self, core):
        '''
        Constructor
        '''
        # Set up the user interface from Designer.
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.core = core
        self.refreshMainWindow()

    def openAddAccountDialog(self):
        self.addAccountDialog = AddAccountDialog(self)
        self.addAccountDialog.setData()
        self.addAccountDialog.exec_()

    def actionAddAccount(self):
        self.addAccountDialog.account.name = self.addAccountDialog.accountName.text()
        try:
            self.core.addAccount(self.addAccountDialog.account)
        except KeyAlreadyUsed as e:
            QErrorMessage(self).showMessage(e.message)

        self.refreshMainWindow()

    def save(self):
        self.core.save()

    def actionChangeAccount(self, accountName):
        self.core.currentAccount = self.core.getAccount(accountName)
        logging.info('Changing account to ' + self.core.currentAccount.name)
        self.refreshMainWindow()


    '''
    Refresh main window
    When the selected account changes, all the widgets
    in the window have to be refreshed
    '''
    def refreshMainWindow(self):
        self.menuChange_account.clear()
        signalMapper = QSignalMapper(self)

        for account in self.core.accounts:
            action = QAction(account.name, self)
            self.menuChange_account.addAction(action)
            signalMapper.setMapping(action, account.name)
            action.triggered.connect(signalMapper.map)
            signalMapper.mapped[str].connect(self.actionChangeAccount)

        if self.core.currentAccount == None:
            self.accountTabs.setEnabled(False)
        else:
            self.accountTabs.setEnabled(True)
            self.accountNameLabel.setText("Current account : " + self.core.currentAccount.name)
            self.walletsList.setModel(WalletsListModel(self.core.currentAccount))
            self.walletContent.setModel(WalletListModel(self.core.currentAccount.wallets.walletsList[0]))
            for community in self.core.currentAccount.communities.communitiesList:
                communityTab = CommunityTabWidget(self.core.currentAccount, community)
                self.communitiesTab.addTab(communityTab, community.name())
            self.transactionsSent.setModel(SentListModel(self.core.currentAccount))
            self.transactionsReceived.setModel(ReceivedListModel(self.core.currentAccount))

