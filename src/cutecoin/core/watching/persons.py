'''
Created on 27 févr. 2015

@author: inso
'''

from PyQt5.QtCore import pyqtSignal
from ..person import Person
from .watcher import Watcher
import logging


class PersonsWatcher(Watcher):
    '''
    This will crawl the network to always
    have up to date informations about the nodes
    '''
    person_changed = pyqtSignal(str)

    def __init__(self, community):
        super().__init__()
        self.community = community
        self.exiting = False

    def watch(self):
        logging.debug("Watching persons")
        instances = Person._instances.copy()
        for p in instances.values():
            if not self.exiting:
                for func in [Person.membership,
                             Person.is_member,
                             Person.certifiers_of,
                             Person.certified_by,
                             Person.published_uid]:
                    if not self.exiting:
                        if p.reload(func, self.community):
                            logging.debug("Change detected on {0} about {1}".format(p.pubkey,
                                                                                func.__name__))
                        self.person_changed.emit(p.pubkey)
        logging.debug("Finished watching persons")
        self.watching_stopped.emit()

    def stop(self):
        self.exiting = True