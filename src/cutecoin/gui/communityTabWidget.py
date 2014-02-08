'''
Created on 2 févr. 2014

@author: inso
'''
from PyQt5.QtWidgets import QWidget
from cutecoin.gen_resources.communityTabWidget_uic import Ui_CommunityTabWidget

class CommunityTabWidget(QWidget, Ui_CommunityTabWidget):
    '''
    classdocs
    '''
    def __init__(self, community):
        '''
        Constructor
        '''
        super(CommunityTabWidget, self).__init__()
        self.setupUi(self)
        self.community = community


