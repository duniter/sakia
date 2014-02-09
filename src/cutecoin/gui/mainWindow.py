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
        self.dialog = AddAccountDialog(self)
        self.dialog.setData()
        self.dialog.exec_()

    def actionAddAccount(self):
        self.dialog.account.name = self.dialog.accountName.text()
        self.core.addAccount(self.dialog.account)
        self.refreshMainWindow()

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
                self.communitiesTab.addPage(CommunityTabWidget(community), community.name())
            #TODO: self.transactionsReceived.setModel()
            #TODO: self.transactionsSent.setModel()


