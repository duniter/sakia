'''
Created on 7 févr. 2014

@author: inso
'''
import json
from cutecoin.core import config
import os

class AppData(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''

    def load(self, core):
        if (os.path.exists(config.data['home'])):
            json_data=open(config.data['home'], 'w+')
            data = json.load(json_data)
            json_data.close()


    def save(self, core):
        #TODO: Sauvegarde de l'état de l'application
        pass