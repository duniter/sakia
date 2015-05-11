'''
Created on 27 févr. 2015

@author: inso
'''

import logging
import time
from requests.exceptions import RequestException
from ...tools.exceptions import NoPeerAvailable
from .watcher import Watcher
from PyQt5.QtCore import pyqtSignal


class BlockchainWatcher(Watcher):

    new_transfers = pyqtSignal(list)
    loading_progressed = pyqtSignal(int, int)

    def __init__(self, account, community):
        super().__init__()
        self.account = account
        self.community = community
        self.time_to_wait = int(self.community.parameters['avgGenTime'] / 10)
        self.exiting = False
        self.last_block = self.community.network.latest_block

    def watch(self):
        loaded_wallets = 0
        def progressing(value, maximum):
            account_value = maximum * loaded_wallets + value
            account_max = maximum * len(self.account.wallets)
            self.loading_progressed.emit(account_value, account_max)

        try:
            received_list = []
            block_number = self.community.network.latest_block
            if self.last_block != block_number:

                for w in self.account.wallets:
                    w.refresh_progressed.connect(progressing)

                if not self.exiting:
                    self.community.refresh_cache()
                for w in self.account.wallets:
                    if not self.exiting:
                        w.refresh_cache(self.community, received_list)
                        loaded_wallets = loaded_wallets + 1

                logging.debug("New block, {0} mined in {1}".format(block_number,
                                                                   self.community.currency))
                self.last_block = block_number
                if len(received_list) > 0:
                    self.new_transfers.emit(received_list)
        except NoPeerAvailable:
            pass
        except RequestException as e:
            self.error.emit("Cannot check new block : {0}".format(str(e)))
        finally:
            self.watching_stopped.emit()

    def stop(self):
        self.exiting = True
