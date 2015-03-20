'''
Created on 27 févr. 2015

@author: inso
'''

from .watcher import Watcher


class NetworkWatcher(Watcher):
    '''
    This will crawl the network to always
    have up to date informations about the nodes
    '''

    def __init__(self, community):
        super().__init__()
        self.community = community

    def watch(self):
        self.community.network.stopped_perpetual_crawling.connect(self.watching_stopped)
        self.community.network.start_perpetual_crawling()

    def stop(self):
        self.community.network.stop_crawling()

