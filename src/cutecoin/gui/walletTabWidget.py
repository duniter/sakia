'''
Created on 2 févr. 2014

@author: inso
'''

import logging
from PyQt5.QtWidgets import QWidget
from cutecoin.gen_resources.walletTabWidget_uic import Ui_WalletTabWidget


class WalletTabWidget(QWidget, Ui_WalletTabWidget):

    '''
    classdocs
    '''

    def __init__(self, account, community):
        '''
        Constructor
        '''
        super(WalletTabWidget, self).__init__()
        self.setupUi(self)
        self.community = community
        self.account = account
