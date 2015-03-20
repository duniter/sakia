'''
Created on 27 févr. 2015

@author: inso
'''

import logging
import time
from requests.exceptions import RequestException
from ...tools.exceptions import NoPeerAvailable
from .watcher import Watcher


class BlockchainWatcher(Watcher):
    def __init__(self, account, community):
        super().__init__()
        self.account = account
        self.community = community
        self.time_to_wait = int(self.community.parameters['avgGenTime'] / 10)
        self.exiting = False
        blockid = self.community.current_blockid()
        self.last_block = blockid['number']

    def watch(self):
        while not self.exiting:
            time.sleep(self.time_to_wait)
            try:
                blockid = self.community.current_blockid()
                block_number = blockid['number']
                if self.last_block != block_number:
                    if not self.exiting:
                        self.community.refresh_cache()
                    for w in self.account.wallets:
                        if not self.exiting:
                            w.refresh_cache(self.community)

                    logging.debug("New block, {0} mined in {1}".format(block_number,
                                                                       self.community.currency))
                    self.community.new_block_mined.emit(block_number)
                    self.last_block = block_number
            except NoPeerAvailable:
                pass
            except RequestException as e:
                self.error.emit("Cannot check new block : {0}".format(str(e)))
        self.watching_stopped.emit()

    def stop(self):
        self.exiting = True
