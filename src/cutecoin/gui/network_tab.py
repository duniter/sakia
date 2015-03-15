'''
Created on 20 févr. 2015

@author: inso
'''

import logging
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QThread
from ..core.watchers.network import NetworkWatcher
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

        self.network_watcher = NetworkWatcher(community)
        self.watcher_thread = QThread()
        self.network_watcher.moveToThread(self.watcher_thread)
        self.watcher_thread.started.connect(self.network_watcher.watch)
        self.watcher_thread.finished.connect(self.network_watcher.stop)
        self.watcher_thread.finished.connect(self.network_watcher.deleteLater)
        self.watcher_thread.finished.connect(self.watcher_thread.deleteLater)

        community.network.nodes_changed.connect(self.refresh_nodes)

    def refresh_nodes(self):
        self.table_network.model().sourceModel().modelReset.emit()
        self.table_network.sortByColumn(0, Qt.AscendingOrder)

    def closeEvent(self, event):
        super().closeEvent(event)
        self.watcher_thread.terminate()

    def showEvent(self, event):
        super().showEvent(event)
        self.watcher_thread.start()
