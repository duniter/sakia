'''
Created on 1 févr. 2014

@author: inso
'''
from cutecoin.gen_resources.mainwindow_uic import Ui_MainWindow
from PyQt5.QtWidgets import QMainWindow
from cutecoin.gui.addAccountDialog import AddAccountDialog
from cutecoin.gui.communityTabWidget import CommunityTabWidget
from cutecoin.models.account.wallets.listModel import WalletsListModel
from cutecoin.models.wallet.listModel import WalletListModel
from cutecoin.models.transaction.sentListModel import SentListModel
from cutecoin.models.transaction.receivedListModel import ReceivedListModel

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

    def openAddAccountDialog(self):
        self.addAccountDialog = AddAccountDialog(self)
        self.addAccountDialog.setData()
        self.addAccountDialog.exec_()

    def actionAddAccount(self):
        self.addAccountDialog.account.name = self.addAccountDialog.accountName.text()
        self.core.addAccount(self.addAccountDialog.account)
        self.refreshMainWindow()

    def save(self):
        self.core.save()

    '''
    Refresh main window
    When the selected account changes, all the widgets
    in the window have to be refreshed
    '''
    def refreshMainWindow(self):
        if self.core.currentAccount == None:
            self.accountTabs.setEnabled(False)
        else:
            self.accountTabs.setEnabled(True)
            self.accountNameLabel = self.core.currentAccount.name
            self.walletsList.setModel(WalletsListModel(self.core.currentAccount))
            self.walletContent.setModel(WalletListModel(self.core.currentAccount.wallets.walletsList[0]))
            for community in self.core.currentAccount.communities.communitiesList:
                self.communitiesTab.addTab(CommunityTabWidget(community), community.name())
            self.transactionsSent.setModel(SentListModel(self.core.currentAccount))
            self.transactionsReceived.setModel(ReceivedListModel(self.core.currentAccount))


