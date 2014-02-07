'''
Created on 7 févr. 2014

@author: inso
'''
import json
from cutecoin.core import config

class AppData(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''

    def load(self, core):
        json_data=open(config.data['home'])
        data = json.load(json_data)
        json_data.close()
        data['accounts']


    def save(self, core):
        #TODO: Sauvegarde de l'état de l'application
        pass