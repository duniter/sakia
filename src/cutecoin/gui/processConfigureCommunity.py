'''
Created on 8 mars 2014

@author: inso
'''
import ucoin
from cutecoin.gen_resources.communityConfigurationDialog_uic import Ui_CommunityConfigurationDialog
from PyQt5.QtWidgets import QDialog, QMenu, QMessageBox
from cutecoin.models.node.treeModel import NodesTreeModel
from cutecoin.models.wallet.trustsTreeModel import TrustsTreeModel
from cutecoin.models.node import Node
from cutecoin.gui.walletTabWidget import WalletTabWidget


class Step():
    def __init__(self, config_dialog, previous_step=None, next_step=None):
        self.previous_step = previous_step
        self.next_step = next_step
        self.config_dialog = config_dialog


class StepPageInit(Step):
    '''
    First step when adding a community
    '''
    def __init__(self, config_dialog):
        super().__init__(config_dialog)

    def is_valid(self):
        server = self.config_dialog.lineedit_server.text()
        port = self.config_dialog.spinbox_port.value()
        try:
            ucoin.network.Peering(server, port)
        except:
            QMessageBox.critical(self, "Server error",
                              "Cannot get node peering")
            return False
        return True

    def process_next(self):
        '''
        We create the community
        '''
        server = self.config_dialog.lineedit_server.text()
        port = self.config_dialog.spinbox_port.value()
        default_node = Node.create(server, port, trust=True, hoster=True)
        account = self.config_dialog.account
        self.config_dialog.community = account.add_community(default_node)

    def display_page(self):
        self.config_dialog.button_previous.setEnabled(False)


class StepPageAddNodes(Step):
    '''
    The step where the user add nodes
    '''
    def __init__(self, config_dialog):
        super().__init__(config_dialog)

    #TODO: Check page validity
    def is_valid(self):
        return True

    def process_next(self):
        pass

    def display_page(self):
        # We add already known nodes to the displayed list
        for wallet in self.config_dialog.account.wallets:
            for node in wallet.nodes:
                if node not in self.config_dialog.nodes:
                    self.config_dialog.nodes.append(node)

        tree_model = NodesTreeModel(self.config_dialog.nodes,
                                    self.config_dialog.community.name())
        self.config_dialog.tree_nodes.setModel(tree_model)
        self.config_dialog.button_previous.setEnabled(False)
        self.config_dialog.button_next.setText("Next")


class StepPageSetWallets(Step):
    '''
    The step where the user set his wallets
    '''
    def __init__(self, config_dialog):
        super().__init__(config_dialog)

    #TODO: Check page validity
    def is_valid(self):
        return True

    def display_page(self):
        self.config_dialog.tabs_wallets.clear()
        for wallet in self.config_dialog.account.wallets:
            wallet_tab = WalletTabWidget(self.config_dialog.account,
                                         self.config_dialog.community)
            self.config_dialog.tabs_wallets.addTab(wallet_tab, wallet.name)
            tree_model = TrustsTreeModel(wallet,
                                         self.config_dialog.community.name())
            wallet_tab.trusts_tree_view.setModel(tree_model)

        self.config_dialog.button_previous.setEnabled(True)
        self.config_dialog.button_next.setText("Ok")

    def process_next(self):
        pass


class ProcessConfigureCommunity(QDialog, Ui_CommunityConfigurationDialog):
    '''
    Dialog to configure or add a community
    '''

    def __init__(self, account, community, default_node=None):
        '''
        Constructor
        '''
        super(ProcessConfigureCommunity, self).__init__()
        self.setupUi(self)
        self.community = community
        self.account = account
        self.step = None
        self.nodes = []

        step_init = StepPageInit(self)
        step_add_nodes = StepPageAddNodes(self)
        step_set_wallets = StepPageSetWallets(self)

        step_init.next_step = step_add_nodes
        step_add_nodes.next_step = step_set_wallets
        step_set_wallets.previous_step = step_add_nodes

        if self.community is not None:
            self.stacked_pages.removeWidget(self.page_init)
            self.step = step_add_nodes
            self.setWindowTitle("Configure community "
                                + self.community.currency)
        else:
            self.step = step_init
            self.setWindowTitle("Add a community")

        self.step.display_page()

    def next(self):
        if self.step.next_step is not None:
            if self.step.is_valid():
                self.step.process_next()
                self.step = self.step.next_step
                next_index = self.stacked_pages.currentIndex() + 1
                self.stacked_pages.setCurrentIndex(next_index)
                self.step.display_page()
        else:
            self.accept()

    def previous(self):
        if self.step.previous_step is not None:
            self.step = self.step.previous_step
            previous_index = self.stacked_pages.currentIndex() - 1
            self.stacked_pages.setCurrentIndex(previous_index)
            self.step.display_page()

    def add_node(self):
        '''
        Add node slot
        '''
        server = self.lineedit_server.text()
        port = self.spinbox_port.value()
        if self.community is not None:
            self.nodes.append(Node.create(server, port, trust=True))
            self.tree_nodes.setModel(NodesTreeModel(self.community,
                                                    self.nodes))

    def required_trusts_changed(self, value):
        wallet = self.account.wallets[self.tabs_wallets.currentIndex()]
        wallet.required_trusts = value

    def showContextMenu(self, point):
        if self.stacked_pages.currentIndex() == 1:
            menu = QMenu()
            action = menu.addAction("Delete", self.removeNode)
            if self.community is not None:
                if len(self.nodes) == 1:
                    action.setEnabled(False)
            menu.exec_(self.mapToGlobal(point))

    def accept(self):
        result = self.account.send_pubkey(self.community)
        if result:
            QMessageBox.critical(self, "Pubkey publishing error",
                              result)

        #TODO: Push wht only if changed
        for wallet in self.account.wallets:
            result = wallet.push_wht(self.account.gpg)
            if result:
                QMessageBox.critical(self, "Wallet publishing error",
                                  result)

        self.accepted.emit()
        self.close()
