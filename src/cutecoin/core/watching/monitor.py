'''
Created on 18 mars 2015

@author: inso
'''

from PyQt5.QtCore import QThread, Qt
from .blockchain import BlockchainWatcher
from .persons import PersonsWatcher
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
        return self._networks[community.name]

    def persons_watcher(self, community):
        return self._persons_watchers[community.name]

    def connect_watcher_to_thread(self, watcher):
        thread = QThread()
        watcher.moveToThread(thread)
        thread.started.connect(watcher.watch)
        watcher.watching_stopped.connect(thread.exit, Qt.DirectConnection)

        self.threads_pool.append(thread)

    def prepare_watching(self):
        for c in self.account.communities:
            persons_watcher = PersonsWatcher(c)
            self.connect_watcher_to_thread(persons_watcher)
            self._persons_watchers[c.name] = persons_watcher

            bc_watcher = BlockchainWatcher(self.account, c)
            self.connect_watcher_to_thread(bc_watcher)
            self._blockchain_watchers[c.name] = bc_watcher

            self.connect_watcher_to_thread(c.network)
            self._network_watchers[c.name] = c.network

    def start_network_watchers(self):
        for watcher in self._network_watchers.values():
            watcher.thread().start()

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
