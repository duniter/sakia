'''
Created on 18 mars 2015

@author: inso
'''

from PyQt5.QtCore import QThread, Qt
from .blockchain import BlockchainWatcher
from .persons import PersonsWatcher
from .network import NetworkWatcher
import logging


class Monitor(object):
    '''
    The monitor is managing watchers
    '''

    def __init__(self, account):
        '''
        Constructor
        '''
        self.account = account
        self.threads_pool = []
        self._blockchain_watchers = {}
        self._network_watchers = {}
        self._persons_watchers = {}

    def blockchain_watcher(self, community):
        return self._blockchain_watchers[community.name]

    def network_watcher(self, community):
        return self._network_watchers[community.name]

    def persons_watcher(self, community):
        return self._persons_watchers[community.name]

    def restart_persons_watching(self, community):
        watcher = self.persons_watcher(community)
        thread = watcher.thread()
        logging.debug("Persons watching thread is : {0}".format(thread.isFinished()))
        thread.start()

    def connect_watcher_to_thread(self, watcher):
        thread = QThread()
        watcher.moveToThread(thread)
        thread.started.connect(watcher.watch)
        success = watcher.watching_stopped.connect(thread.exit, Qt.DirectConnection)

        self.threads_pool.append(thread)

    def prepare_watching(self):
        for c in self.account.communities:
            persons_watcher = PersonsWatcher(c)
            self.connect_watcher_to_thread(persons_watcher)
            self._persons_watchers[c.name] = persons_watcher

            bc_watcher = BlockchainWatcher(self.account, c)
            self.connect_watcher_to_thread(bc_watcher)
            self._blockchain_watchers[c.name] = bc_watcher

            network_watcher = NetworkWatcher(c)
            self.connect_watcher_to_thread(network_watcher)
            self._network_watchers[c.name] = network_watcher

    def start_watching(self):
        for thread in self.threads_pool:
            thread.start()

    def stop_watching(self):
        for watcher in self._persons_watchers.values():
            watcher.stop()
            self.threads_pool.remove(watcher.thread())
            watcher.deleteLater()
            watcher.thread().deleteLater()

        for watcher in self._blockchain_watchers.values():
            watcher.stop()
            self.threads_pool.remove(watcher.thread())
            watcher.deleteLater()
            watcher.thread().deleteLater()

        for watcher in self._network_watchers.values():
            watcher.stop()
            self.threads_pool.remove(watcher.thread())
            watcher.deleteLater()
            watcher.thread().deleteLater()
