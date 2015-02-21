'''
Created on 20 févr. 2015

@author: inso
'''

from PyQt5.QtWidgets import QWidget
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
        proxy = NetworkFilterProxyModel()
        proxy.setSourceModel(model)
        self.table_network.setModel(proxy)


