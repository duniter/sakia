'''
Created on 20 févr. 2015

@author: inso
'''

import logging
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QThread, pyqtSlot
from ..models.network import NetworkTableModel, NetworkFilterProxyModel
from ..gen_resources.network_tab_uic import Ui_NetworkTabWidget


class NetworkTabWidget(QWidget, Ui_NetworkTabWidget):
    '''
    classdocs
    '''

    def __init__(self, community):
        '''
        Constructor
        '''
        super().__init__()
        self.setupUi(self)
        model = NetworkTableModel(community)
        proxy = NetworkFilterProxyModel(self)
        proxy.setSourceModel(model)
        self.table_network.setModel(proxy)
        self.table_network.sortByColumn(0, Qt.DescendingOrder)
        self.table_network.resizeColumnsToContents()
        community.network.nodes_changed.connect(self.refresh_nodes)

    @pyqtSlot()
    def refresh_nodes(self):
        logging.debug("Refresh nodes")
        self.table_network.model().sourceModel().modelReset.emit()
