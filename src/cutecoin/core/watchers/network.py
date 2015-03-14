'''
Created on 27 févr. 2015

@author: inso
'''

from PyQt5.QtCore import QObject, pyqtSlot


class NetworkWatcher(QObject):
    '''
    This will crawl the network to always
    have up to date informations about the nodes
    '''

    def __init__(self, community):
        super().__init__()
        self.community = community

    @pyqtSlot()
    def watch(self):
        self.community.network.start_perpetual_crawling()

    @pyqtSlot()
    def stop(self):
        self.community.network.stop_crawling()
