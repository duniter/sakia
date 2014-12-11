'''
Created on 2 déc. 2014

@author: inso
'''
from . import Document


class SelfCertification(Document):
    '''
    A document discribing a self certification.
    '''
    def __init__(self, ts, identifier):
        super(ts)
        self.identifier = identifier

    def uid(self):
        return "UID:{0}".format(self.identifier)

    def content(self):
        return "{0}\n{1}".format(self.uid(), self.timestamp())


class Certification(Document):
    '''
    classdocs
    '''

    def __init__(self, selfcert, blockid):
        '''
        Constructor
        '''
        self.selfcert = selfcert
        self.blockid = blockid

    def timestamp(self):
        return "META:TS:{0}".format(self.blockid)

    def content(self):
        return "{0}\n{1}".format(self.selfcert.content(), self.timestamp())
